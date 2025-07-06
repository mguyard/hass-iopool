"""The iopool integration."""

from __future__ import annotations

from dataclasses import asdict
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import CoreState, Event, HomeAssistant

from .const import CONF_API_KEY, DOMAIN
from .coordinator import IopoolDataUpdateCoordinator
from .filtration import Filtration
from .models import IopoolConfigData, IopoolConfigEntry, IopoolData

_LOGGER = logging.getLogger(__name__)

# Keep sensor before binary_sensor for correct loading order
# This is important for the filtration entity to be created after the binary sensor
PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: IopoolConfigEntry) -> bool:
    """Set up iopool from a config entry."""
    config = IopoolConfigData.from_config_entry(entry)
    # Convert IopoolConfigData to a standard dictionary
    config_dict = asdict(config)

    coordinator = IopoolDataUpdateCoordinator(hass, config_dict[CONF_API_KEY])

    # Fetch initial data to populate the coordinator
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = IopoolData(
        config=config,
        coordinator=coordinator,
        filtration=None,
        remove_time_listeners=[],  # Store time listeners to remove them later
    )

    # Create a Filtration instance and store it in runtime_data
    # To avoid circular reference, we create the Filtration instance
    filtration = Filtration(entry=entry)
    entry.runtime_data.filtration = filtration

    # Store also in hass.data for compatibility with other components
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config_entry": entry,
    }

    # Set up all platforms for this device/entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register an update listener to handle config changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Store the configuration function in runtime_data
    entry.runtime_data.setup_time_events = filtration.setup_time_events

    # Configure time events immediately if filtration is enabled and HA is fully running
    if filtration.config_filtration_enabled() and hass.state == CoreState.running:
        filtration.setup_time_events()

    # Also configure events when HA is fully started
    async def _on_started(event: Event) -> None:
        """Handle Home Assistant fully started event."""
        # Configure events only if filtration is enabled
        if filtration.config_filtration_enabled():
            filtration.setup_time_events()
        else:
            _LOGGER.debug(
                "ON_STARTED : Filtration not enabled, skipping time events setup"
            )

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: IopoolConfigEntry) -> bool:
    """Unload a config entry."""
    # Clean up time event listeners
    if entry.runtime_data and hasattr(entry.runtime_data, "remove_time_listeners"):
        for remove_listener in entry.runtime_data.remove_time_listeners:
            remove_listener()

    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
        return unload_ok
    return False


async def update_listener(hass: HomeAssistant, entry: IopoolConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Options updated for entry %s, reconfiguring", entry.entry_id)
    # Update the runtime_data.config with new configuration values
    # This ensures entities can access the new config before the reload completes
    if entry.runtime_data is not None:
        entry.runtime_data.config = IopoolConfigData.from_config_entry(entry)

    # Reload the entry to recreate runtime_data and entities
    await hass.config_entries.async_reload(entry.entry_id)
