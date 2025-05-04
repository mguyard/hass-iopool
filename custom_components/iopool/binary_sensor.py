"""Binary sensor platform for iopool integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_IS_VALID,
    ATTR_MEASURE_MODE,
    ATTR_MEASURED_AT,
    DOMAIN,
    MANUFACTURER,
    SENSOR_ACTION_REQUIRED,
)
from .coordinator import IopoolDataUpdateCoordinator
from .models import iopoolPoolData

_LOGGER = logging.getLogger(__name__)

# Binary sensor definition
ACTION_REQUIRED_BINARY_SENSOR = BinarySensorEntityDescription(
    key=SENSOR_ACTION_REQUIRED,
    name="Action Required",
    icon="mdi:gesture-tap-button",
    device_class=BinarySensorDeviceClass.PROBLEM,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up iopool binary sensors based on a config entry."""
    coordinator: IopoolDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create entities for each detected pool
    entities = [
        IopoolBinarySensor(
            coordinator,
            ACTION_REQUIRED_BINARY_SENSOR,
            entry.entry_id,
            pool.id,
            pool.title,
        )
        for pool in coordinator.data.pools
    ]

    async_add_entities(entities)


class IopoolBinarySensor(CoordinatorEntity, BinarySensorEntity):
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
        self._attr_name = f"{pool_name} {description.name}"

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

    def _get_pool(self) -> iopoolPoolData | None:
        """Get the pool data from coordinator."""
        if not self.coordinator.data:
            return None

        return next(
            (pool for pool in self.coordinator.data.pools if pool.id == self._pool_id),
            None,
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

        return pool.has_action_required

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

        if pool and pool.latest_measure:
            attributes.update(
                {
                    ATTR_IS_VALID: pool.latest_measure.is_valid,
                    ATTR_MEASURE_MODE: pool.latest_measure.mode,
                    ATTR_MEASURED_AT: pool.latest_measure.measured_at,
                }
            )

        return attributes
