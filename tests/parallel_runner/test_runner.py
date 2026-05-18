"""Tests for Parallel Local Runner."""

import tempfile
from pathlib import Path

import pytest

from src.parallel_runner.models import RunnerTask, RunnerResult, RunBatch, RunStatus
from src.parallel_runner.runner import ParallelRunner, FileLock


@pytest.fixture
def runner():
    with tempfile.TemporaryDirectory() as tmp:
        yield ParallelRunner(max_workers=2, data_dir=Path(tmp))


class TestModels:
    def test_task_to_from_dict(self):
        task = RunnerTask(task_id="t1", name="test_task", args=[1, 2], kwargs={"x": 3}, timeout=10.0)
        d = task.to_dict()
        restored = RunnerTask.from_dict(d)
        assert restored.task_id == "t1"
        assert restored.name == "test_task"
        assert restored.args == [1, 2]
        assert restored.kwargs == {"x": 3}
        assert restored.timeout == 10.0

    def test_result_to_from_dict(self):
        result = RunnerResult(task_id="t1", name="test", success=True, result={"ok": True},
                              duration=0.5, status=RunStatus.SUCCESS)
        d = result.to_dict()
        restored = RunnerResult.from_dict(d)
        assert restored.task_id == "t1"
        assert restored.success
        assert restored.result == {"ok": True}
        assert restored.duration == 0.5
        assert restored.status == RunStatus.SUCCESS

    def test_batch_to_from_dict(self):
        tasks = [RunnerTask(task_id="t1", name="task1")]
        results = [RunnerResult(task_id="t1", name="task1", success=True, status=RunStatus.SUCCESS)]
        batch = RunBatch(batch_id="b1", tasks=tasks, results=results, status=RunStatus.SUCCESS)
        d = batch.to_dict()
        restored = RunBatch.from_dict(d)
        assert restored.batch_id == "b1"
        assert len(restored.tasks) == 1
        assert len(restored.results) == 1
        assert restored.succeeded == 1
        assert restored.failed == 0

    def test_batch_properties(self):
        results = [
            RunnerResult(task_id="t1", name="a", success=True, duration=1.0),
            RunnerResult(task_id="t2", name="b", success=False, duration=2.0, status=RunStatus.FAILED),
            RunnerResult(task_id="t3", name="c", success=True, duration=0.5),
        ]
        batch = RunBatch(batch_id="b1", tasks=[], results=results)
        assert batch.succeeded == 2
        assert batch.failed == 1
        assert batch.total_duration == 3.5


class TestFileLock:
    def test_acquire_release(self, runner):
        lock_path = runner.data_dir / "locks" / "test.lock"
        fl = FileLock(lock_path)
        assert fl.acquire()
        assert fl.locked
        fl.release()
        assert not fl.locked

    def test_acquire_twice_fails(self, runner):
        lock_path = runner.data_dir / "locks" / "double.lock"
        fl1 = FileLock(lock_path, timeout=0.1)
        fl2 = FileLock(lock_path, timeout=0.1)
        assert fl1.acquire()
        assert not fl2.acquire()
        fl1.release()

    def test_reacquire_after_release(self, runner):
        lock_path = runner.data_dir / "locks" / "reacquire.lock"
        fl = FileLock(lock_path)
        assert fl.acquire()
        fl.release()
        assert fl.acquire()
        fl.release()

    def test_lock_context_manager(self, runner):
        with runner.lock("ctx-test"):
            assert True

    def test_lock_context_manager_blocks_reentry(self, runner):
        lock_path = runner.data_dir / "locks" / "ctx-test2.lock"
        with runner.lock("ctx-test2"):
            fl = FileLock(lock_path, timeout=0.05)
            assert not fl.acquire()


class TestParallelRunner:
    def test_run_sync(self, runner):
        tasks = [
            RunnerTask(task_id="t1", name="task1"),
            RunnerTask(task_id="t2", name="task2"),
            RunnerTask(task_id="t3", name="task3"),
        ]
        batch = runner.run_sync(tasks)
        assert batch.status == RunStatus.SUCCESS
        assert len(batch.results) == 3
        assert all(r.success for r in batch.results)
        assert batch.succeeded == 3

    def test_run_parallel(self, runner):
        tasks = [
            RunnerTask(task_id="p1", name="parallel_1"),
            RunnerTask(task_id="p2", name="parallel_2"),
            RunnerTask(task_id="p3", name="parallel_3"),
            RunnerTask(task_id="p4", name="parallel_4"),
        ]
        batch = runner.run_parallel(tasks)
        assert batch.status == RunStatus.SUCCESS
        assert len(batch.results) == 4
        assert all(r.success for r in batch.results)

    def test_run_dispatches_correctly(self, runner):
        tasks = [RunnerTask(task_id="x1", name="echo", args=[42], kwargs={"key": "val"})]
        batch = runner.run_sync(tasks)
        result = batch.results[0].result
        assert result["task_id"] == "x1"
        assert result["args"] == [42]
        assert result["kwargs"] == {"key": "val"}

    def test_run_auto_parallel_for_multiple_tasks(self, runner):
        tasks = [RunnerTask(task_id="a1", name="a"), RunnerTask(task_id="a2", name="b")]
        batch = runner.run(tasks, parallel=True)
        assert len(batch.results) == 2
        assert all(r.success for r in batch.results)

    def test_run_auto_sync_for_single_task(self, runner):
        tasks = [RunnerTask(task_id="solo", name="only")]
        batch = runner.run(tasks, parallel=True)
        assert len(batch.results) == 1
        assert batch.results[0].success

    def test_batch_persistence(self, runner):
        tasks = [RunnerTask(task_id="persist", name="persist_me")]
        batch = runner.run_sync(tasks)
        loaded = runner.load_batch(batch.batch_id)
        assert loaded is not None
        assert loaded.batch_id == batch.batch_id
        assert len(loaded.results) == 1

    def test_list_batches(self, runner):
        runner.run_sync([RunnerTask(task_id="1", name="first")])
        runner.run_sync([RunnerTask(task_id="2", name="second")])
        batches = runner.list_batches()
        assert len(batches) == 2

    def test_load_nonexistent_batch(self, runner):
        assert runner.load_batch("no-such-batch") is None

    def test_consolidate(self, runner):
        b1 = runner.run_sync([RunnerTask(task_id="c1", name="c1"), RunnerTask(task_id="c2", name="c2")])
        b2 = runner.run_sync([RunnerTask(task_id="c3", name="c3")])
        summary = runner.consolidate([b1, b2])
        assert summary["batches"] == 2
        assert summary["total_tasks"] == 3
        assert summary["succeeded"] == 3
        assert summary["failed"] == 0
        assert summary["success_rate"] == 1.0

    def test_result_has_duration(self, runner):
        tasks = [RunnerTask(task_id="dur", name="duration_test")]
        batch = runner.run_sync(tasks)
        assert batch.results[0].duration >= 0
        assert batch.results[0].started_at
        assert batch.results[0].finished_at
