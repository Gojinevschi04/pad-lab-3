class TicketError(Exception):
    """Base ticket error."""


class SeatAlreadyTakenError(TicketError):
    pass


class TicketNotFoundError(TicketError):
    pass


class TicketAlreadyCancelledError(TicketError):
    pass
