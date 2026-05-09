"""Manual publishing tracker errors."""


class ManualPublishingError(Exception):
    pass


class PublishRecordNotFoundError(ManualPublishingError):
    pass
