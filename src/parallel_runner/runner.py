"""Parallel Runner — concurrent task execution with file locks."""

from __future__ import annotations

import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from .models import RunnerTask, RunnerResult, RunBatch, RunStatus


class FileLock:
    """Simple file-based mutual exclusion lock."""

    def __init__(self, lock_path: Path, timeout: float = 10.0, poll_interval: float = 0.05):
        self.lock_path = lock_path
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._held = False

    def acquire(self) -> bool:
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                self.lock_path.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                self._held = True
                return True
            except FileExistsError:
                time.sleep(self.poll_interval)
        return False

    def release(self) -> None:
        if self._held:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass
            self._held = False

    @property
    def locked(self) -> bool:
        return self.lock_path.exists()


class ParallelRunner:
    """Execute tasks in parallel with thread pool, locks, and consolidation."""

    def __init__(self, max_workers: int = 4, data_dir: Optional[Path] = None):
        self.max_workers = max_workers
        self.data_dir = Path(data_dir or Path(os.getcwd()) / "data" / "runs")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def lock(self, name: str, timeout: float = 10.0):
        """Context manager for file-based lock on a named resource."""
        lock_path = self.data_dir / "locks" / f"{name}.lock"
        fl = FileLock(lock_path, timeout=timeout)
        acquired = fl.acquire()
        if not acquired:
            raise TimeoutError(f"Could not acquire lock '{name}' within {timeout}s")
        try:
            yield
        finally:
            fl.release()

    def run_sync(self, tasks: list[RunnerTask], timeout: Optional[float] = None) -> RunBatch:
        """Execute tasks sequentially (deterministic order)."""
        batch = RunBatch(batch_id=str(uuid.uuid4())[:8], status=RunStatus.RUNNING, tasks=tasks)
        for task in tasks:
            result = self._execute_one(task, timeout or task.timeout)
            batch.results.append(result)
        batch.status = RunStatus.SUCCESS if all(r.success for r in batch.results) else RunStatus.FAILED
        batch.finished_at = self._now()
        self._save_batch(batch)
        return batch

    def run_parallel(self, tasks: list[RunnerTask], timeout: Optional[float] = None) -> RunBatch:
        """Execute tasks in parallel with ThreadPoolExecutor."""
        batch = RunBatch(batch_id=str(uuid.uuid4())[:8], status=RunStatus.RUNNING, tasks=tasks)
        results_map: dict[str, RunnerResult] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._execute_one, task, timeout or task.timeout): task
                for task in tasks
            }
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=(timeout or 60) + 10)
                except Exception as e:
                    task = futures[future]
                    result = RunnerResult(
                        task_id=task.task_id, name=task.name,
                        success=False, error=str(e), status=RunStatus.FAILED,
                    )
                results_map[result.task_id] = result

        # Preserve original task order in results
        for task in tasks:
            batch.results.append(results_map.get(task.task_id, RunnerResult(
                task_id=task.task_id, name=task.name,
                success=False, error="Missing result", status=RunStatus.FAILED,
            )))

        batch.status = RunStatus.SUCCESS if all(r.success for r in batch.results) else RunStatus.FAILED
        batch.finished_at = self._now()
        self._save_batch(batch)
        return batch

    def run(self, tasks: list[RunnerTask], parallel: bool = True, timeout: Optional[float] = None) -> RunBatch:
        """Run tasks (parallel or sync) and consolidate results."""
        if parallel and len(tasks) > 1:
            return self.run_parallel(tasks, timeout)
        return self.run_sync(tasks, timeout)

    def consolidate(self, batches: list[RunBatch]) -> dict:
        """Consolidate multiple batches into summary."""
        total_tasks = sum(len(b.tasks) for b in batches)
        total_succeeded = sum(b.succeeded for b in batches)
        total_failed = sum(b.failed for b in batches)
        total_duration = sum(b.total_duration for b in batches)

        return {
            "batches": len(batches),
            "total_tasks": total_tasks,
            "succeeded": total_succeeded,
            "failed": total_failed,
            "success_rate": total_succeeded / max(1, total_tasks),
            "total_duration": total_duration,
            "avg_duration": total_duration / max(1, total_tasks),
            "batch_ids": [b.batch_id for b in batches],
        }

    def _execute_one(self, task: RunnerTask, timeout: float) -> RunnerResult:
        started_at = self._now()
        try:
            result = RunnerResult(
                task_id=task.task_id, name=task.name,
                success=True, status=RunStatus.RUNNING,
                started_at=started_at,
            )
            # Simulated execution — real runner would dispatch to registered functions
            output = self._dispatch(task)
            result.result = output
            result.success = True
            result.status = RunStatus.SUCCESS
        except Exception as e:
            result.success = False
            result.error = str(e)
            result.status = RunStatus.FAILED
        finally:
            result.finished_at = self._now()
            result.duration = self._parse_duration(result.started_at, result.finished_at)

        return result

    def _dispatch(self, task: RunnerTask) -> Any:
        """Dispatch a task. Override or register callables for real execution."""
        # Default: return a structured echo for testing
        return {"task_id": task.task_id, "name": task.name, "args": task.args, "kwargs": task.kwargs}

    def _save_batch(self, batch: RunBatch) -> None:
        path = self.data_dir / f"{batch.batch_id}.json"
        path.write_text(json.dumps(batch.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def load_batch(self, batch_id: str) -> Optional[RunBatch]:
        path = self.data_dir / f"{batch_id}.json"
        if path.exists():
            return RunBatch.from_dict(json.loads(path.read_text(encoding="utf-8")))
        return None

    def list_batches(self) -> list[str]:
        return [p.stem for p in sorted(self.data_dir.glob("*.json"))]

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    @staticmethod
    def _parse_duration(start: str, end: str) -> float:
        if not start or not end:
            return 0.0
        try:
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            s = datetime.strptime(start, fmt)
            e = datetime.strptime(end, fmt)
            return (e - s).total_seconds()
        except ValueError:
            return 0.0
