from src.observability.error_taxonomy import (
    ErrorCategory,
    ErrorSeverity,
    ErrorClassifier,
    ClassifiedError,
    CATEGORY_SEVERITY_MAP,
)


class TestErrorCategory:
    def test_all_categories(self):
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.RUNTIME.value == "runtime"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.IO.value == "io"
        assert ErrorCategory.SECURITY.value == "security"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.DEPENDENCY.value == "dependency"
        assert ErrorCategory.STATE_MACHINE.value == "state_machine"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestErrorSeverity:
    def test_all_severities(self):
        assert ErrorSeverity.FATAL.value == "fatal"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"


class TestCategorySeverityMap:
    def test_configuration_is_fatal(self):
        assert CATEGORY_SEVERITY_MAP[ErrorCategory.CONFIGURATION] == ErrorSeverity.FATAL

    def test_security_is_fatal(self):
        assert CATEGORY_SEVERITY_MAP[ErrorCategory.SECURITY] == ErrorSeverity.FATAL

    def test_timeout_is_warning(self):
        assert CATEGORY_SEVERITY_MAP[ErrorCategory.TIMEOUT] == ErrorSeverity.WARNING


class TestClassifiedError:
    def test_defaults(self):
        ce = ClassifiedError()
        assert ce.category == ErrorCategory.UNKNOWN
        assert ce.severity == ErrorSeverity.ERROR

    def test_fields(self):
        ce = ClassifiedError(
            error_id="e1",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            message="bad input",
            original_exception="ValueError",
            context={"field": "name"},
        )
        assert ce.error_id == "e1"
        assert ce.message == "bad input"
        assert ce.context == {"field": "name"}


class TestErrorClassifier:
    def test_classify_validation(self):
        result = ErrorClassifier.classify("invalid schema detected")
        assert result.category == ErrorCategory.VALIDATION
        assert result.severity == ErrorSeverity.ERROR

    def test_classify_timeout(self):
        result = ErrorClassifier.classify("connection timed out after 30s")
        assert result.category == ErrorCategory.TIMEOUT
        assert result.severity == ErrorSeverity.WARNING

    def test_classify_configuration(self):
        result = ErrorClassifier.classify("missing configuration key: API_URL")
        assert result.category == ErrorCategory.CONFIGURATION
        assert result.severity == ErrorSeverity.FATAL

    def test_classify_security(self):
        result = ErrorClassifier.classify("permission denied for operation")
        assert result.category == ErrorCategory.SECURITY
        assert result.severity == ErrorSeverity.FATAL

    def test_classify_io(self):
        result = ErrorClassifier.classify("file not found: /tmp/missing.json")
        assert result.category == ErrorCategory.IO
        assert result.severity == ErrorSeverity.ERROR

    def test_classify_dependency(self):
        result = ErrorClassifier.classify("import error: no module named 'foo'")
        assert result.category == ErrorCategory.DEPENDENCY
        assert result.severity == ErrorSeverity.ERROR

    def test_classify_state_machine(self):
        result = ErrorClassifier.classify("invalid state transition from DRAFT to PUBLISHED")
        assert result.category == ErrorCategory.STATE_MACHINE
        assert result.severity == ErrorSeverity.FATAL

    def test_classify_runtime(self):
        result = ErrorClassifier.classify("unexpected null reference in handler")
        assert result.category == ErrorCategory.RUNTIME
        assert result.severity == ErrorSeverity.ERROR

    def test_classify_unknown(self):
        result = ErrorClassifier.classify("something weird happened")
        assert result.category == ErrorCategory.UNKNOWN
        assert result.severity == ErrorSeverity.ERROR

    def test_classify_by_exception_type_fallback(self):
        result = ErrorClassifier.classify(
            "an error occurred",
            exception_type="ValidationError",
        )
        assert result.category == ErrorCategory.VALIDATION

    def test_classify_with_context(self):
        result = ErrorClassifier.classify(
            "disk full",
            context={"path": "/data", "available_bytes": 0},
        )
        assert result.category == ErrorCategory.IO
        assert result.context["path"] == "/data"

    def test_is_retryable(self):
        assert ErrorClassifier.is_retryable(ErrorCategory.TIMEOUT) is True
        assert ErrorClassifier.is_retryable(ErrorCategory.IO) is True
        assert ErrorClassifier.is_retryable(ErrorCategory.DEPENDENCY) is True
        assert ErrorClassifier.is_retryable(ErrorCategory.VALIDATION) is False
        assert ErrorClassifier.is_retryable(ErrorCategory.CONFIGURATION) is False

    def test_is_fatal(self):
        assert ErrorClassifier.is_fatal(ErrorCategory.CONFIGURATION) is True
        assert ErrorClassifier.is_fatal(ErrorCategory.SECURITY) is True
        assert ErrorClassifier.is_fatal(ErrorCategory.STATE_MACHINE) is True
        assert ErrorClassifier.is_fatal(ErrorCategory.TIMEOUT) is False
        assert ErrorClassifier.is_fatal(ErrorCategory.VALIDATION) is False
