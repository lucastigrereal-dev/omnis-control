"""P26 App Factory Supreme — errors."""


class AppFactorySupremeError(Exception):
    """Base error for P26 App Factory Supreme."""
    pass


class BuildError(AppFactorySupremeError):
    """Build failed during code generation."""
    pass


class VerificationError(AppFactorySupremeError):
    """Build failed verification (tests, policy scan)."""
    pass


class PackageError(AppFactorySupremeError):
    """Build failed during packaging."""
    pass


class BlueprintNotApprovedError(AppFactorySupremeError):
    """Blueprint was not approved — cannot proceed to generation."""
    pass


class SecurityScanFailedError(AppFactorySupremeError):
    """Policy scan found critical violations — cannot package."""
    pass


class RollbackError(AppFactorySupremeError):
    """Rollback operation failed."""
    pass
