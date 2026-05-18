"""Mission Replay engine — snapshot, replay, and diff missions."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import ReplaySession, DiffReport, DiffEntry

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPLAY_DIR = PROJECT_ROOT / "missions" / ".replays"


class MissionReplay:
    """Load, replay, and compare missions."""

    def __init__(self, missions_dir: Optional[Path] = None):
        self.missions_dir = Path(missions_dir) if missions_dir else PROJECT_ROOT / "missions"
        self.replays_dir = self.missions_dir / ".replays"
        self._sessions: dict[str, ReplaySession] = {}

    # -----------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------

    def list_missions(self) -> list[str]:
        """List available mission IDs."""
        ids = []
        for d in sorted(self.missions_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                contract = d / "mission_contract.json"
                if contract.is_file():
                    ids.append(d.name)
        return ids

    def mission_exists(self, mission_id: str) -> bool:
        return (self.missions_dir / mission_id).is_dir()

    # -----------------------------------------------------------
    # Snapshot
    # -----------------------------------------------------------

    def snapshot(self, mission_id: str) -> dict:
        """Take a metadata snapshot of a mission without copying files."""
        mdir = self.missions_dir / mission_id
        if not mdir.is_dir():
            raise FileNotFoundError(f"Mission not found: {mission_id}")

        contract = self._read_json(mdir / "mission_contract.json") or {}
        files = []
        for f in sorted(mdir.rglob("*")):
            if f.is_file() and ".replays" not in str(f.relative_to(mdir)):
                rel = str(f.relative_to(mdir))
                files.append({
                    "path": rel,
                    "size": f.stat().st_size,
                    "hash": self._hash_file(f),
                })

        return {
            "mission_id": mission_id,
            "contract": contract,
            "files": files,
            "snapshot_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

    # -----------------------------------------------------------
    # Replay
    # -----------------------------------------------------------

    def create_replay(
        self,
        mission_id: str,
        variant_name: str,
        variant_changes: Optional[dict] = None,
        dry_run: bool = True,
    ) -> ReplaySession:
        """Create a replay session for a mission with variant parameters.

        Args:
            mission_id: Original mission to replay
            variant_name: Short name for the variant (e.g. "Brotas", "v2")
            variant_changes: Dict of parameter overrides
            dry_run: If True, only create session metadata, don't copy files
        """
        if not self.mission_exists(mission_id):
            raise FileNotFoundError(f"Mission not found: {mission_id}")

        session_id = f"REPLAY-{mission_id}-{variant_name}"
        original_path = str(self.missions_dir / mission_id)

        session = ReplaySession(
            session_id=session_id,
            original_mission_id=mission_id,
            variant_name=variant_name,
            variant_changes=variant_changes or {},
            original_path=original_path,
        )

        if not dry_run:
            replay_path = self.replays_dir / session_id
            if replay_path.exists():
                shutil.rmtree(replay_path)
            replay_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(original_path, replay_path)
            session.replay_path = str(replay_path)

            # Apply variant changes to the replay contract
            self._apply_changes(replay_path, variant_changes or {})

            # Count output files
            outputs = replay_path / "05_outputs"
            session.output_count = len(list(outputs.rglob("*"))) if outputs.is_dir() else 0

            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        self._sessions[session_id] = session
        if not dry_run:
            self._save_session(session)
        return session

    def _apply_changes(self, replay_path: Path, changes: dict) -> None:
        """Apply variant parameter changes to the replayed mission."""
        contract_path = replay_path / "mission_contract.json"
        if not contract_path.is_file():
            return
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract.update(changes)

        # Add replay metadata
        contract["_replay"] = {
            "variant": changes.get("variant", "unknown"),
            "applied_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "changes": changes,
        }

        contract_path.write_text(
            json.dumps(contract, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # -----------------------------------------------------------
    # Diff / Compare
    # -----------------------------------------------------------

    def diff(self, session_id: str) -> DiffReport:
        """Generate a diff report between original and replay."""
        session = self._load_session(session_id)
        if not session:
            # Try loading from file
            session_file = self.replays_dir / session_id / "session.json"
            if session_file.is_file():
                session = ReplaySession.from_dict(
                    json.loads(session_file.read_text(encoding="utf-8"))
                )
            else:
                raise FileNotFoundError(f"Replay session not found: {session_id}")

        original_path = Path(session.original_path) if session.original_path else self.missions_dir / session.original_mission_id

        if not session.replay_path:
            return self._diff_from_snapshots(session)

        replay_path = Path(session.replay_path)

        if not replay_path.is_dir():
            # Dry-run mode: compare snapshot metadata
            return self._diff_from_snapshots(session)

        report = DiffReport(
            session_id=session_id,
            original_mission_id=session.original_mission_id,
            variant_name=session.variant_name,
        )

        # Map files by relative path
        original_files = self._file_map(original_path, skip_replays=True)
        replay_files = self._file_map(replay_path, skip_replays=False)

        all_paths = set(original_files.keys()) | set(replay_files.keys())

        for rel_path in sorted(all_paths):
            orig = original_files.get(rel_path)
            repl = replay_files.get(rel_path)

            if orig and repl:
                if orig["hash"] == repl["hash"]:
                    entry = DiffEntry(
                        file_path=rel_path,
                        change_type="unchanged",
                        original_size=orig["size"],
                        replay_size=repl["size"],
                        original_hash=orig["hash"],
                        replay_hash=repl["hash"],
                    )
                    report.files_unchanged += 1
                else:
                    entry = DiffEntry(
                        file_path=rel_path,
                        change_type="modified",
                        original_size=orig["size"],
                        replay_size=repl["size"],
                        original_hash=orig["hash"],
                        replay_hash=repl["hash"],
                        summary=f"Size: {orig['size']} → {repl['size']} bytes",
                    )
                    report.files_modified += 1
            elif orig and not repl:
                entry = DiffEntry(
                    file_path=rel_path,
                    change_type="removed",
                    original_size=orig["size"],
                )
                report.files_removed += 1
            else:
                entry = DiffEntry(
                    file_path=rel_path,
                    change_type="added",
                    replay_size=repl["size"],
                )
                report.files_added += 1

            report.entries.append(entry)
            report.total_files += 1

        return report

    def _diff_from_snapshots(self, session: ReplaySession) -> DiffReport:
        """Generate a placeholder diff report when replay hasn't been materialized."""
        original_snap = self.snapshot(session.original_mission_id)
        report = DiffReport(
            session_id=session.session_id,
            original_mission_id=session.original_mission_id,
            variant_name=session.variant_name,
            total_files=len(original_snap["files"]),
            files_unchanged=len(original_snap["files"]),
        )
        for f in original_snap["files"]:
            report.entries.append(DiffEntry(
                file_path=f["path"],
                change_type="unchanged",
                original_size=f["size"],
                original_hash=f["hash"],
                summary="dry-run: no replay files to compare",
            ))
        return report

    # -----------------------------------------------------------
    # Session persistence
    # -----------------------------------------------------------

    def _save_session(self, session: ReplaySession) -> None:
        session_dir = self.replays_dir / session.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "session.json").write_text(
            json.dumps(session.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_session(self, session_id: str) -> Optional[ReplaySession]:
        if session_id in self._sessions:
            return self._sessions[session_id]
        session_file = self.replays_dir / session_id / "session.json"
        if session_file.is_file():
            session = ReplaySession.from_dict(
                json.loads(session_file.read_text(encoding="utf-8"))
            )
            self._sessions[session_id] = session
            return session
        return None

    def list_sessions(self) -> list[ReplaySession]:
        """List all replay sessions."""
        sessions = []
        if self.replays_dir.is_dir():
            for d in self.replays_dir.iterdir():
                if d.is_dir():
                    session = self._load_session(d.name)
                    if session:
                        sessions.append(session)
        return sessions

    # -----------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------

    def _read_json(self, path: Path) -> Optional[dict]:
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _hash_file(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    def _file_map(self, directory: Path, skip_replays: bool = True) -> dict[str, dict]:
        """Map relative paths to file metadata."""
        result = {}
        for f in directory.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(directory))
                if skip_replays and ".replays" in rel:
                    continue
                result[rel] = {
                    "size": f.stat().st_size,
                    "hash": self._hash_file(f),
                }
        return result
