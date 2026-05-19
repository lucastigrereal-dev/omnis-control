"""
OMNIS Redis Listener — Read-Only Observer (GAP-001)
Subscribes to 3 channels, validates V2 envelope, logs events.
ZERO automatic actions. Read-only.
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import redis

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "events.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("omnis.event_listener")
logger.setLevel(logging.DEBUG)

_fh = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
))
logger.addHandler(_fh)

_console = logging.StreamHandler(sys.stdout)
_console.setLevel(logging.INFO)
_console.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
))
logger.addHandler(_console)

# ---------------------------------------------------------------------------
# V2 Envelope Contract Validator (from REDIS_CHANNEL_CONTRACTS.md)
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = {"event_id", "event_type", "timestamp", "source", "severity", "status", "payload"}
VALID_SEVERITIES = {"debug", "info", "warn", "error", "critical"}
VALID_STATUSES = {"ok", "degraded", "failed", "pending"}

# Channels this listener subscribes to (read-only)
DEFAULT_CHANNELS = [
    "system:heartbeat",
    "risk:events",
    "omnis:events",
]


def validate_envelope(event: dict) -> list[str]:
    """
    Validate an event against the V2 standard envelope contract.
    Returns a list of error messages. Empty list = valid.
    """
    errors: list[str] = []

    if not isinstance(event, dict):
        return ["Event is not a dict"]

    missing = REQUIRED_FIELDS - set(event.keys())
    if missing:
        errors.append(f"Missing fields: {sorted(missing)}")

    sev = event.get("severity")
    if sev is not None and sev not in VALID_SEVERITIES:
        errors.append(f"Invalid severity: {sev!r} (valid: {sorted(VALID_SEVERITIES)})")

    st = event.get("status")
    if st is not None and st not in VALID_STATUSES:
        errors.append(f"Invalid status: {st!r} (valid: {sorted(VALID_STATUSES)})")

    src = event.get("source")
    if isinstance(src, dict):
        if "service" not in src:
            errors.append("Missing source.service")
        if "version" not in src:
            errors.append("Missing source.version")
    elif src is not None:
        errors.append(f"source must be a dict, got {type(src).__name__}")

    return errors


# ---------------------------------------------------------------------------
# Event Listener
# ---------------------------------------------------------------------------
class OmnisEventListener:
    """
    Read-only Redis subscriber that observes events on the event nervous system.
    Validates V2 envelope contract before logging. Takes ZERO automatic actions.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6382,
        channels: Optional[list[str]] = None,
        redis_client: Optional[redis.Redis] = None,
    ):
        self.host = host
        self.port = port
        self.channels = channels or DEFAULT_CHANNELS
        self._redis_client = redis_client
        self._pubsub = None
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    @property
    def redis(self) -> redis.Redis:
        """Lazy init the Redis client (allows injection for tests)."""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )
        return self._redis_client

    def connect(self) -> bool:
        """Establish connection to Redis. Returns True on success."""
        try:
            self.redis.ping()
            logger.info("Connected to Redis %s:%s", self.host, self.port)
            return True
        except redis.ConnectionError as exc:
            logger.error("Redis connection failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------
    def subscribe(self) -> None:
        """Subscribe to all configured channels (read-only)."""
        self._pubsub = self.redis.pubsub()
        self._pubsub.subscribe(*self.channels)
        logger.info("Subscribed to %d channels: %s", len(self.channels), self.channels)

    def unsubscribe(self) -> None:
        """Cleanly unsubscribe and release pubsub."""
        if self._pubsub is not None:
            try:
                self._pubsub.unsubscribe()
                self._pubsub.close()
            except Exception:
                pass
            self._pubsub = None

    # ------------------------------------------------------------------
    # Event loop
    # ------------------------------------------------------------------
    def _handle_message(self, msg: dict) -> None:
        """Process a single Redis pubsub message. ZERO side-effects beyond logging."""
        # Skip non-message types (subscribe, unsubscribe, etc.)
        if msg.get("type") != "message":
            return

        channel = msg.get("channel", "unknown")
        raw_data = msg.get("data", "")

        # Attempt JSON decode
        try:
            event = json.loads(raw_data)
        except json.JSONDecodeError:
            logger.warning(
                "[%s] Non-JSON message received (channel=%s, raw_len=%d)",
                msg.get("channel", "?"),
                channel,
                len(raw_data),
            )
            return

        # Validate V2 envelope
        errors = validate_envelope(event)
        if errors:
            logger.warning(
                "[%s] INVALID V2 envelope — event_id=%s — errors: %s",
                channel,
                event.get("event_id", "?"),
                "; ".join(errors),
            )
            return

        # Log valid event
        logger.info(
            "[%s] %s | sev=%s status=%s | src=%s/%s | event_id=%s",
            channel,
            event.get("event_type", "?"),
            event.get("severity", "?"),
            event.get("status", "?"),
            event.get("source", {}).get("service", "?"),
            event.get("source", {}).get("version", "?"),
            event.get("event_id", "?"),
        )
        # Debug: full payload (file only, not console)
        logger.debug(
            "[%s] FULL EVENT: %s",
            channel,
            json.dumps(event, ensure_ascii=False, default=str),
        )

    def listen(self, timeout: Optional[float] = None) -> int:
        """
        Blocking listen loop. Reads messages from subscribed channels.
        Returns the count of valid events received.

        If timeout is set, stops after that many seconds.
        Otherwise runs until stop() is called or signal received.
        """
        if self._pubsub is None:
            self.subscribe()

        self._running = True
        count = 0
        start = time.monotonic()

        logger.info("Listening on %s (read-only observer)...", self.channels)

        while self._running:
            try:
                msg = self._pubsub.get_message(timeout=1.0)
            except (redis.ConnectionError, OSError) as exc:
                logger.warning("Redis read error: %s — reconnecting...", exc)
                self._reconnect()
                continue

            if msg is None:
                # Check timeout
                if timeout is not None and (time.monotonic() - start) >= timeout:
                    logger.info("Listen timeout reached (%.1fs)", timeout)
                    break
                continue

            self._handle_message(msg)
            count += 1

        self._running = False
        logger.info("Listener stopped. Processed %d messages.", count)
        return count

    def stop(self) -> None:
        """Signal the listen loop to exit gracefully."""
        logger.info("Stop requested — shutting down listener...")
        self._running = False

    # ------------------------------------------------------------------
    # Reconnect logic
    # ------------------------------------------------------------------
    def _reconnect(self) -> None:
        """Reconnect with exponential backoff (1s → 2s → 4s → ... → 60s cap)."""
        delay = self._reconnect_delay
        while self._running:
            try:
                self.unsubscribe()
                self._redis_client = None  # force fresh connection
                if self.connect():
                    self.subscribe()
                    self._reconnect_delay = 1.0  # reset
                    logger.info("Reconnected successfully.")
                    return
            except Exception as exc:
                logger.warning("Reconnect attempt failed: %s", exc)

            logger.info("Retrying in %.1fs...", delay)
            time.sleep(delay)
            delay = min(delay * 2, self._max_reconnect_delay)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------
    def __enter__(self) -> "OmnisEventListener":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.unsubscribe()
        if self._redis_client is not None:
            try:
                self._redis_client.close()
            except Exception:
                pass
            self._redis_client = None


# ---------------------------------------------------------------------------
# Signal handler for clean shutdown
# ---------------------------------------------------------------------------
def _install_signal_handler(listener: OmnisEventListener) -> None:
    """Install SIGINT/SIGTERM handler for clean shutdown."""

    def _handler(signum: int, _frame: object) -> None:
        sig_name = signal.Signals(signum).name
        logger.info("Received %s — shutting down...", sig_name)
        listener.stop()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


# ---------------------------------------------------------------------------
# CLI entrypoint (for manual testing)
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the listener as a standalone process."""
    import argparse

    parser = argparse.ArgumentParser(description="OMNIS Redis Event Listener (Read-Only)")
    parser.add_argument("--host", default="localhost", help="Redis host")
    parser.add_argument("--port", type=int, default=6382, help="Redis port")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Stop after N seconds (0 = infinite)")
    parser.add_argument("--channels", nargs="*", default=DEFAULT_CHANNELS,
                        help="Channels to subscribe to")
    args = parser.parse_args()

    listener = OmnisEventListener(
        host=args.host,
        port=args.port,
        channels=args.channels,
    )

    if not listener.connect():
        logger.error("Cannot connect to Redis. Exiting.")
        sys.exit(1)

    _install_signal_handler(listener)

    timeout = args.timeout if args.timeout and args.timeout > 0 else None
    listener.listen(timeout=timeout)

    logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
