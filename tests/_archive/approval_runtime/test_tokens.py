import pytest

from src.approval_runtime.tokens import TokenVerifier
from src.approval_runtime.errors import InvalidTokenError


class TestTokenVerifier:
    def test_generate_and_verify(self):
        tv = TokenVerifier()
        token = tv.generate_token("apr_1")
        assert token.startswith("omnis_approval_")
        assert tv.verify("apr_1", token) is True

    def test_verify_wrong_token_raises(self):
        tv = TokenVerifier()
        tv.generate_token("apr_1")
        with pytest.raises(InvalidTokenError):
            tv.verify("apr_1", "wrong_token")

    def test_verify_unknown_request_raises(self):
        tv = TokenVerifier()
        with pytest.raises(InvalidTokenError):
            tv.verify("unknown", "some_token")

    def test_cannot_use_token_twice(self):
        tv = TokenVerifier()
        token = tv.generate_token("apr_1")
        tv.verify("apr_1", token)
        with pytest.raises(InvalidTokenError):
            tv.verify("apr_1", token)

    def test_revoke(self):
        tv = TokenVerifier()
        token = tv.generate_token("apr_1")
        tv.revoke("apr_1")
        with pytest.raises(InvalidTokenError):
            tv.verify("apr_1", token)
