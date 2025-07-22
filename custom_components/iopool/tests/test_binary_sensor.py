"""Test the iopool binary sensor platform."""

from __future__ import annotations

from datetime import datetime, time, timedelta
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

    @pytest.mark.asyncio
    async def test_async_added_to_hass_with_last_state_on(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test async_added_to_hass with restored state 'on'."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Mock last state as 'on'
        last_state = MagicMock()
        last_state.state = "on"
        last_state.attributes = {"test": "value"}
        sensor.async_get_last_state = AsyncMock(return_value=last_state)
        sensor.async_on_remove = MagicMock()
        sensor.hass = hass

        # Mock _get_state to return None (no current state)
        hass.states.get.return_value = None

        await sensor.async_added_to_hass()

        # Should restore the 'on' state
        hass.states.async_set.assert_called_with(
            sensor.entity_id, "on", last_state.attributes
        )

    @pytest.mark.asyncio
    async def test_async_added_to_hass_with_last_state_off(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test async_added_to_hass with restored state 'off'."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Mock last state as 'off'
        last_state = MagicMock()
        last_state.state = "off"
        last_state.attributes = {"test": "value"}
        sensor.async_get_last_state = AsyncMock(return_value=last_state)
        sensor.async_on_remove = MagicMock()
        sensor.hass = hass

        # Mock _get_state to return None (no current state)
        hass.states.get.return_value = None

        await sensor.async_added_to_hass()

        # Should restore the 'off' state
        hass.states.async_set.assert_called_with(
            sensor.entity_id, "off", last_state.attributes
        )

    @pytest.mark.asyncio
    async def test_async_added_to_hass_no_switch_entity(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test async_added_to_hass when switch entity is not found."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Mock filtration to return None for switch entity
        mock_filtration = mock_iopool_coordinator.config_entry.runtime_data.filtration
        mock_filtration.get_switch_entity.return_value = None

        sensor.async_get_last_state = AsyncMock(return_value=None)
        sensor.async_on_remove = MagicMock()
        sensor.hass = hass

        await sensor.async_added_to_hass()

        # Should still call async_on_remove but not set up state listener
        sensor.async_on_remove.assert_called()

    @pytest.mark.asyncio
    async def test_switch_state_change_callback(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test switch state change callback functionality."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Mock switch entity exists
        mock_filtration = mock_iopool_coordinator.config_entry.runtime_data.filtration
        mock_filtration.get_switch_entity.return_value = "switch.test_switch"

        sensor.async_get_last_state = AsyncMock(return_value=None)
        sensor.hass = hass

        # Capture the callback function
        captured_callback = None

        def mock_async_on_remove(callback):
            nonlocal captured_callback
            captured_callback = callback

        sensor.async_on_remove = mock_async_on_remove

        await sensor.async_added_to_hass()

        # Simulate switch state change event with 'on' state
        event = MagicMock()
        new_state = MagicMock()
        new_state.state = "on"
        event.data = {"new_state": new_state}

        # Mock current state
        current_state = MagicMock()
        current_state.attributes = {"existing": "attribute"}
        hass.states.get.return_value = current_state

        # Call the captured callback
        if hasattr(captured_callback, "__wrapped__"):
            # It's an async_track_state_change_event call, get the actual callback
            # We need to simulate the actual callback that would be passed
            with patch(
                "custom_components.iopool.binary_sensor.async_track_state_change_event"
            ) as mock_track:
                # Re-run the setup to capture the actual callback
                await sensor.async_added_to_hass()
                callback_func = mock_track.call_args[0][
                    2
                ]  # Third argument is the callback

                # Now test the callback
                callback_func(event)

                # Should update state to 'on'
                hass.states.async_set.assert_called_with(
                    sensor.entity_id, "on", {"existing": "attribute"}
                )

    def test_is_on_action_required_no_pool(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test is_on for action_required sensor when no pool data."""
        sensor_description = POOL_BINARY_SENSORS[0]  # action_required
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Mock coordinator to return None for pool data
        mock_iopool_coordinator.get_pool_data.return_value = None

        assert sensor.is_on is None

    def test_is_on_filtration_no_switch_state(
        self,
        mock_iopool_coordinator,
        mock_api_response,
        hass,
    ) -> None:
        """Test is_on for filtration sensor when switch state is None."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        sensor.hass = hass
        mock_iopool_coordinator.get_pool_data.return_value = mock_api_response.pools[0]

        # Mock switch entity exists but state is None
        mock_filtration = mock_iopool_coordinator.config_entry.runtime_data.filtration
        mock_filtration.get_switch_entity.return_value = "switch.test_switch"
        hass.states.get.return_value = None

        assert sensor.is_on is False

    def test_extra_state_attributes_filtration_winter_mode(
        self,
        mock_iopool_coordinator,
        mock_api_response,
        hass,
    ) -> None:
        """Test extra state attributes for filtration sensor in winter mode."""
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

        # Mock winter mode
        mock_filtration = mock_iopool_coordinator.config_entry.runtime_data.filtration
        mock_filtration.get_filtration_pool_mode.return_value = "Active-Winter"
        mock_filtration.configuration_filtration_enabled_winter = True

        # Mock winter filtration data
        winter_start_time = time(10, 0)  # 10:00 AM
        winter_duration = timedelta(hours=2)  # 2 hours
        mock_filtration.get_winter_filtration_start_end.return_value = (
            winter_start_time,
            winter_duration,
        )

        mock_iopool_coordinator.get_pool_data.return_value = mock_api_response.pools[0]
        attributes = sensor.extra_state_attributes

        assert "filtration_mode" in attributes
        assert attributes["filtration_mode"] == "Active-Winter"
        assert "filtration_duration_minutes" in attributes
        assert attributes["filtration_duration_minutes"] == 120.0  # 2 hours
        assert "winter_filtration_start" in attributes
        assert "winter_filtration_end" in attributes

    def test_extra_state_attributes_filtration_passive_winter_mode(
        self,
        mock_iopool_coordinator,
        mock_api_response,
        hass,
    ) -> None:
        """Test extra state attributes for filtration sensor in passive winter mode."""
        sensor_description = POOL_BINARY_SENSORS_CONDITIONAL_FILTRATION[0]  # filtration
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        sensor.hass = hass

        # Mock existing state with attributes that should be cleaned
        state_mock = MagicMock()
        state_mock.attributes = {
            "filtration_duration_minutes": 120,
            "winter_filtration_start": "2024-01-01T10:00:00",
            "winter_filtration_end": "2024-01-01T12:00:00",
            "slot1_start_time": "2024-01-01T09:00:00",
            "slot1_end_time": "2024-01-01T11:00:00",
            "slot2_start_time": "2024-01-01T15:00:00",
            "slot2_end_time": "2024-01-01T17:00:00",
            "keep_this": "should_remain",
        }
        hass.states.get.return_value = state_mock

        # Mock passive winter mode
        mock_filtration = mock_iopool_coordinator.config_entry.runtime_data.filtration
        mock_filtration.get_filtration_pool_mode.return_value = "Passive-Winter"

        mock_iopool_coordinator.get_pool_data.return_value = mock_api_response.pools[0]
        attributes = sensor.extra_state_attributes

        assert "filtration_mode" in attributes
        assert attributes["filtration_mode"] == "Passive-Winter"

        # These attributes should be cleaned up
        assert "filtration_duration_minutes" not in attributes
        assert "winter_filtration_start" not in attributes
        assert "winter_filtration_end" not in attributes
        assert "slot1_start_time" not in attributes
        assert "slot1_end_time" not in attributes
        assert "slot2_start_time" not in attributes
        assert "slot2_end_time" not in attributes

        # This attribute should remain
        assert "keep_this" in attributes
        assert attributes["keep_this"] == "should_remain"

    def test_extra_state_attributes_filtration_summer_with_slot2(
        self,
        mock_iopool_coordinator,
        mock_api_response,
        hass,
    ) -> None:
        """Test extra state attributes for filtration sensor in summer mode with slot2."""
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
        state_mock.attributes = {
            "slot1_end_time": "existing_end_time",
            "slot2_end_time": "existing_slot2_end",
            "next_stop_time": "existing_stop_time",
            "active_slot": "existing_slot",
        }
        hass.states.get.return_value = state_mock

        # Mock summer mode with slot2 enabled
        mock_filtration = mock_iopool_coordinator.config_entry.runtime_data.filtration
        mock_filtration.get_filtration_pool_mode.return_value = "Standard"
        mock_filtration.configuration_filtration_enabled_summer = True

        # Mock slot times
        slot1_start = datetime(2024, 1, 1, 9, 0)
        slot2_start = datetime(2024, 1, 1, 15, 0)
        mock_filtration.get_summer_filtration_slot_start.side_effect = [
            slot1_start,  # First call for slot 1
            slot2_start,  # Second call for slot 2
        ]

        # Mock config with slot2 enabled (>0 duration)
        mock_config = mock_iopool_coordinator.config_entry.runtime_data.config
        mock_config.options.filtration.get.return_value = {
            "slot2": {"duration_percent": 25}  # >0 means slot2 is enabled
        }

        mock_iopool_coordinator.get_pool_data.return_value = mock_api_response.pools[0]
        attributes = sensor.extra_state_attributes

        assert "filtration_mode" in attributes
        assert attributes["filtration_mode"] == "Standard"
        assert "slot1_start_time" in attributes
        assert "slot2_start_time" in attributes

        # Preserved attributes should remain
        assert "slot1_end_time" in attributes
        assert attributes["slot1_end_time"] == "existing_end_time"
        assert "slot2_end_time" in attributes
        assert attributes["slot2_end_time"] == "existing_slot2_end"
        assert "next_stop_time" in attributes
        assert attributes["next_stop_time"] == "existing_stop_time"
        assert "active_slot" in attributes
        assert attributes["active_slot"] == "existing_slot"

    def test_icon_property(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test icon property."""
        sensor_description = POOL_BINARY_SENSORS[0]  # action_required
        sensor = IopoolBinarySensor(
            mock_iopool_coordinator,
            sensor_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert sensor.icon == sensor_description.icon
        assert sensor.icon == "mdi:gesture-tap-button"
