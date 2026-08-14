"""DataUpdateCoordinator for iopool integration."""

# import asyncio
# import json
import logging

# from pathlib import Path
from aiohttp.client_exceptions import ClientError, ServerTimeoutError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_models import IopoolAPIResponse, IopoolAPIResponsePool
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, POOLS_ENDPOINT

_LOGGER = logging.getLogger(__name__)

# Number of trailing API key characters kept visible in debug logs
VISIBLE_API_KEY_CHARS = 4


def obfuscate_api_key(api_key: str) -> str:
    """Mask an API key for logging, keeping only its last 4 characters.

    Enough to let a user confirm which key is in use when reading debug logs,
    without exposing the key itself in logs that often get pasted into issues.
    """
    if not api_key:
        return ""
    if len(api_key) <= VISIBLE_API_KEY_CHARS:
        return "***"
    return f"***{api_key[-VISIBLE_API_KEY_CHARS:]}"


class IopoolDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage data updates for iopool devices."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize the coordinator."""
        self.api_key = api_key
        self.headers = {"x-api-key": api_key}
        self.hass = hass
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    def get_pool_data(self, pool_id: str) -> IopoolAPIResponsePool | None:
        """Get data for a specific pool by ID.

        The data is retrieved from the coordinator's data property,
        which is populated by the _async_update_data method from the
        DataUpdateCoordinator parent class.

        Args:
            pool_id: The ID of the pool to retrieve data for.

        Returns:
            The pool data if found, None otherwise.

        """
        if not self.data or not self.data.pools:
            return None

        return next(
            (pool for pool in self.data.pools if pool.id == pool_id),
            None,
        )

    async def _async_update_data(self) -> IopoolAPIResponse:
        """Fetch data from iopool API."""
        _LOGGER.debug(
            "Updating iopool data with API key %s", obfuscate_api_key(self.api_key)
        )
        try:
            async with self.session.get(
                POOLS_ENDPOINT, headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()

                _LOGGER.debug("iopool Response data: %s", data)

                # Convert raw data to model objects
                _LOGGER.debug("Converting data to iopoolData model")
                _LOGGER.debug(
                    "iopool Converted data: %s", IopoolAPIResponse.from_dict(data)
                )
                return IopoolAPIResponse.from_dict(data)

        except (ServerTimeoutError, ClientError) as error:
            _LOGGER.error("Error fetching data from iopool API: %s", error)
            raise UpdateFailed(f"Error communicating with API: {error}") from error
        except (KeyError, ValueError) as error:
            _LOGGER.error("Error parsing response from iopool API: %s", error)
            raise UpdateFailed(f"Error parsing API response: {error}") from error
