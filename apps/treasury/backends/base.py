from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


class BaseBackend:
    def __init__(self, **kwargs):
        pass

    def pay_ticket(
        self, user_data: dict, ticket_data: dict, trip_data: dict
    ) -> dict | None:
        raise NotImplementedError

    def refund_ticket(self, invoice_data: dict) -> dict | None:
        raise NotImplementedError


def get_treasury_backend() -> BaseBackend:
    module_settings = getattr(settings, "TREASURY", {})
    module_string = module_settings.get("backend")
    module_options = module_settings.get("options", {})

    if not module_string:
        raise ImproperlyConfigured("No TREASURY backend configured")

    module_class = import_string(module_string)
    from tickets.treasury.backends.client import TreasuryClient

    client = TreasuryClient(
        base_url=module_options.get("base_url"),
        # api_key=module_options.get("api_key"), # to do - keep add authorization
        timeout=module_options.get("timeout", 10),
    )

    return module_class(client=client)

    # return module_class(**module_options)
