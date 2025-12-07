from urllib.parse import urljoin

from requests import Session


class DepotClient(Session):
    def __init__(self, base_url: str, api_key: str = None, timeout: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

        if self.api_key:
            self.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def request(self, method: str, url: str, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        return super().request(method, urljoin(self.base_url, url), **kwargs)
