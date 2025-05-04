"""The iopool integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import IopoolDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Update platforms to include binary_sensor
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iopool from a config entry."""
    api_key = entry.data["api_key"]

    coordinator = IopoolDataUpdateCoordinator(hass, api_key)

    # Fetch initial data to populate the coordinator
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in hass data for later reference
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Set up all platforms for this device/entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register an update listener to handle config changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator from hass data
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
