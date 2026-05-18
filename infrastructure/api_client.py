"""HTTP client for Faceit API - infrastructure layer."""
from typing import Any, Optional, Protocol
import requests


class HTTPClient(Protocol):
    """Protocol for HTTP client to allow different implementations."""

    def get(self, url: str, headers: dict[str, str], params: Optional[dict] = None) -> dict[str, Any]:
        """Make GET request and return JSON response."""
        ...


class RequestsHTTPClient:
    """Concrete implementation using requests library."""

    def get(self, url: str, headers: dict[str, str], params: Optional[dict] = None) -> dict[str, Any]:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


class FaceitAPIError(Exception):
    """Raised when Faceit API returns an error."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class FaceitAPIClient:
    """Client for interacting with Faceit API."""

    BASE_URL = "https://open.faceit.com/data/v4"

    def __init__(self, api_key: str, http_client: HTTPClient | None = None) -> None:
        self._api_key = api_key
        self._http_client = http_client or RequestsHTTPClient()
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json"
        }

    def get(self, endpoint: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make GET request to Faceit API."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            return self._http_client.get(url, self._headers, params)
        except requests.exceptions.HTTPError as err:
            raise FaceitAPIError(
                status_code=err.response.status_code,
                message=str(err)
            ) from err
