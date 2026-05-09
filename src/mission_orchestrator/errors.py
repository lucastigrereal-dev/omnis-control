class OrchestratorError(Exception):
    pass

class UnknownIntentError(OrchestratorError):
    pass

class RunNotFoundError(OrchestratorError):
    pass
