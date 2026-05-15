from src.runtime_cli.smoke import run_smoke_tests


class TestSmokeTests:
    def test_run_all_smoke_tests(self):
        result = run_smoke_tests()
        assert result.total == 9
        assert result.passed == 9
        assert result.failed == 0
        assert result.all_passed is True

    def test_smoke_results_have_entries(self):
        result = run_smoke_tests()
        assert len(result.results) == 9
        for entry in result.results:
            assert entry["status"] == "PASS"
