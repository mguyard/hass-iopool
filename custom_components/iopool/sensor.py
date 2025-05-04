"""Sensor platform for iopool integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_IS_VALID,
    ATTR_MEASURE_MODE,
    ATTR_MEASURED_AT,
    CONF_TEMPERATURE_UNIT,
    DEFAULT_TEMPERATURE_UNIT,
    DOMAIN,
    MANUFACTURER,
    SENSOR_FILTRATION_DURATION,
    SENSOR_MODE,  # Ajoutez cette constante dans const.py
    SENSOR_ORP,
    SENSOR_PH,
    SENSOR_TEMPERATURE,
)
from .coordinator import IopoolDataUpdateCoordinator
from .models import iopoolPoolData

_LOGGER = logging.getLogger(__name__)

# Sensor definitions for each pool (remove unit_of_measurement from temperature sensor)
POOL_SENSORS = [
    SensorEntityDescription(
        key=SENSOR_TEMPERATURE,
        name="Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key=SENSOR_PH,
        name="pH",
        icon="mdi:alpha-p-box-outline",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key=SENSOR_ORP,
        name="ORP",
        icon="mdi:alpha-o-box-outline",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="mV",
    ),
    SensorEntityDescription(
        key=SENSOR_FILTRATION_DURATION,
        name="Filtration Duration",
        icon="mdi:clock-time-two-outline",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SensorEntityDescription(
        key=SENSOR_MODE,
        name="Mode",
        icon="mdi:auto-mode",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up iopool sensors based on a config entry."""
    coordinator: IopoolDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get configured temperature unit
    temperature_unit = entry.options.get(
        CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT
    )

    entities = []

    # Create entities for each detected pool
    for pool in coordinator.data.pools:
        # Create entities for each sensor type
        for description in POOL_SENSORS:
            # Set the temperature unit for temperature sensors
            if description.key == SENSOR_TEMPERATURE:
                entities.append(
                    IopoolTemperatureSensor(
                        coordinator,
                        description,
                        entry.entry_id,
                        pool.id,
                        pool.title,
                        temperature_unit,
                    )
                )
            else:
                entities.append(
                    IopoolSensor(
                        coordinator,
                        description,
                        entry.entry_id,
                        pool.id,
                        pool.title,
                    )
                )

    async_add_entities(entities)


class IopoolSensor(CoordinatorEntity, SensorEntity):
    """Representation of an iopool sensor."""

    coordinator: IopoolDataUpdateCoordinator

    def __init__(
        self,
        coordinator: IopoolDataUpdateCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
        pool_id: str,
        pool_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._pool_id = pool_id

        # Set unique_id for state persistence
        self._attr_unique_id = f"{config_entry_id}_{pool_id}_{description.key}"

        # Set friendly name - will be updated dynamically via name property
        self._pool_name = pool_name  # Store initial name for fallback only

        # Set custom entity_id with iopool_ prefix
        snake_pool_name = pool_name.lower().replace(" ", "_")
        self.entity_id = f"sensor.iopool_{snake_pool_name}_{description.key}"

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        # Get current pool data to ensure name is up-to-date
        pool = self._get_pool()
        if pool:
            return f"{pool.title} {self.entity_description.name}"
        # Fallback to initial name if pool data not available
        return f"{self._pool_name} {self.entity_description.name}"

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        return self.entity_description.icon

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        # Get current pool data to ensure all info is up-to-date
        pool = self._get_pool()

        # If pool not found, return minimal device info with just the ID
        if not pool or not pool.latest_measure:
            return DeviceInfo(
                identifiers={(DOMAIN, self._pool_id)},
                name=self._pool_name,  # Use stored name as fallback
                manufacturer=MANUFACTURER,
                model="iopool ECO",
            )

        # Return complete device info with up-to-date data
        return DeviceInfo(
            identifiers={(DOMAIN, self._pool_id)},
            name=pool.title,  # Use current name from API
            manufacturer=MANUFACTURER,
            model="iopool ECO",
            hw_version=pool.latest_measure.eco_id,  # Add eco_id as hardware version
        )

    def _get_pool(self) -> iopoolPoolData | None:
        """Get the pool data from coordinator."""
        if not self.coordinator.data:
            return None

        return next(
            (pool for pool in self.coordinator.data.pools if pool.id == self._pool_id),
            None,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        pool = self._get_pool()

        if not pool:
            return None

        # Get the value based on the sensor type
        key = self.entity_description.key
        match key:  # Using variable to avoid Ruff warnings
            case "temperature":
                return pool.latest_measure.temperature if pool.latest_measure else None
            case "ph":
                return pool.latest_measure.ph if pool.latest_measure else None
            case "orp":
                return pool.latest_measure.orp if pool.latest_measure else None
            case "filtration_duration":
                # Convert hours to minutes
                if pool.advice and pool.advice.filtration_duration is not None:
                    return pool.advice.filtration_duration * 60
                return None
            case "mode":
                return pool.mode if pool.mode else None
            case _:
                return None

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
            attributes.update(
                {
                    ATTR_IS_VALID: pool.latest_measure.is_valid,
                    ATTR_MEASURE_MODE: pool.latest_measure.mode,
                    ATTR_MEASURED_AT: pool.latest_measure.measured_at,
                }
            )

        return attributes


class IopoolTemperatureSensor(IopoolSensor):
    """Representation of an iopool temperature sensor with configurable unit."""

    def __init__(
        self,
        coordinator: IopoolDataUpdateCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
        pool_id: str,
        pool_name: str,
        temperature_unit: str,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, description, config_entry_id, pool_id, pool_name)
        self._attr_native_unit_of_measurement = temperature_unit

    @property
    def native_value(self) -> float | None:
        """Return the temperature in the configured unit."""
        pool = self._get_pool()

        if not pool or not pool.latest_measure:
            return None

        # Get temperature in Celsius from the API
        temp_celsius = pool.latest_measure.temperature

        # Convert to Fahrenheit if needed
        if self.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT:
            return celsius_to_fahrenheit(temp_celsius)

        return temp_celsius


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32
