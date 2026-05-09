class SectorRegistryError(Exception):
    pass

class InvalidSectorConfigError(SectorRegistryError):
    pass

class SectorNotFoundError(SectorRegistryError):
    pass
