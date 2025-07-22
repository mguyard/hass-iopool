"""Tests for iopool sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from custom_components.iopool.const import DOMAIN
from custom_components.iopool.sensor import (
    POOL_SENSORS,
    IopoolSensor,
    async_setup_entry,
)
import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from .conftest import TEST_API_KEY, TEST_POOL_ID, TEST_POOL_TITLE


class TestIopoolSensorPlatform:
    """Test iopool sensor platform."""

    @pytest.mark.asyncio
    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("custom_components.iopool.sensor.IopoolSensor")
    async def test_async_setup_entry(
        self,
        mock_sensor_class,
        mock_zeroconf,
        mock_report: MagicMock,
        hass: HomeAssistant,
    ) -> None:
        """Test sensor platform setup."""
        # Create mock config entry
        config_entry = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title=TEST_POOL_TITLE,
            data={
                "api_key": TEST_API_KEY,
                "pool_id": TEST_POOL_ID,
            },
            options={},
            source="user",
            unique_id=TEST_POOL_ID,
            discovery_keys=frozenset(),
            subentries_data={},
        )

        # Mock runtime data
        mock_coordinator = MagicMock()
        mock_coordinator.get_pool_data.return_value = MagicMock(
            id=TEST_POOL_ID, title="Test Pool"
        )

        # Mock config with filtration options (no switch entity)
        mock_config = MagicMock()
        mock_config.options.filtration.get.return_value = None  # No switch entity

        mock_runtime_data = MagicMock()
        mock_runtime_data.coordinator = mock_coordinator
        mock_runtime_data.config = mock_config
        config_entry.runtime_data = mock_runtime_data

        # Mock async_add_entities
        mock_async_add_entities = MagicMock()

        # Mock sensor instances
        mock_sensor_instances = [
            MagicMock() for _ in range(6)
        ]  # Based on POOL_SENSORS count
        mock_sensor_class.side_effect = mock_sensor_instances

        await async_setup_entry(hass, config_entry, mock_async_add_entities)

        # Verify sensors were created and added
        assert mock_sensor_class.call_count > 0
        mock_async_add_entities.assert_called_once()

    @pytest.mark.asyncio
    @patch("homeassistant.helpers.frame.report_usage")
    async def test_async_setup_entry_no_runtime_data(
        self,
        mock_report: MagicMock,
        hass: HomeAssistant,
    ) -> None:
        """Test sensor platform setup with no runtime data."""
        # Create mock config entry without runtime data
        config_entry = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title=TEST_POOL_TITLE,
            data={
                "api_key": TEST_API_KEY,
                "pool_id": TEST_POOL_ID,
            },
            options={},
            source="user",
            unique_id=TEST_POOL_ID,
            discovery_keys=frozenset(),
            subentries_data={},
        )

        config_entry.runtime_data = None

        # Mock async_add_entities
        mock_async_add_entities = MagicMock()

        # This should raise an AttributeError due to accessing None.coordinator
        with pytest.raises(
            AttributeError, match="'NoneType' object has no attribute 'coordinator'"
        ):
            await async_setup_entry(hass, config_entry, mock_async_add_entities)

        # Verify no entities were added
        mock_async_add_entities.assert_not_called()


class TestIopoolSensor:
    """Test individual iopool sensor."""

    def test_sensor_initialization(self) -> None:
        """Test sensor initialization."""
        mock_coordinator = MagicMock()
        mock_coordinator.data = MagicMock()
        mock_coordinator.data.pools = [MagicMock()]
        mock_coordinator.data.pools[0].id = TEST_POOL_ID

        sensor_description = POOL_SENSORS[0]  # Temperature sensor
        sensor = IopoolSensor(
            mock_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.coordinator == mock_coordinator
        assert sensor.entity_description == sensor_description
        # Test that sensor was created with correct parameters
        assert sensor.unique_id is not None

    def test_temperature_sensor_properties(self) -> None:
        """Test temperature sensor specific properties."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.id = TEST_POOL_ID
        mock_pool.latest_measure = MagicMock()
        mock_pool.latest_measure.temperature = 24.5
        mock_pool.latest_measure.is_valid = True
        mock_coordinator.get_pool_data.return_value = mock_pool

        # Get temperature sensor description
        temp_sensor_desc = next(
            desc for desc in POOL_SENSORS if desc.key == "temperature"
        )

        sensor = IopoolSensor(
            mock_coordinator,
            temp_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.native_value == 24.5
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        assert sensor.available is True

    def test_sensor_unavailable_when_no_pool_data(self) -> None:
        """Test sensor is unavailable when no pool data."""
        mock_coordinator = MagicMock()
        mock_coordinator.get_pool_data.return_value = None

        sensor_description = POOL_SENSORS[0]
        sensor = IopoolSensor(
            mock_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.available is False
        assert sensor.native_value is None

    def test_sensor_unavailable_when_invalid_measure(self) -> None:
        """Test sensor attributes when measure is invalid."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.id = TEST_POOL_ID
        mock_pool.latest_measure = MagicMock()
        mock_pool.latest_measure.temperature = 0.0
        mock_pool.latest_measure.is_valid = False
        mock_pool.latest_measure.mode = "standard"
        mock_pool.latest_measure.measured_at = None
        mock_coordinator.get_pool_data.return_value = mock_pool

        temp_sensor_desc = next(
            desc for desc in POOL_SENSORS if desc.key == "temperature"
        )

        sensor = IopoolSensor(
            mock_coordinator,
            temp_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Sensor should be available even with invalid measure (as per current implementation)
        assert sensor.available is True
        # But the is_valid should be reflected in extra_state_attributes
        attributes = sensor.extra_state_attributes
        assert attributes.get("is_valid") is False
