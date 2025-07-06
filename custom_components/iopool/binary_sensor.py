"""Binary sensor platform for iopool integration."""

from __future__ import annotations

from datetime import date, datetime
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import IopoolConfigEntry
from .api_models import IopoolAPIResponsePool
from .const import (
    ATTR_IS_VALID,
    ATTR_MEASURE_MODE,
    ATTR_MEASURED_AT,
    CONF_OPTIONS_FILTRATION_DURATION_PERCENT,
    CONF_OPTIONS_FILTRATION_SLOT2,
    CONF_OPTIONS_FILTRATION_SUMMER,
    CONF_POOL_ID,
    DOMAIN,
    MANUFACTURER,
    SENSOR_ACTION_REQUIRED,
    SENSOR_FILTRATION,
)
from .coordinator import IopoolDataUpdateCoordinator
from .filtration import Filtration
from .models import IopoolConfigData

_LOGGER = logging.getLogger(__name__)

# Binary sensor definition
POOL_BINARY_SENSORS = [
    BinarySensorEntityDescription(
        key=SENSOR_ACTION_REQUIRED,
        translation_key=SENSOR_ACTION_REQUIRED,
        icon="mdi:gesture-tap-button",
        device_class=BinarySensorDeviceClass.PROBLEM,
    )
]

POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION = [
    BinarySensorEntityDescription(
        key=SENSOR_FILTRATION,
        translation_key=SENSOR_FILTRATION,
        icon="mdi:water-boiler",
        device_class=BinarySensorDeviceClass.RUNNING,
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IopoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iopool binary sensors based on a config entry."""
    coordinator: IopoolDataUpdateCoordinator = entry.runtime_data.coordinator
    filtration: Filtration = entry.runtime_data.filtration
    pool_id = entry.data[CONF_POOL_ID]

    # Get pool data for the specific pool_id
    pool = coordinator.get_pool_data(pool_id)
    if pool is None:
        _LOGGER.error("No pool found with ID: %s", pool_id)
        return

    entities = []

    # Create entities for the specific pool
    entities.extend(
        [
            IopoolBinarySensor(
                coordinator,
                description,
                entry.entry_id,
                pool.id,
                pool.title,
            )
            for description in POOL_BINARY_SENSORS
        ]
    )

    if filtration.configuration_filtration_enabled:
        entities.extend(
            [
                IopoolBinarySensor(
                    coordinator,
                    description,
                    entry.entry_id,
                    pool.id,
                    pool.title,
                )
                for description in POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION
            ]
        )

    async_add_entities(entities)


class IopoolBinarySensor(CoordinatorEntity, BinarySensorEntity, RestoreEntity):
    """Representation of an iopool binary sensor."""

    coordinator: IopoolDataUpdateCoordinator

    def __init__(
        self,
        coordinator: IopoolDataUpdateCoordinator,
        description: BinarySensorEntityDescription,
        config_entry_id: str,
        pool_id: str,
        pool_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._pool_id = pool_id
        self._attr_unique_id = f"{config_entry_id}_{pool_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_translation_key = description.translation_key
        self._config: IopoolConfigData = coordinator.config_entry.runtime_data.config
        self._filtration: Filtration = coordinator.config_entry.runtime_data.filtration

        # Convert pool_name to snake_case for consistency
        snake_pool_name = pool_name.lower().replace(" ", "_")
        self.entity_id = f"binary_sensor.iopool_{snake_pool_name}_{description.key}"

        # Create a unique DeviceInfo for each pool - must match the sensor platform
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, pool_id)},
            name=pool_name,
            manufacturer=MANUFACTURER,
            model="iopool ECO",
        )

    def _get_state(self) -> State | None:
        """Get the state of the binary sensor."""
        return self.hass.states.get(self.entity_id)

    def _get_pool(self) -> IopoolAPIResponsePool | None:
        """Get the pool data from coordinator."""
        return self.coordinator.get_pool_data(self._pool_id)

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added to Home Assistant."""
        await super().async_added_to_hass()
        # Restore state only for filtration sensor
        if self.entity_description.key == "filtration":
            last_state = await self.async_get_last_state()
            _LOGGER.debug("Restoring last state for %s: %s", self.entity_id, last_state)
            if last_state is not None and self._get_state() is None:
                # Restore the previous state
                if last_state.state == "on":
                    self.hass.states.async_set(
                        self.entity_id, "on", last_state.attributes
                    )
                elif last_state.state == "off":
                    self.hass.states.async_set(
                        self.entity_id, "off", last_state.attributes
                    )
            # Set up listener for switch state changes
            switch_entity = self._filtration.get_switch_entity()
            if switch_entity:
                _LOGGER.debug(
                    "Setting up state change listener for switch entity: %s",
                    switch_entity,
                )

                @callback
                def _handle_switch_state_change(event: Event) -> None:
                    """Handle switch state changes."""
                    new_state = event.data.get("new_state")
                    if not new_state:
                        return

                    _LOGGER.debug(
                        "Switch state changed to %s, updating filtration binary sensor",
                        new_state.state,
                    )

                    # Get current attributes to preserve them
                    current_state = self._get_state()
                    attributes = dict(current_state.attributes) if current_state else {}

                    # Update binary sensor state based on switch state
                    self.hass.states.async_set(
                        self.entity_id,
                        "on" if new_state.state == "on" else "off",
                        attributes,
                    )

                # Track state changes for the switch entity
                self.async_on_remove(
                    async_track_state_change_event(
                        self.hass, [switch_entity], _handle_switch_state_change
                    )
                )
            else:
                _LOGGER.warning(
                    "Configured switch entity not found for filtration, skipping state change listener"
                )

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        return self.entity_description.icon

    @property
    def is_on(self) -> bool | None:
        """Return true if action is required."""
        pool = self._get_pool()

        if not pool:
            return None

        match self.entity_description.key:
            case "action_required":
                # Check if the pool has any action required
                return pool.has_action_required
            case "filtration":
                # Check if filtration is currently running
                switch_entity = self._filtration.get_switch_entity()
                if switch_entity:
                    switch_state = self.hass.states.get(switch_entity)
                    if switch_state:
                        # The filtration state is directly linked to the switch state
                        return switch_state.state == "on"
                return False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.data:
            return False

        # Check if pool exists in the data
        return self._get_pool() is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        pool = self._get_pool()

        attributes = {}

        match self.entity_description.key:
            case "action_required":
                if pool and pool.latest_measure:
                    measured_at: datetime = pool.latest_measure.measured_at
                    if measured_at:
                        # Convert directly from UTC to local timezone
                        measured_at: datetime = dt_util.as_local(measured_at)

                    attributes.update(
                        {
                            ATTR_IS_VALID: pool.latest_measure.is_valid,
                            ATTR_MEASURE_MODE: pool.latest_measure.mode,
                            ATTR_MEASURED_AT: measured_at,
                        }
                    )
            case "filtration":
                filtration: Filtration = self._filtration
                pool_mode = filtration.get_filtration_pool_mode()

                # Retrieve the current state of the entity
                # This is necessary to keep the existing attributes if they are already set
                state = self._get_state()

                # Add Pool Mode to attributes
                attributes["filtration_mode"] = pool_mode

                # If pool_mode is Standard and summer filtration is enabled
                if (
                    filtration.configuration_filtration_enabled_summer
                    and pool_mode == "Standard"
                ):
                    # Add filtration duration to attributes
                    duration = filtration.get_summer_filtration_duration()
                    if duration is not None:
                        attributes["filtration_duration_minutes"] = duration
                    # Add filtration start time to attributes
                    slot1_start_time = filtration.get_summer_filtration_slot_start(1)
                    if slot1_start_time is not None:
                        attributes["slot1_start_time"] = dt_util.as_local(
                            slot1_start_time
                        ).isoformat()
                    # Add slot2 start time to attributes if slot2 is enabled (>0 duration)
                    if (
                        int(
                            self._config.options.filtration.get(
                                CONF_OPTIONS_FILTRATION_SUMMER, {}
                            )
                            .get(CONF_OPTIONS_FILTRATION_SLOT2, {})
                            .get(CONF_OPTIONS_FILTRATION_DURATION_PERCENT, 0)
                        )
                        > 0
                    ):
                        slot2_start_time = filtration.get_summer_filtration_slot_start(
                            2
                        )
                        if slot2_start_time is not None:
                            attributes["slot2_start_time"] = dt_util.as_local(
                                slot2_start_time
                            ).isoformat()
                    # Preserve existing attributes that we want to keep
                    preserved_attrs = [
                        "slot1_end_time",
                        "slot2_end_time",
                        "next_stop_time",
                        "active_slot",
                    ]
                    if state and state.attributes:
                        for attr in preserved_attrs:
                            if attr in state.attributes:
                                attributes[attr] = state.attributes[attr]

                # If pool_mode is Active-Winter and winter filtration is enabled
                if (
                    filtration.configuration_filtration_enabled_winter
                    and pool_mode == "Active-Winter"
                ):
                    # Get filtration informations
                    winter_filtration_start_time, winter_filtration_duration = (
                        filtration.get_winter_filtration_start_end()
                    )

                    winter_filtration_start_today = datetime.combine(
                        date.today(),
                        winter_filtration_start_time,
                    )
                    winter_filtration_end = (
                        winter_filtration_start_today + winter_filtration_duration
                    )
                    _LOGGER.debug(
                        "Winter filtration start: %s / End : %s",
                        winter_filtration_start_today,
                        winter_filtration_end,
                    )
                    # Add filtration duration to attributes
                    if winter_filtration_duration is not None:
                        attributes["filtration_duration_minutes"] = (
                            winter_filtration_duration.total_seconds() / 60
                        )
                    # Add winter filteration start and end to attributes
                    if winter_filtration_start_today is not None:
                        attributes["winter_filtration_start"] = dt_util.as_local(
                            winter_filtration_start_today
                        ).isoformat()
                    if winter_filtration_end is not None:
                        attributes["winter_filtration_end"] = dt_util.as_local(
                            winter_filtration_end
                        ).isoformat()
                if pool_mode == "Passive-Winter":
                    # If pool_mode is Passive-Winter and other mode attributes are set,
                    # we remove them to avoid confusion
                    if state and state.attributes:
                        attributes.update(state.attributes)
                    clean_attributes: list[str] = [
                        "filtration_duration_minutes",
                        "winter_filtration_start",
                        "winter_filtration_end",
                        "slot1_start_time",
                        "slot1_end_time",
                        "slot2_start_time",
                        "slot2_end_time",
                    ]
                    _LOGGER.debug("Attributes before cleaning: %s", attributes)
                    # Clean up attributes that are not relevant for Passive-Winter mode
                    for attr in clean_attributes:
                        attributes.pop(attr, None)
                    _LOGGER.debug("Attributes after cleaning: %s", attributes)

        return attributes
