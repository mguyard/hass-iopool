"""Test the iopool binary sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.iopool.binary_sensor import (
    POOL_BINARY_SENSORS,
    POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION,
    IopoolBinarySensor,
    async_setup_entry,
)
from custom_components.iopool.const import CONF_POOL_ID
from custom_components.iopool.models import IopoolConfigData, IopoolData
import pytest

from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .conftest import TEST_API_KEY, TEST_POOL_ID, TEST_POOL_TITLE


class TestIopoolBinarySensorPlatform:
    """Test class for iopool binary sensor platform."""

    @pytest.mark.asyncio
    @patch("custom_components.iopool.binary_sensor.IopoolBinarySensor")
    async def test_async_setup_entry(
        self,
        mock_binary_sensor_class,
        hass: HomeAssistant,
        mock_config_entry,
        mock_iopool_coordinator,
    ) -> None:
        """Test binary sensor platform setup."""
        # Mock async_add_entities
        async_add_entities = AsyncMock()

        # Mock config data
        config_data = MagicMock(spec=IopoolConfigData)
        config_data.options = MagicMock()
        config_data.options.filtration = {}

        # Mock filtration
        filtration_mock = MagicMock()
        filtration_mock.configuration_filtration_enabled = True

        # Mock runtime data
        runtime_data = MagicMock(spec=IopoolData)
        runtime_data.coordinator = mock_iopool_coordinator
        runtime_data.config = config_data
        runtime_data.filtration = filtration_mock

        mock_config_entry.runtime_data = runtime_data
        mock_config_entry.data = {
            CONF_API_KEY: TEST_API_KEY,
            CONF_POOL_ID: TEST_POOL_ID,
        }

        # Call setup entry
        await async_setup_entry(hass, mock_config_entry, async_add_entities)

        # Verify async_add_entities was called
        async_add_entities.assert_called_once()
        call_args = async_add_entities.call_args[0][0]

        # Should create entities for both regular and conditional sensors
        expected_sensors = len(POOL_BINARY_SENSORS) + len(
            POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION
        )
        assert len(call_args) == expected_sensors

    @pytest.mark.asyncio
    async def test_async_setup_entry_no_pool_data(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ) -> None:
        """Test binary sensor platform setup with no pool data."""
        # Mock async_add_entities
        async_add_entities = AsyncMock()

        # Mock coordinator that returns None for pool data
        mock_coordinator = MagicMock()
        mock_coordinator.get_pool_data.return_value = None

        # Mock runtime data with all required attributes
        runtime_data = MagicMock(spec=IopoolData)
        runtime_data.coordinator = mock_coordinator
        runtime_data.config = MagicMock()  # Add config
        runtime_data.filtration = MagicMock()  # Add filtration

        mock_config_entry.runtime_data = runtime_data
        mock_config_entry.data = {
            CONF_API_KEY: TEST_API_KEY,
            CONF_POOL_ID: TEST_POOL_ID,
        }

        # Call setup entry
        await async_setup_entry(hass, mock_config_entry, async_add_entities)

        # Should not call async_add_entities when no pool data
        async_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_setup_entry_filtration_disabled(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_iopool_coordinator,
    ) -> None:
        """Test binary sensor platform setup with filtration disabled."""
        # Mock async_add_entities
        async_add_entities = AsyncMock()

        # Mock filtration disabled
        filtration_mock = MagicMock()
        filtration_mock.configuration_filtration_enabled = False

        # Mock runtime data with all required attributes
        runtime_data = MagicMock(spec=IopoolData)
        runtime_data.coordinator = mock_iopool_coordinator
        runtime_data.filtration = filtration_mock
        runtime_data.config = MagicMock()  # Add config

        mock_config_entry.runtime_data = runtime_data
        mock_config_entry.data = {
            CONF_API_KEY: TEST_API_KEY,
            CONF_POOL_ID: TEST_POOL_ID,
        }

        # Call setup entry
        await async_setup_entry(hass, mock_config_entry, async_add_entities)

        # Should only create regular binary sensors (not conditional ones)
        async_add_entities.assert_called_once()
        call_args = async_add_entities.call_args[0][0]
        assert len(call_args) == len(POOL_BINARY_SENSORS)


class TestIopoolBinarySensor:
    """Test class for iopool binary sensor entity."""

    def test_binary_sensor_initialization(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test binary sensor initialization."""
        sensor_description = POOL_BINARY_SENSORS[0]  # action_required
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.entity_description == sensor_description
        assert (
            sensor.unique_id == f"test_entry_id_{TEST_POOL_ID}_{sensor_description.key}"
        )
        assert sensor.has_entity_name is True
        assert sensor.translation_key == sensor_description.translation_key

    def test_action_required_sensor_properties(
        self,
        mock_iopool_coordinator,
        mock_api_response,
    ) -> None:
        """Test action required sensor properties."""
        sensor_description = POOL_BINARY_SENSORS[0]  # action_required
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Test when action is not required
        mock_iopool_coordinator.get_pool_data.return_value = mock_api_response.pools[0]
        assert sensor.is_on is False
        assert sensor.available is True

        # Test when action is required
        pool_data = mock_api_response.pools[0]
        pool_data.has_action_required = True
        mock_iopool_coordinator.get_pool_data.return_value = pool_data
        assert sensor.is_on is True

    def test_filtration_sensor_properties(
        self,
        mock_iopool_coordinator,
        mock_api_response,
        hass,
    ) -> None:
        """Test filtration sensor properties."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Mock switch state
        switch_state = MagicMock()
        switch_state.state = "on"
        sensor.hass = hass
        hass.states.get.return_value = switch_state

        # Test filtration sensor
        mock_iopool_coordinator.get_pool_data.return_value = mock_api_response.pools[0]
        assert sensor.is_on is True

        # Test when switch is off
        switch_state.state = "off"
        assert sensor.is_on is False

        # Test when no switch entity - mock at the filtration level
        mock_filtration = mock_iopool_coordinator.config_entry.runtime_data.filtration
        mock_filtration.get_switch_entity.return_value = None
        assert sensor.is_on is False

    def test_sensor_unavailable_when_no_pool_data(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test sensor availability when no pool data."""
        sensor_description = POOL_BINARY_SENSORS[0]
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Test when coordinator has no data
        mock_iopool_coordinator.data = None
        assert sensor.available is False

        # Test when pool not found
        mock_iopool_coordinator.data = MagicMock()
        mock_iopool_coordinator.get_pool_data.return_value = None
        assert sensor.available is False

    def test_extra_state_attributes_action_required(
        self,
        mock_iopool_coordinator,
        mock_api_response,
    ) -> None:
        """Test extra state attributes for action required sensor."""
        sensor_description = POOL_BINARY_SENSORS[0]  # action_required
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        mock_iopool_coordinator.get_pool_data.return_value = mock_api_response.pools[0]
        attributes = sensor.extra_state_attributes

        assert "is_valid" in attributes
        assert "measure_mode" in attributes
        assert "measured_at" in attributes
        assert attributes["is_valid"] is True
        assert attributes["measure_mode"] == "gateway"

    def test_extra_state_attributes_filtration(
        self,
        mock_iopool_coordinator,
        mock_api_response,
        hass,
    ) -> None:
        """Test extra state attributes for filtration sensor."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        sensor.hass = hass
        state_mock = MagicMock()
        state_mock.attributes = {}
        hass.states.get.return_value = state_mock

        mock_iopool_coordinator.get_pool_data.return_value = mock_api_response.pools[0]
        attributes = sensor.extra_state_attributes

        assert "filtration_mode" in attributes
        assert attributes["filtration_mode"] == "Standard"
        assert "filtration_duration_minutes" in attributes
        assert attributes["filtration_duration_minutes"] == 8.5

    @pytest.mark.asyncio
    async def test_async_added_to_hass_filtration_sensor(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test async_added_to_hass for filtration sensor."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Mock restore state
        sensor.async_get_last_state = AsyncMock(return_value=None)
        sensor.async_on_remove = MagicMock()
        sensor.hass = hass

        await sensor.async_added_to_hass()

        # Should set up state change listener
        sensor.async_on_remove.assert_called()
