"""Frontend for iopool Cards."""

import logging
import pathlib

from homeassistant.components.http import StaticPathConfig
from homeassistant.const import __version__ as ha_version
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

URL_BASE = "/iopool"
CARD_FILENAME = "iopool-card.js"


def _get_card_version() -> str:
    """Get the card version from iopool-card.version file."""
    version_file = pathlib.Path(__file__).parent / "iopool-card.version"
    return version_file.read_text().strip()


def _ha_version_tuple(version_str: str) -> tuple:
    """Convert HA version string to tuple for comparison."""
    try:
        parts = version_str.split(".")
        return tuple(int(x) for x in parts[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


_HA_VERSION = _ha_version_tuple(ha_version)


class IopoolCardRegistration:
    """Manage iopool frontend card registration."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        self.hass = hass

    @property
    def lovelace_resource_mode(self) -> str:
        """Get the Lovelace resource mode, handling HA version differences."""
        if _HA_VERSION >= (2026, 2, 0):
            return self.hass.data["lovelace"].resource_mode
        if _HA_VERSION >= (2025, 2, 0):
            return self.hass.data["lovelace"].mode
        return self.hass.data["lovelace"]["mode"]

    @property
    def lovelace_resources(self):
        """Get Lovelace resources, handling HA version differences."""
        if _HA_VERSION >= (2025, 2, 0):
            return self.hass.data["lovelace"].resources
        return self.hass.data["lovelace"]["resources"]

    async def async_register(self) -> None:
        """Register static path and Lovelace resource."""
        await self._async_register_path()
        if self.lovelace_resource_mode == "storage":
            await self._async_wait_for_resources()

    async def _async_register_path(self) -> None:
        """Register static path for the frontend directory."""
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, pathlib.Path(__file__).parent, False)]
            )
            _LOGGER.debug("Registered iopool frontend path from %s", pathlib.Path(__file__).parent)
        except RuntimeError:
            _LOGGER.debug("iopool frontend static path already registered")

    async def _async_wait_for_resources(self) -> None:
        """Wait for Lovelace resources to load, then register card."""

        async def check_resources_loaded(now):
            if self.lovelace_resources.loaded:
                await self._async_register_card()
            else:
                _LOGGER.debug("Lovelace resources not yet loaded, retrying in 5 seconds")
                async_call_later(self.hass, 5, check_resources_loaded)

        await check_resources_loaded(0)

    async def _async_register_card(self) -> None:
        """Add or update the iopool card Lovelace resource."""
        version = _get_card_version()
        url = f"{URL_BASE}/{CARD_FILENAME}"
        _LOGGER.debug("Registering iopool card as version %s", version)

        existing = [
            res for res in self.lovelace_resources.async_items()
            if res["url"].startswith(url)
        ]

        if existing:
            res = existing[0]
            current_version = self._get_resource_version(res["url"])
            if current_version != version:
                _LOGGER.debug("Updating iopool card to version %s", version)
                await self.lovelace_resources.async_update_item(
                    res["id"],
                    {"res_type": "module", "url": f"{url}?v={version}"},
                )
            else:
                _LOGGER.debug("iopool card already registered as version %s", version)
        else:
            _LOGGER.debug("Creating iopool card resource, version %s", version)
            await self.lovelace_resources.async_create_item(
                {"res_type": "module", "url": f"{url}?v={version}"}
            )

    @staticmethod
    def _get_resource_version(url: str) -> str:
        """Extract version from resource URL."""
        try:
            return url.split("?v=")[1]
        except (IndexError, AttributeError):
            return ""

    async def async_unregister(self) -> None:
        """Remove the iopool card from Lovelace resources."""
        if self.lovelace_resource_mode != "storage":
            return
        url = f"{URL_BASE}/{CARD_FILENAME}"
        resources = [
            res for res in self.lovelace_resources.async_items()
            if res["url"].startswith(url)
        ]
        for resource in resources:
            await self.lovelace_resources.async_delete_item(resource["id"])
