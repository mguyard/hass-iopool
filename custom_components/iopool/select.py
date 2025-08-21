"""Select platform for iopool integration."""

from __future__ import annotations

import datetime
import logging
import re
from typing import Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .api_models import IopoolAPIResponsePool
from .const import (
    CONF_OPTIONS_FILTRATION_SWITCH_ENTITY,
    CONF_POOL_ID,
    EVENT_TYPE_BOOST_CANCELED,
    EVENT_TYPE_BOOST_END,
    EVENT_TYPE_BOOST_START,
    SENSOR_BOOST_SELECTOR,
    SENSOR_POOL_MODE,
)
from .coordinator import IopoolDataUpdateCoordinator
from .entity import IopoolEntity
from .filtration import Filtration
from .models import IopoolConfigData, IopoolConfigEntry

_LOGGER = logging.getLogger(__name__)

BOOST_OPTIONS: Final = ["None", "1H", "2H", "4H", "8H", "24H"]
MODE_OPTIONS: Final = ["Standard", "Active-Winter", "Passive-Winter"]

# Entity descriptions for each pool
POOL_SELECTS_CONDITIONAL_FILTRATION = [
    SelectEntityDescription(
        key=SENSOR_BOOST_SELECTOR,
        translation_key=SENSOR_BOOST_SELECTOR,
        icon="mdi:plus-box-multiple",
    ),
    SelectEntityDescription(
        key=SENSOR_POOL_MODE,
        translation_key=SENSOR_POOL_MODE,
        icon="mdi:sun-snowflake-variant",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IopoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the iopool select entities."""
    coordinator: IopoolDataUpdateCoordinator = entry.runtime_data.coordinator
    config: IopoolConfigData = entry.runtime_data.config
    filtration: Filtration = entry.runtime_data.filtration
    pool_id = entry.data[CONF_POOL_ID]

    # Get pool data for the specific pool_id
    pool = coordinator.get_pool_data(pool_id)
    if pool is None:
        _LOGGER.error("No pool found with ID: %s", pool_id)
        return

    entities = []

    switch_entity: str | None = config.options.filtration.get(
        CONF_OPTIONS_FILTRATION_SWITCH_ENTITY, None
    )
    filtration_enable: bool = filtration.configuration_filtration_enabled
    _LOGGER.debug(
        "SELECT Conditional Entities - Switch entity: %s, Filtration enable: %s",
        switch_entity,
        filtration_enable,
    )

    # Create entities for the specific pool if filtration is enabled
    if switch_entity and filtration_enable:
        entities.extend(
            [
                IopoolSelect(
                    coordinator,
                    filtration,
                    description,
                    entry.entry_id,
                    pool.id,
                    pool.title,
                )
                for description in POOL_SELECTS_CONDITIONAL_FILTRATION
            ]
        )

    async_add_entities(entities)


class IopoolSelect(IopoolEntity, SelectEntity):
    """Representation of an iopool select entity."""

    def __init__(
        self,
        coordinator: IopoolDataUpdateCoordinator,
        filtration: Filtration,
        description: SelectEntityDescription,
        config_entry_id: str,
        pool_id: str,
        pool_name: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, config_entry_id, pool_id, pool_name)
        self._config_entry_id = config_entry_id
        self.entity_description = description
        self._boost_timer = None
        self._filtration: Filtration = filtration
        self._attr_extra_state_attributes = {}

        # Set unique_id for state persistence
        self._attr_unique_id = f"{config_entry_id}_{pool_id}_{description.key}"

        # Set custom entity_id with iopool_ prefix
        snake_pool_name = pool_name.lower().replace(" ", "_")
        self.entity_id = f"select.iopool_{snake_pool_name}_{description.key}"

    @property
    def options(self) -> list[str]:
        """Return the list of available options (keys, not translated labels)."""
        # For boost selector
        if self.entity_description.key == SENSOR_BOOST_SELECTOR:
            return BOOST_OPTIONS
        # For pool mode
        if self.entity_description.key == SENSOR_POOL_MODE:
            return MODE_OPTIONS
        return []

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        return self.entity_description.icon

    def _get_pool(self) -> IopoolAPIResponsePool | None:
        """Get the pool data from coordinator."""
        return self.coordinator.get_pool_data(self._pool_id)

    async def _clean_filtration_attributes_active_slot(self) -> None:
        """Clean up the active slot attribute in filtration attributes."""
        _, _, filtration_attributes = await self._filtration.get_filtration_attributes()
        if filtration_attributes.get("active_slot", None) == "boost":
            await self._filtration.update_filtration_attributes(active_slot=None)

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to register update signal handler."""
        await super().async_added_to_hass()

        # Try to restore the last state
        last_state = await self.async_get_last_state()

        if last_state and last_state.state in self.options:
            # If we have a valid last state, use it
            self._attr_current_option = last_state.state

            # Check if there was a boost in progress
            if (
                self.entity_description.key == SENSOR_BOOST_SELECTOR
                and self._attr_current_option != "None"
                and last_state.attributes.get("boost_end_time")
            ):
                # Get the stored end time
                end_time_str = last_state.attributes.get("boost_end_time")
                # Parse datetime - stored times are already in local timezone
                end_time = dt_util.parse_datetime(end_time_str)

                # Only set up a timer if the end time is in the future
                now = dt_util.utcnow()
                if end_time and end_time > now:
                    _LOGGER.debug(
                        "Restoring boost timer with end time: %s", end_time_str
                    )
                    self._boost_timer = async_track_point_in_time(
                        self.hass, self._async_boost_timer_finished, end_time
                    )
                    # Store end time in attributes for persistence
                    self._attr_extra_state_attributes["boost_end_time"] = end_time_str

                    # Also restore start time attribute if available
                    if start_time_str := last_state.attributes.get("boost_start_time"):
                        self._attr_extra_state_attributes["boost_start_time"] = (
                            start_time_str
                        )
                else:
                    # Boost has expired during restart, set to None
                    _LOGGER.debug("Boost expired during restart, turning off")
                    self._attr_current_option = "None"
                    await self._filtration.async_stop_filtration()
                    await self._clean_filtration_attributes_active_slot()
        else:
            # Otherwise, initialize with default value
            self._attr_current_option = self._get_initial_option()

    def _get_initial_option(self) -> str:
        """Get the initial option based on the select type."""
        if self.entity_description.key == SENSOR_BOOST_SELECTOR:
            return "None"
        if self.entity_description.key == SENSOR_POOL_MODE:
            pool = self._get_pool()
            if pool and pool.mode:
                # Map the pool mode to the select option
                if pool.mode == "STANDARD":
                    return "Standard"
                if pool.mode == "ACTIVE_WINTER":
                    return "Active-Winter"
                if pool.mode == "WINTER":
                    return "Passive-Winter"
        # Default to first option if no match found
        return self.options[0] if self.options else "Unknown"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        old_option = self._attr_current_option
        self._attr_current_option = option
        self._reload_required = False

        # Handle boost timer logic only for boost selector
        if self.entity_description.key == SENSOR_BOOST_SELECTOR:
            # Cancel any existing timer
            if self._boost_timer is not None:
                self._boost_timer()
                self._boost_timer = None

                # Get start time for duration calculation
                start_time_str = self._attr_extra_state_attributes.get(
                    "boost_start_time"
                )

                if start_time_str and old_option != "None":
                    # Calculate actual duration for canceled boost
                    start_time = dt_util.parse_datetime(start_time_str)
                    end_time = dt_util.as_local(dt_util.utcnow())
                    end_time_str = end_time.isoformat()

                    if start_time:
                        duration_seconds = (
                            end_time.replace(tzinfo=None)
                            - start_time.replace(tzinfo=None)
                        ).total_seconds()
                        duration_minutes = int(duration_seconds / 60)

                        # Fire canceled boost event using filtration's publish_event
                        await self._filtration.publish_event(
                            EVENT_TYPE_BOOST_CANCELED,
                            {
                                "start_time": start_time_str,
                                "end_time": end_time_str,
                                "duration_minutes": duration_minutes,
                            },
                        )

                # Clear boost times from attributes
                self._attr_extra_state_attributes.pop("boost_end_time", None)
                self._attr_extra_state_attributes.pop("boost_start_time", None)

            # If a boost time is selected, schedule end time
            if option != "None":
                # Parse the boost duration (1H, 2H, 4H, 8H, 24H)
                match = re.match(r"(\d+)H", option)
                if match:
                    hours = int(match.group(1))
                    _LOGGER.debug("Starting boost for %s hours", hours)

                    # Start filtration
                    await self._filtration.async_start_filtration()

                    # Record start time in UTC for internal use
                    start_time_utc = dt_util.utcnow()
                    # Convert to local time for display and storage
                    start_time_local = dt_util.as_local(start_time_utc)
                    start_time_str = start_time_local.isoformat()
                    self._attr_extra_state_attributes["boost_start_time"] = (
                        start_time_str
                    )

                    # Schedule the end of boost (using UTC internally)
                    end_time_utc = start_time_utc + datetime.timedelta(hours=hours)
                    self._boost_timer = async_track_point_in_time(
                        self.hass, self._async_boost_timer_finished, end_time_utc
                    )

                    # Store end time in local timezone for display
                    end_time_local = dt_util.as_local(end_time_utc)
                    end_time_str = end_time_local.isoformat()
                    self._attr_extra_state_attributes["boost_end_time"] = end_time_str
                    _LOGGER.debug(
                        "Boost: start=%s, end=%s", start_time_str, end_time_str
                    )

                    # Calculate duration in minutes
                    duration_minutes = hours * 60

                    # Fire start boost event using filtration's publish_event
                    await self._filtration.publish_event(
                        EVENT_TYPE_BOOST_START,
                        {
                            "start_time": start_time_str,
                            "end_time": end_time_str,
                            "duration_minutes": duration_minutes,
                        },
                    )
            elif old_option != "None" and old_option is not None:
                # If changing from boost to None, turn off filtration
                await self._filtration.async_stop_filtration()
                await self._clean_filtration_attributes_active_slot()

        if self.entity_description.key == SENSOR_POOL_MODE:
            if self._attr_current_option in {
                "Standard",
                "Active-Winter",
                "Passive-Winter",
            }:
                self._reload_required = True

        self.async_write_ha_state()

        if self._reload_required:
            # Reload the integration to apply the new mode.
            # Necessary to clear/create async_track_time_change
            _LOGGER.debug(
                "Reloading integration to apply new mode: Old=%s, New=%s",
                old_option,
                option,
            )
            self.hass.config_entries.async_schedule_reload(self._config_entry_id)

    @callback
    async def _async_boost_timer_finished(self, _now=None):
        """Handle boost timer finished."""
        _LOGGER.debug("Boost timer expired, turning off filtration")
        self._boost_timer = None

        # Get boost times for event data
        start_time_str = self._attr_extra_state_attributes.get("boost_start_time")
        end_time_str = self._attr_extra_state_attributes.get("boost_end_time")

        # Get filtration state
        _, _, filtration_attributes = await self._filtration.get_filtration_attributes()
        _LOGGER.debug("Filtration state at boost end: %s", filtration_attributes)

        if start_time_str and end_time_str:
            # Calculate actual duration
            start_time = dt_util.parse_datetime(start_time_str)
            end_time = dt_util.parse_datetime(end_time_str)

            if start_time and end_time:
                duration_seconds = (
                    end_time.replace(tzinfo=None) - start_time.replace(tzinfo=None)
                ).total_seconds()
                duration_minutes = int(duration_seconds / 60)

                # Fire end boost event using filtration's publish_event
                await self._filtration.publish_event(
                    EVENT_TYPE_BOOST_END,
                    {
                        "start_time": start_time_str,
                        "end_time": end_time_str,
                        "duration_minutes": duration_minutes,
                    },
                )

        self._attr_current_option = "None"
        # Clear boost times from attributes
        self._attr_extra_state_attributes.pop("boost_end_time", None)
        self._attr_extra_state_attributes.pop("boost_start_time", None)
        # Stop filtration if no active slot is set
        if filtration_attributes.get("active_slot", None) is None:
            _LOGGER.info("No active slot, stopping filtration")
            await self._filtration.async_stop_filtration()
        await self._clean_filtration_attributes_active_slot()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """When entity is removed from hass."""
        # Clean up any running timers
        if self._boost_timer is not None:
            self._boost_timer()
            self._boost_timer = None
        await super().async_will_remove_from_hass()
