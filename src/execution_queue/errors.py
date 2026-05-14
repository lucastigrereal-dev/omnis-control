class QueueError(Exception):
    pass


class QueueBlockedError(QueueError):
    pass


class QueueStateError(QueueError):
    pass
