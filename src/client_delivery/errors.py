"""Client delivery errors."""


class ClientDeliveryError(Exception):
    pass


class DeliveryNotFoundError(ClientDeliveryError):
    pass


class DeliverySourceError(ClientDeliveryError):
    pass
