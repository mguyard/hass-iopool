"""DataUpdateCoordinator for iopool integration."""

# import asyncio
# import json
import logging

# from pathlib import Path
from aiohttp.client_exceptions import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, POOLS_ENDPOINT
from .models import iopoolData

_LOGGER = logging.getLogger(__name__)


class IopoolDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage data updates for iopool devices."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize the coordinator."""
        self.api_key = api_key
        self.headers = {"x-api-key": api_key}
        self.hass = hass
        self.session = async_get_clientsession(hass)

        # Track known pool IDs
        self._known_pool_ids = set()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> iopoolData:
        """Fetch data from iopool API."""
        _LOGGER.debug("Updating iopool data with API key %s", self.api_key)
        try:
            async with self.session.get(
                POOLS_ENDPOINT, headers=self.headers
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # ---------- DEVELOPMENT ONLY ----------
                # Uncomment the following lines to use test data from a local file
                # try:
                #     test_file_path = Path(__file__).parent / "test.json"
                #     if test_file_path.exists():

                #         async def read_test_file():
                #             return json.loads(
                #                 await asyncio.to_thread(
                #                     test_file_path.read_text, encoding="utf-8"
                #                 )
                #             )

                #         data = await read_test_file()
                #         _LOGGER.debug(
                #             "Using test data from test.json instead of API response"
                #         )
                # except (json.JSONDecodeError, OSError) as err:
                #     _LOGGER.debug("Could not load test data: %s", err)
                # ---------- DEVELOPMENT ONLY ----------

                _LOGGER.debug("iopool Response data: %s", data)

                # Process the response data
                iopool_data = iopoolData.from_dict(data)

                # Clean up removed devices
                await self._cleanup_removed_devices(iopool_data)

                # Convert raw data to model objects
                _LOGGER.debug("Converting data to iopoolData model")
                _LOGGER.debug("iopool Converted data: %s", iopoolData.from_dict(data))
                return iopoolData.from_dict(data)

        except (TimeoutError, ClientError) as error:
            _LOGGER.error("Error fetching data from iopool API: %s", error)
            raise UpdateFailed(f"Error communicating with API: {error}") from error
        except (KeyError, ValueError) as error:
            _LOGGER.error("Error parsing response from iopool API: %s", error)
            raise UpdateFailed(f"Error parsing API response: {error}") from error

    async def _cleanup_removed_devices(self, iopool_data: iopoolData) -> None:
        """Remove devices that no longer exist in the API response."""
        _LOGGER.debug("Cleaning up removed devices")

        # Get current pool IDs from API response
        current_pool_ids = {pool.id for pool in iopool_data.pools}
        _LOGGER.debug("Current pool IDs from API: %s", current_pool_ids)

        # Get device registry
        device_registry = async_get_device_registry(self.hass)

        # Find all devices that belong to our integration
        our_devices = [
            device
            for device in device_registry.devices.values()
            if any(ident[0] == DOMAIN for ident in device.identifiers)
        ]

        # Check each device if it still exists in the API response
        for device in our_devices:
            # Extract the pool ID from the device identifiers
            # Device identifiers format is a set of tuples: {(domain, id), ...}
            pool_ids = [ident[1] for ident in device.identifiers if ident[0] == DOMAIN]

            if not pool_ids:
                continue

            pool_id = pool_ids[0]  # We should only have one ID per device

            # If the pool ID is not in the current API response, remove the device
            if pool_id not in current_pool_ids:
                _LOGGER.info(
                    "Removing device %s (pool ID: %s) as it no longer exists in API",
                    device.id,
                    pool_id,
                )
                device_registry.async_remove_device(device.id)
