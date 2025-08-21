"""Sensor platform for iopool integration."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .api_models import IopoolAPIResponsePool
from .const import (
    ATTR_IS_VALID,
    ATTR_MEASURE_MODE,
    ATTR_MEASURED_AT,
    CONF_OPTIONS_FILTRATION_SWITCH_ENTITY,
    CONF_POOL_ID,
    SENSOR_ELAPSED_FILTRATION,
    SENSOR_FILTRATION_RECOMMENDATION,
    SENSOR_IOPOOL_MODE,
    SENSOR_ORP,
    SENSOR_PH,
    SENSOR_TEMPERATURE,
)
from .coordinator import IopoolDataUpdateCoordinator
from .entity import IopoolEntity
from .models import IopoolConfigEntry

_LOGGER = logging.getLogger(__name__)

# Sensor definitions for each pool
POOL_SENSORS = [
    SensorEntityDescription(
        key=SENSOR_TEMPERATURE,
        translation_key=SENSOR_TEMPERATURE,
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key=SENSOR_PH,
        translation_key=SENSOR_PH,
        icon="mdi:alpha-p-box-outline",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key=SENSOR_ORP,
        translation_key=SENSOR_ORP,
        icon="mdi:alpha-o-box-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="mV",
    ),
    SensorEntityDescription(
        key=SENSOR_FILTRATION_RECOMMENDATION,
        translation_key=SENSOR_FILTRATION_RECOMMENDATION,
        icon="mdi:clock-time-two-outline",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SensorEntityDescription(
        key=SENSOR_IOPOOL_MODE,
        translation_key=SENSOR_IOPOOL_MODE,
        icon="mdi:auto-mode",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IopoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up iopool sensors based on a config entry."""
    coordinator: IopoolDataUpdateCoordinator = entry.runtime_data.coordinator
    pool_id: str = entry.data[CONF_POOL_ID]

    # Get pool data for the specific pool_id
    pool: IopoolAPIResponsePool = coordinator.get_pool_data(pool_id)
    if pool is None:
        _LOGGER.error("No pool found with ID: %s", pool_id)
        return

    entities = []

    # Create entities for the specific pool
    entities.extend(
        [
            IopoolSensor(
                coordinator,
                description,
                entry.entry_id,
                pool.id,
                pool.title,
            )
            for description in POOL_SENSORS
        ]
    )

    async_add_entities(entities)

    # Setup history stats sensor if switch entity is configured and filtration is enabled
    # This is a custom sensor that tracks the elapsed filtration duration
    # and is not part of the standard iopool sensors
    # It requires a switch entity to be configured in the options
    # The switch entity is used to track the state of the filtration system
    switch_entity: str | None = entry.runtime_data.config.options.filtration.get(
        CONF_OPTIONS_FILTRATION_SWITCH_ENTITY, None
    )
    _LOGGER.debug(
        "History Sensor - Switch entity: %s",
        switch_entity,
    )
    if switch_entity:
        from homeassistant.components.history_stats.const import CONF_TYPE_TIME
        from homeassistant.components.history_stats.coordinator import (
            HistoryStatsUpdateCoordinator,
        )
        from homeassistant.components.history_stats.data import HistoryStats
        from homeassistant.components.history_stats.sensor import HistoryStatsSensor
        from homeassistant.helpers.template import Template

        start_template = Template(
            "{{ now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() }}",
            hass,
        )
        end_template = Template("{{ now().isoformat() }}", hass)

        # Create a friendly name for the sensor based on the pool title and language
        FRIENDLY_NAMES = {
            "en": "{pool} Elapsed Filtration Duration Today",
            "fr": "{pool} Durée de filtration écoulée aujourd'hui",
            # Add more languages as needed
        }
        ha_language = hass.config.language
        template = FRIENDLY_NAMES.get(
            ha_language, FRIENDLY_NAMES["en"]
        )  # Fallback to English if not found
        friendly_name = template.format(pool=pool.title)

        # Create the history stats object
        history_stats = HistoryStats(
            hass,
            entity_id=switch_entity,
            entity_states=["on"],
            start=start_template,
            end=end_template,
            duration=None,
        )
        # Create the coordinator
        coordinator = HistoryStatsUpdateCoordinator(
            hass,
            history_stats,
            entry,
            friendly_name,
        )
        try:
            # Ensure the coordinator is initialized
            await coordinator.async_config_entry_first_refresh()
            # Create the sensor with the coordinator
            history_stats_entity = HistoryStatsSensor(
                hass=hass,
                coordinator=coordinator,
                sensor_type=CONF_TYPE_TIME,
                name=friendly_name,
                unique_id=f"{entry.entry_id}_{pool_id}_{SENSOR_ELAPSED_FILTRATION}",
                source_entity_id=f"sensor.iopool_{pool.title.lower().replace(' ', '_')}_{SENSOR_TEMPERATURE}",
            )
            history_stats_entity.entity_id = f"sensor.iopool_{pool.title.lower().replace(' ', '_')}_{SENSOR_ELAPSED_FILTRATION}"
            # Add the entity to Home Assistant
            async_add_entities([history_stats_entity])
        except (ValueError, KeyError, TypeError) as err:
            _LOGGER.error("Failed to set up history_stats sensor: %s", err)


class IopoolSensor(IopoolEntity, SensorEntity):
    """Representation of an iopool sensor."""

    def __init__(
        self,
        coordinator: IopoolDataUpdateCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
        pool_id: str,
        pool_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry_id, pool_id, pool_name)
        self.entity_description = description

        # Set unique_id for state persistence
        self._attr_unique_id = f"{config_entry_id}_{pool_id}_{description.key}"

        # Set custom entity_id with iopool_ prefix
        snake_pool_name = pool_name.lower().replace(" ", "_")
        self.entity_id = f"sensor.iopool_{snake_pool_name}_{description.key}"

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        return self.entity_description.icon

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        pool = self._get_pool()

        if not pool:
            return None

        # Get the value based on the sensor type
        key = self.entity_description.key
        value = None

        match key:  # Using string to avoid Ruff warnings
            case "temperature":
                value = pool.latest_measure.temperature if pool.latest_measure else None
            case "ph":
                value = pool.latest_measure.ph if pool.latest_measure else None
            case "orp":
                value = pool.latest_measure.orp if pool.latest_measure else None
            case "filtration_recommendation":
                # Convert hours to minutes
                if pool.advice and pool.advice.filtration_duration is not None:
                    value = pool.advice.filtration_duration * 60
            case "iopool_mode":
                value = pool.mode if pool.mode else None
            case _:
                value = None

        return value

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.data:
            return False

        # Find the corresponding pool in the data
        pool = self._get_pool()

        if not pool:
            return False

        if self.entity_description.key in [SENSOR_TEMPERATURE, SENSOR_PH, SENSOR_ORP]:
            return bool(pool.latest_measure)

        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        pool = self._get_pool()

        attributes = {}

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

        # If the entity description suggests a display precision, expose it
        # as an attribute so frontends or automations can use it.
        precision = getattr(
            self.entity_description, "suggested_display_precision", None
        )
        if precision is not None:
            # Ensure we return a plain int (or similar) in attributes
            attributes["display_precision"] = int(precision)

        return attributes

    def _get_pool(self) -> IopoolAPIResponsePool | None:
        """Get the pool data from coordinator."""
        return self.coordinator.get_pool_data(self._pool_id)
