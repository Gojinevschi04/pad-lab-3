from requests import HTTPError


class DepotServiceError(HTTPError):
    def __init__(self, method: str, path: str, original: Exception | None = None):
        self.method = method
        self.path = path
        self.original = original

        original_message = type(original).__name__ if original else "Unknown error"

        super().__init__(f"Depot service {method} {path} failed: {original_message}")
