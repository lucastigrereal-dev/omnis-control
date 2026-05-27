"""Tests for RetryPolicy — política de retry configurável por nó."""
import pytest
from src.mission_graph.retry_policy import NodeRetryConfig, RetryPolicy


class TestRetryPolicy:
    def test_default_policy_max_retries(self):
        """default_policy() deve ter max_retries=3."""
        policy = RetryPolicy.default_policy()
        assert policy.max_retries_for("any_node") == 3

    def test_strict_policy_no_retry(self):
        """strict() → should_retry deve retornar False mesmo na tentativa 0."""
        policy = RetryPolicy.strict()
        assert policy.should_retry("execute", 0) is False
        assert policy.should_retry("execute", 1) is False

    def test_node_specific_config(self):
        """Nó 'execute' tem max_retries=5; outros usam default=3."""
        policy = RetryPolicy(
            default=NodeRetryConfig(max_retries=3),
            nodes={"execute": NodeRetryConfig(max_retries=5)},
        )
        assert policy.max_retries_for("execute") == 5
        assert policy.max_retries_for("other_node") == 3

    def test_should_retry_within_limit(self):
        """attempts=2, max=3 → True."""
        policy = RetryPolicy(default=NodeRetryConfig(max_retries=3))
        assert policy.should_retry("execute", 2) is True

    def test_should_retry_at_limit(self):
        """attempts=3, max=3 → False."""
        policy = RetryPolicy(default=NodeRetryConfig(max_retries=3))
        assert policy.should_retry("execute", 3) is False
