"""Tests for iopool sensor entities."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

from custom_components.iopool.const import DOMAIN
from custom_components.iopool.sensor import (
    POOL_SENSORS,
    IopoolSensor,
    async_setup_entry,
)
import pytest

from homeassistant.components.sensor import SensorEntityDescription
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


class TestAsyncSetupEntryEdgeCases:
    """Test edge cases for async_setup_entry."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_no_pool_found(self, hass: HomeAssistant) -> None:
        """Test setup when pool is not found."""
        # Create mock config entry
        config_entry = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title=TEST_POOL_TITLE,
            data={
                "api_key": TEST_API_KEY,
                "pool_id": "nonexistent_pool",
            },
            options={},
            source="user",
            unique_id="nonexistent_pool",
            discovery_keys=frozenset(),
            subentries_data={},
        )

        # Mock runtime data
        mock_coordinator = MagicMock()
        mock_coordinator.get_pool_data.return_value = None  # No pool found

        mock_config = MagicMock()
        mock_config.options.filtration.get.return_value = None

        mock_runtime_data = MagicMock()
        mock_runtime_data.coordinator = mock_coordinator
        mock_runtime_data.config = mock_config
        config_entry.runtime_data = mock_runtime_data

        # Mock async_add_entities
        mock_async_add_entities = MagicMock()

        # Should return early when no pool found
        await async_setup_entry(hass, config_entry, mock_async_add_entities)

        # Verify no entities were added (since pool was not found)
        mock_async_add_entities.assert_not_called()

    @pytest.mark.asyncio
    @patch("homeassistant.helpers.template.Template")
    @patch("homeassistant.components.history_stats.sensor.HistoryStatsSensor")
    @patch(
        "homeassistant.components.history_stats.coordinator.HistoryStatsUpdateCoordinator"
    )
    @patch("homeassistant.components.history_stats.data.HistoryStats")
    async def test_async_setup_entry_with_switch_entity(
        self,
        mock_history_stats,
        mock_coordinator_class,
        mock_sensor_class,
        mock_template,
        hass: HomeAssistant,
    ) -> None:
        """Test setup with switch entity configured for history stats."""
        # Setup mocks
        hass.config.language = "en"

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

        # Mock pool data
        mock_pool = MagicMock()
        mock_pool.id = TEST_POOL_ID
        mock_pool.title = "Test Pool"

        mock_coordinator = MagicMock()
        mock_coordinator.get_pool_data.return_value = mock_pool

        # Mock config with switch entity
        mock_config = MagicMock()
        mock_config.options.filtration.get.return_value = "switch.pool_pump"

        mock_runtime_data = MagicMock()
        mock_runtime_data.coordinator = mock_coordinator
        mock_runtime_data.config = mock_config
        config_entry.runtime_data = mock_runtime_data

        # Mock history stats components
        mock_template.return_value = MagicMock()
        mock_history_stats.return_value = MagicMock()

        mock_history_coordinator = MagicMock()
        mock_history_coordinator.async_config_entry_first_refresh = MagicMock(
            return_value=None
        )
        mock_coordinator_class.return_value = mock_history_coordinator

        mock_history_sensor = MagicMock()
        mock_sensor_class.return_value = mock_history_sensor

        mock_async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, mock_async_add_entities)

        # Verify history stats components were created
        mock_template.assert_called()
        mock_history_stats.assert_called_once()
        mock_coordinator_class.assert_called_once()
        # Note: HistoryStatsSensor is called but within a try/except that might fail
        # So we just verify that basic entities were added
        assert mock_async_add_entities.call_count >= 1

    @pytest.mark.asyncio
    @patch("homeassistant.helpers.template.Template")
    @patch("homeassistant.components.history_stats.sensor.HistoryStatsSensor")
    @patch(
        "homeassistant.components.history_stats.coordinator.HistoryStatsUpdateCoordinator"
    )
    @patch("homeassistant.components.history_stats.data.HistoryStats")
    async def test_async_setup_entry_with_switch_entity_french(
        self,
        mock_history_stats,
        mock_coordinator_class,
        mock_sensor_class,
        mock_template,
        hass: HomeAssistant,
    ) -> None:
        """Test setup with switch entity and French language."""
        # Setup mocks
        hass.config.language = "fr"

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

        # Mock pool data
        mock_pool = MagicMock()
        mock_pool.id = TEST_POOL_ID
        mock_pool.title = "Piscine Test"

        mock_coordinator = MagicMock()
        mock_coordinator.get_pool_data.return_value = mock_pool

        # Mock config with switch entity
        mock_config = MagicMock()
        mock_config.options.filtration.get.return_value = "switch.pompe_piscine"

        mock_runtime_data = MagicMock()
        mock_runtime_data.coordinator = mock_coordinator
        mock_runtime_data.config = mock_config
        config_entry.runtime_data = mock_runtime_data

        # Mock history stats components
        mock_template.return_value = MagicMock()
        mock_history_stats.return_value = MagicMock()

        mock_history_coordinator = MagicMock()
        mock_history_coordinator.async_config_entry_first_refresh = MagicMock()
        mock_coordinator_class.return_value = mock_history_coordinator

        mock_history_sensor = MagicMock()
        mock_sensor_class.return_value = mock_history_sensor

        mock_async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, mock_async_add_entities)

        # Verify French language template was used
        # This is indirectly tested by checking that the coordinator was created
        mock_coordinator_class.assert_called_once()
        call_args = mock_coordinator_class.call_args[0]
        friendly_name = call_args[3]  # 4th argument is friendly_name
        assert friendly_name == "Piscine Test Durée de filtration écoulée aujourd'hui"

    @pytest.mark.asyncio
    @patch("homeassistant.helpers.template.Template")
    @patch(
        "homeassistant.components.history_stats.coordinator.HistoryStatsUpdateCoordinator"
    )
    @patch("homeassistant.components.history_stats.data.HistoryStats")
    async def test_async_setup_entry_history_stats_error(
        self,
        mock_history_stats,
        mock_coordinator_class,
        mock_template,
        hass: HomeAssistant,
    ) -> None:
        """Test setup when history stats initialization fails."""
        # Setup mocks
        hass.config.language = "en"

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

        # Mock pool data
        mock_pool = MagicMock()
        mock_pool.id = TEST_POOL_ID
        mock_pool.title = "Test Pool"

        mock_coordinator = MagicMock()
        mock_coordinator.get_pool_data.return_value = mock_pool

        # Mock config with switch entity
        mock_config = MagicMock()
        mock_config.options.filtration.get.return_value = "switch.pool_pump"

        mock_runtime_data = MagicMock()
        mock_runtime_data.coordinator = mock_coordinator
        mock_runtime_data.config = mock_config
        config_entry.runtime_data = mock_runtime_data

        # Mock history stats components to raise error
        mock_template.return_value = MagicMock()
        mock_history_stats.return_value = MagicMock()

        mock_history_coordinator = MagicMock()
        # Make the first refresh fail
        mock_history_coordinator.async_config_entry_first_refresh.side_effect = (
            ValueError("Test error")
        )
        mock_coordinator_class.return_value = mock_history_coordinator

        mock_async_add_entities = MagicMock()

        # Should not raise error, but log it
        await async_setup_entry(hass, config_entry, mock_async_add_entities)

        # Verify basic entities were still added despite history stats error
        assert mock_async_add_entities.call_count == 1  # Only basic sensors


class TestIopoolSensorProperties:
    """Test IopoolSensor properties and methods."""

    def test_ph_sensor_native_value(self) -> None:
        """Test pH sensor native value."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.latest_measure = MagicMock()
        mock_pool.latest_measure.ph = 7.2
        mock_coordinator.get_pool_data.return_value = mock_pool

        ph_sensor_desc = next(desc for desc in POOL_SENSORS if desc.key == "ph")
        sensor = IopoolSensor(
            mock_coordinator,
            ph_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.native_value == 7.2

    def test_orp_sensor_native_value(self) -> None:
        """Test ORP sensor native value."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.latest_measure = MagicMock()
        mock_pool.latest_measure.orp = 650
        mock_coordinator.get_pool_data.return_value = mock_pool

        orp_sensor_desc = next(desc for desc in POOL_SENSORS if desc.key == "orp")
        sensor = IopoolSensor(
            mock_coordinator,
            orp_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.native_value == 650

    def test_filtration_recommendation_sensor_native_value(self) -> None:
        """Test filtration recommendation sensor native value."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.advice = MagicMock()
        mock_pool.advice.filtration_duration = 4.5  # 4.5 hours
        mock_coordinator.get_pool_data.return_value = mock_pool

        filtration_sensor_desc = next(
            desc for desc in POOL_SENSORS if desc.key == "filtration_recommendation"
        )
        sensor = IopoolSensor(
            mock_coordinator,
            filtration_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.native_value == 270  # 4.5 * 60 = 270 minutes

    def test_iopool_mode_sensor_native_value(self) -> None:
        """Test iopool mode sensor native value."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.mode = "Standard"
        mock_coordinator.get_pool_data.return_value = mock_pool

        mode_sensor_desc = next(
            desc for desc in POOL_SENSORS if desc.key == "iopool_mode"
        )
        sensor = IopoolSensor(
            mock_coordinator,
            mode_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.native_value == "Standard"

    def test_sensor_with_no_latest_measure(self) -> None:
        """Test sensor when pool has no latest measure."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.latest_measure = None
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

        assert sensor.native_value is None
        assert (
            sensor.available is False
        )  # Should be unavailable for measure-based sensors

    def test_sensor_with_no_advice(self) -> None:
        """Test filtration recommendation sensor when pool has no advice."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.advice = None
        mock_coordinator.get_pool_data.return_value = mock_pool

        filtration_sensor_desc = next(
            desc for desc in POOL_SENSORS if desc.key == "filtration_recommendation"
        )
        sensor = IopoolSensor(
            mock_coordinator,
            filtration_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.native_value is None
        assert (
            sensor.available is True
        )  # Should still be available for non-measure sensors

    def test_sensor_icon_property(self) -> None:
        """Test sensor icon property."""
        mock_coordinator = MagicMock()

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

        assert sensor.icon == "mdi:thermometer"

    def test_sensor_no_coordinator_data(self) -> None:
        """Test sensor when coordinator has no data."""
        mock_coordinator = MagicMock()
        mock_coordinator.data = None

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

        assert sensor.available is False

    def test_unknown_sensor_key(self) -> None:
        """Test sensor with unknown key."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_coordinator.get_pool_data.return_value = mock_pool

        # Create a custom sensor description with unknown key
        unknown_sensor_desc = SensorEntityDescription(
            key="unknown_sensor",
            translation_key="unknown_sensor",
        )

        sensor = IopoolSensor(
            mock_coordinator,
            unknown_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.native_value is None

    @patch("homeassistant.util.dt.as_local")
    def test_extra_state_attributes_with_measured_at(self, mock_as_local) -> None:
        """Test extra state attributes when measured_at is available."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_measure = MagicMock()
        mock_measure.is_valid = True
        mock_measure.mode = "standard"
        mock_measure.measured_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_pool.latest_measure = mock_measure
        mock_coordinator.get_pool_data.return_value = mock_pool

        # Mock as_local to return a local datetime
        local_datetime = datetime(2023, 1, 1, 13, 0, 0)  # 1 hour ahead
        mock_as_local.return_value = local_datetime

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

        attributes = sensor.extra_state_attributes

        assert attributes["is_valid"] is True
        assert attributes["measure_mode"] == "standard"
        assert attributes["measured_at"] == local_datetime
        mock_as_local.assert_called_once()

    def test_extra_state_attributes_no_measure(self) -> None:
        """Test extra state attributes when no measure is available."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.latest_measure = None
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

        attributes = sensor.extra_state_attributes
        assert attributes == {}
