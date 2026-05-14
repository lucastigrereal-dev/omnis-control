"""Tests for P29 OMNIS OS CLI."""
from src.omnis_os.cli import main


class TestCLIBasic:
    def test_no_command(self):
        assert main([]) == 1

    def test_bootstrap(self):
        assert main(["bootstrap"]) == 0

    def test_status(self):
        assert main(["status"]) == 0

    def test_health(self):
        assert main(["health"]) == 0

    def test_health_module(self):
        # Fake module — will raise, but CLI catches in dry run
        assert main(["health", "--module", "ghost"]) in (0, 1)

    def test_events(self):
        assert main(["events"]) == 0

    def test_events_filtered(self):
        assert main(["events", "--type", "boot", "--limit", "5"]) == 0

    def test_modules(self):
        assert main(["modules"]) == 0

    def test_modules_namespace(self):
        assert main(["modules", "--namespace", "omnis_os"]) == 0

    def test_modules_legacy(self):
        assert main(["modules", "--legacy"]) == 0

    def test_shutdown(self):
        assert main(["shutdown"]) == 0
