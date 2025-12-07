class TicketFormatterDict:
    DEFAULT_STR = "N/A"
    DEFAULT_DATE = "1970-01-01"
    DEFAULT_TIME = "00:00:00"

    def __init__(self, user: dict, ticket: dict, trip: dict):
        self.user = user
        self.ticket = ticket
        self.trip = trip

    def ticket_details(self) -> dict:
        return {
            "first_name": self.user.get("first_name", self.DEFAULT_STR),
            "last_name": self.user.get("last_name", self.DEFAULT_STR),
            "route": f"{self.trip.get('route_name', self.DEFAULT_STR)}",
            "date": (
                self.trip.get("date") if self.trip.get("date") else self.DEFAULT_DATE
            ),
            "hour": (
                self.trip.get("start_time")
                if self.trip.get("start_time")
                else self.DEFAULT_TIME
            ),
            "email": self.user.get("email", self.DEFAULT_STR),
            "seat_code": str(self.ticket.get("seat_number", 0)),
        }

    def billing_details(self) -> dict:
        return {
            "first_name": self.user.get("first_name", self.DEFAULT_STR),
            "last_name": self.user.get("last_name", self.DEFAULT_STR),
            "company": self.user.get("company", self.DEFAULT_STR),
            "tax_number": self.user.get("tax_number", self.DEFAULT_STR),
            "street_address": self.user.get("street_address", self.DEFAULT_STR),
            "zip_code": self.user.get("zip_code", self.DEFAULT_STR),
            "city": self.user.get("city", self.DEFAULT_STR),
            "country": self.user.get("country", self.DEFAULT_STR),
        }

    def to_dict(self) -> dict:
        return {
            "ticket_details": self.ticket_details(),
            "billing_details": self.billing_details(),
            "reservation_id": str(self.ticket.get("id", self.DEFAULT_STR)),
            "amount": str(self.ticket.get("price", 0)),
            "currency": "MDL",
        }
