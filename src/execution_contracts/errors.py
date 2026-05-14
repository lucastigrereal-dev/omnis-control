class ContractError(Exception):
    pass


class ValidationError(ContractError):
    pass


class PermissionError(ContractError):
    pass


class OutcomeError(ContractError):
    pass
