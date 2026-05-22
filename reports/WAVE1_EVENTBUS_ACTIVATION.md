# WAVE 1 — Redis + EventBus Activation

**Date:** 2026-05-22
**Status:** COMPLETE
**Risk Level:** L1 (read + temporary test streams)

## Results

| Block | Test | Result |
|-------|------|--------|
| 1-2 | Redis :6381 connectivity | PASS — aurora_redis v7.4.7 |
| 3-4 | Publish/Consume via Redis Streams | PASS — XADD + XREAD |
| 5 | Envelope v2 contract | PASS — 8 fields + trace_id + roundtrip |
| 6 | Retry/Reconnect | PASS — 5/5 rapid-fire |
| 7 | trace_id E2E propagation | PASS — 3 events, 1 trace |
| 8 | Replay buffer hooks | PASS — size=5, replay=5 |
| 9 | Channel topology (10 channels) | PASS — all writable |
| 10 | Report | THIS FILE |

## Infrastructure

- aurora_redis :6381 (canonical bus) — UP, healthy, keyspace empty
- crm-tigre-redis :6380 — UP (separate, publisher-os)
- omnis_bus tests: 121/121 PASS
- Envelope: v2 with trace_id, source_badge auto-inference
- Script: scripts/wave1_eventbus_test.py

## Next
Wave 2 — Health Bridge Real
