from src.observability.run_log import RunLogger


class TestRunLogger:
    def test_start_run(self):
        logger = RunLogger()
        run = logger.start_run("P37")
        assert run.phase == "P37"
        assert run.status == "STARTED"
        assert run.started_at != ""

    def test_update_status(self):
        logger = RunLogger()
        run = logger.start_run("P38")
        updated = logger.update(run.run_id, "IN_PROGRESS", "Building skill router")
        assert updated.status == "IN_PROGRESS"
        assert updated.detail == "Building skill router"

    def test_completed_sets_finished_at(self):
        logger = RunLogger()
        run = logger.start_run("P39")
        updated = logger.update(run.run_id, "COMPLETED")
        assert updated.finished_at != ""

    def test_active_runs(self):
        logger = RunLogger()
        logger.start_run("P40")
        run2 = logger.start_run("P41")
        logger.update(run2.run_id, "COMPLETED")
        active = logger.active_runs
        assert len(active) == 1
        assert active[0].phase == "P40"

    def test_update_creates_if_missing(self):
        logger = RunLogger()
        run = logger.update("unknown_id", "RECOVERED", "recreated")
        assert run.run_id == "unknown_id"
        assert run.status == "RECOVERED"

    def test_to_dict(self):
        logger = RunLogger()
        logger.start_run("P42")
        data = logger.to_dict()
        assert len(data["runs"]) == 1
        assert data["runs"][0]["phase"] == "P42"
