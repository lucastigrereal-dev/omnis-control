"""Campaign package errors."""


class CampaignError(Exception):
    pass


class CampaignNotFoundError(CampaignError):
    pass


class CampaignValidationError(CampaignError):
    pass
