from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


class BaseBackend:
    def __init__(self, **kwargs):
        pass

    def list_trips(self, origin: str, destination: str) -> list[dict]:
        raise NotImplementedError

    def get_trip(self, trip_id: int, origin: str, destination: str) -> dict | None:
        raise NotImplementedError

    def get_seat_info(self, trip_id: int, origin: str, destination: str) -> dict | None:
        raise NotImplementedError


def get_depot_backend() -> BaseBackend:
    module_settings = getattr(settings, "DEPOT", {})
    module_string = module_settings.get("backend")
    module_options = module_settings.get("options", {})

    if not module_string:
        raise ImproperlyConfigured("No DEPOT backend configured")

    module_class = import_string(module_string)

    from tickets.depot.backends.client import DepotClient

    client = DepotClient(
        base_url=module_options.get("base_url"),
        timeout=module_options.get("timeout", 10),
    )

    return module_class(client=client)

    # return module_class(**module_options)
