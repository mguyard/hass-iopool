"""Tests for iopool sensor entities."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.iopool.const import DOMAIN, SENSOR_ELAPSED_FILTRATION
from custom_components.iopool.sensor import (
    POOL_SENSORS,
    IopoolElapsedFiltrationSensor,
    IopoolSensor,
    async_setup_entry,
)
import pytest

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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

    @pytest.mark.parametrize(
        ("pool_name", "expected_id_fragment"),
        [
            ("My Pool", "my_pool"),
            ("Piscine été", "piscine_ete"),
            ("aquarium à  pikatchu", "aquarium_a_pikatchu"),
            ("Pool-Name", "pool_name"),
            ("  Leading Spaces  ", "leading_spaces"),
        ],
    )
    def test_sensor_entity_id_slugified(
        self, pool_name: str, expected_id_fragment: str
    ) -> None:
        """Test that sensor entity_id is properly slugified from the pool name."""
        mock_coordinator = MagicMock()
        sensor_description = POOL_SENSORS[0]  # Temperature sensor
        sensor = IopoolSensor(
            mock_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            pool_name,
        )
        expected_entity_id = (
            f"sensor.iopool_{expected_id_fragment}_{sensor_description.key}"
        )
        assert sensor.entity_id == expected_entity_id

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
    @patch(
        "homeassistant.components.history_stats.coordinator.HistoryStatsUpdateCoordinator"
    )
    @patch("homeassistant.components.history_stats.data.HistoryStats")
    async def test_async_setup_entry_with_switch_entity(
        self,
        mock_history_stats,
        mock_coordinator_class,
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
        mock_history_coordinator.async_config_entry_first_refresh = AsyncMock(
            return_value=None
        )
        mock_coordinator_class.return_value = mock_history_coordinator

        mock_async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, mock_async_add_entities)

        # Verify history stats components were created
        mock_template.assert_called()
        mock_history_stats.assert_called_once()
        mock_coordinator_class.assert_called_once()
        # Verify HistoryStats was called with min_state_duration=timedelta(0) (required since HA 2026.4)
        from datetime import timedelta

        hs_call_kwargs = mock_history_stats.call_args[1]
        assert hs_call_kwargs.get("min_state_duration") == timedelta(0)
        assert mock_async_add_entities.call_count >= 1

    @pytest.mark.asyncio
    @patch("homeassistant.helpers.template.Template")
    @patch(
        "homeassistant.components.history_stats.coordinator.HistoryStatsUpdateCoordinator"
    )
    @patch("homeassistant.components.history_stats.data.HistoryStats")
    async def test_async_setup_entry_elapsed_filtration_sensor_identity(
        self,
        mock_history_stats,
        mock_coordinator_class,
        mock_template,
        hass: HomeAssistant,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Pin down every attribute an existing install depends on.

        This sensor exists on every install that has a filtration switch
        configured, so these values are a migration contract, not style:

        - `unique_id` and `entity_id` identify the entity in the registry.
          Change either and users silently lose the entity's recorded history.
        - unit, `state_class` and `device_class` must stay stable or the
          recorder's long-term statistics break.
        - `has_entity_name` is False because the name is a full sentence built
          from the pool title, not a suffix to the device name. Flipping it
          would rename the entity for everyone.

        The sensor is built for real (not mocked): a mocked class accepts
        anything and would let all of the above drift unnoticed.
        """
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

        mock_pool = MagicMock()
        mock_pool.id = TEST_POOL_ID
        mock_pool.title = "Test Pool"

        mock_coordinator = MagicMock()
        mock_coordinator.get_pool_data.return_value = mock_pool

        mock_config = MagicMock()
        mock_config.options.filtration.get.return_value = "switch.pool_pump"

        mock_runtime_data = MagicMock()
        mock_runtime_data.coordinator = mock_coordinator
        mock_runtime_data.config = mock_config
        config_entry.runtime_data = mock_runtime_data

        mock_template.return_value = MagicMock()

        mock_history_coordinator = MagicMock()
        mock_history_coordinator.async_config_entry_first_refresh = AsyncMock(
            return_value=None
        )
        mock_coordinator_class.return_value = mock_history_coordinator

        mock_async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, mock_async_add_entities)

        assert "Failed to set up history_stats sensor" not in caplog.text

        # First call adds POOL_SENSORS; second call (only reached if the sensor
        # was constructed without raising) adds the elapsed filtration entity.
        assert mock_async_add_entities.call_count == 2
        added_entities = mock_async_add_entities.call_args_list[1][0][0]
        assert len(added_entities) == 1
        sensor = added_entities[0]

        assert isinstance(sensor, IopoolElapsedFiltrationSensor)

        # Registry identity
        assert (
            sensor.unique_id
            == f"{config_entry.entry_id}_{TEST_POOL_ID}_{SENSOR_ELAPSED_FILTRATION}"
        )
        assert sensor.entity_id == (
            f"sensor.iopool_test_pool_{SENSOR_ELAPSED_FILTRATION}"
        )

        # Recorder / statistics contract
        assert sensor.native_unit_of_measurement == UnitOfTime.HOURS
        assert sensor.state_class == SensorStateClass.MEASUREMENT
        assert sensor.device_class == SensorDeviceClass.DURATION

        # Displayed name
        assert sensor.has_entity_name is False
        assert sensor.name == "Test Pool Elapsed Filtration Duration Today"

        # Device grouping is declared, not resolved at construction time, so it
        # cannot race the creation of the pool device on a first install.
        assert sensor.device_info["identifiers"] == {(DOMAIN, TEST_POOL_ID)}

    @pytest.mark.asyncio
    @patch("homeassistant.helpers.template.Template")
    @patch(
        "homeassistant.components.history_stats.coordinator.HistoryStatsUpdateCoordinator"
    )
    @patch("homeassistant.components.history_stats.data.HistoryStats")
    async def test_async_setup_entry_with_switch_entity_french(
        self,
        mock_history_stats,
        mock_coordinator_class,
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
        mock_history_coordinator.async_config_entry_first_refresh = AsyncMock(
            return_value=None
        )
        mock_coordinator_class.return_value = mock_history_coordinator

        mock_async_add_entities = MagicMock()

        await async_setup_entry(hass, config_entry, mock_async_add_entities)

        # Verify French language template was used
        mock_coordinator_class.assert_called_once()
        call_args = mock_coordinator_class.call_args[0]
        friendly_name = call_args[3]  # 4th argument is friendly_name
        assert friendly_name == "Piscine Test Durée de filtration écoulée aujourd'hui"
        # The same name must reach the entity itself, not just the coordinator
        sensor = mock_async_add_entities.call_args_list[1][0][0][0]
        assert sensor.name == friendly_name
        # Verify HistoryStats was called with min_state_duration=timedelta(0) (required since HA 2026.4)
        from datetime import timedelta

        hs_call_kwargs = mock_history_stats.call_args[1]
        assert hs_call_kwargs.get("min_state_duration") == timedelta(0)
        assert mock_async_add_entities.call_count >= 1

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
        assert (
            attributes["display_precision"] == 2
        )  # Temperature sensor has suggested_display_precision=2
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
        # Should still include display_precision even without measure data
        assert attributes == {"display_precision": 2}

    def test_extra_state_attributes_display_precision(self) -> None:
        """Test that display_precision is included when suggested_display_precision is set."""
        mock_coordinator = MagicMock()
        mock_pool = MagicMock()
        mock_pool.latest_measure = None
        mock_coordinator.get_pool_data.return_value = mock_pool

        # Test with temperature sensor (has suggested_display_precision=2)
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
        assert "display_precision" in attributes
        assert attributes["display_precision"] == 2

        # Test with pH sensor (also has suggested_display_precision=2)
        ph_sensor_desc = next(desc for desc in POOL_SENSORS if desc.key == "ph")
        ph_sensor = IopoolSensor(
            mock_coordinator,
            ph_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        ph_attributes = ph_sensor.extra_state_attributes
        assert "display_precision" in ph_attributes
        assert ph_attributes["display_precision"] == 2

        # Test with ORP sensor (no suggested_display_precision)
        orp_sensor_desc = next(desc for desc in POOL_SENSORS if desc.key == "orp")
        orp_sensor = IopoolSensor(
            mock_coordinator,
            orp_sensor_desc,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        orp_attributes = orp_sensor.extra_state_attributes
        assert "display_precision" not in orp_attributes


class TestIopoolElapsedFiltrationSensor:
    """Test the elapsed filtration sensor's own logic."""

    def _make_sensor(self, coordinator_data) -> IopoolElapsedFiltrationSensor:
        """Build a sensor whose coordinator returns the given data."""
        coordinator = MagicMock()
        coordinator.data = coordinator_data
        return IopoolElapsedFiltrationSensor(
            coordinator,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
            "Test Pool Elapsed Filtration Duration Today",
        )

    @pytest.mark.parametrize(
        ("seconds_matched", "expected"),
        [
            (3600, 1.0),
            (5400, 1.5),
            (0, 0.0),
            (131.0169885, pytest.approx(0.03639360791666667)),
        ],
    )
    def test_native_value_converts_seconds_to_hours(
        self, seconds_matched: float, expected: float
    ) -> None:
        """Seconds from history_stats are reported as hours."""
        data = MagicMock()
        data.seconds_matched = seconds_matched

        assert self._make_sensor(data).native_value == expected

    def test_native_value_none_when_coordinator_has_no_data(self) -> None:
        """A coordinator that has not refreshed yet yields no value."""
        assert self._make_sensor(None).native_value is None

    def test_native_value_none_when_nothing_matched(self) -> None:
        """history_stats reports None rather than 0 when it cannot compute."""
        data = MagicMock()
        data.seconds_matched = None

        assert self._make_sensor(data).native_value is None

    @pytest.mark.parametrize(
        ("pool_name", "expected_entity_id"),
        [
            ("Test Pool", "sensor.iopool_test_pool_elapsed_filtration_duration"),
            ("Piscine été", "sensor.iopool_piscine_ete_elapsed_filtration_duration"),
        ],
    )
    def test_entity_id_is_slugified_from_pool_name(
        self, pool_name: str, expected_entity_id: str
    ) -> None:
        """The entity_id follows the same slug rules as the other sensors."""
        sensor = IopoolElapsedFiltrationSensor(
            MagicMock(), "test_entry_id", TEST_POOL_ID, pool_name, "Whatever"
        )

        assert sensor.entity_id == expected_entity_id

    async def test_added_to_hass_subscribes_to_source_state_changes(self) -> None:
        """The coordinator's state listener must be wired up and torn down.

        Without it the sensor only updates on the coordinator's own schedule
        and ignores the pump switch turning on or off.
        """
        coordinator = MagicMock()
        remove_listener = MagicMock()
        coordinator.async_setup_state_listener.return_value = remove_listener
        sensor = IopoolElapsedFiltrationSensor(
            coordinator, "test_entry_id", TEST_POOL_ID, TEST_POOL_TITLE, "Whatever"
        )
        sensor.async_on_remove = MagicMock()
        sensor.hass = MagicMock()
        sensor.async_write_ha_state = MagicMock()

        with patch.object(CoordinatorEntity, "async_added_to_hass", AsyncMock()):
            await sensor.async_added_to_hass()

        coordinator.async_setup_state_listener.assert_called_once_with()
        sensor.async_on_remove.assert_called_once_with(remove_listener)
