from websockets.exceptions import ConnectionClosed

ConnectionClosed = ConnectionClosed


class InvalidMessage(Exception):
    pass


class InvalidPayloadSyntax(InvalidMessage):
    pass


class NotAllowedEventName(Exception):
    def __init__(self, event):
        super().__init__("{} is a predefined Phoenix-event.".format(event))


class CommunicationError(Exception):
    pass
