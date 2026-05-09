"""Errors for Role Registry."""


class RoleRegistryError(Exception):
    pass


class InvalidRolesConfigError(RoleRegistryError):
    pass


class RoleNotFoundError(RoleRegistryError):
    pass
