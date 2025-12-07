import requests

from tickets.treasury.backends.base import BaseBackend
from tickets.treasury.backends.client import TreasuryClient
from tickets.treasury.exceptions import TreasuryServiceError
from tickets.treasury.formatter import TicketFormatterDict


class TreasuryServiceBackend(BaseBackend):
    def __init__(self, client: TreasuryClient):
        super().__init__()
        self.client = client

    def _request(self, method: str, path: str, **kwargs) -> dict | None:
        try:
            response = self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, requests.JSONDecodeError) as exception:
            raise TreasuryServiceError(method.upper(), path, exception) from exception

    def pay_ticket(
        self, user_data: dict, ticket_data: dict, trip_data: dict
    ) -> dict | None:
        data = TicketFormatterDict(user_data, ticket_data, trip_data).to_dict()

        return self._request(
            "post",
            "api/invoices",
            json=data,
        )

    def refund_ticket(self, invoice_data: dict) -> dict | None:
        return self._request("post", "api/refund", json=invoice_data)
