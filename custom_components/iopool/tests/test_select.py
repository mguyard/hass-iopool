"""Test the iopool select platform."""

from __future__ import annotations  # noqa: I001

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.iopool.const import CONF_POOL_ID
from custom_components.iopool.models import IopoolConfigData, IopoolData
from custom_components.iopool.select import (
    BOOST_OPTIONS,
    IopoolSelect,
    MODE_OPTIONS,
    POOL_SELECTS_CONDITIONAL_FILTRATION,
    async_setup_entry,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .conftest import TEST_API_KEY, TEST_POOL_ID, TEST_POOL_TITLE


class TestIopoolSelectPlatform:
    """Test class for iopool select platform."""

    @pytest.mark.asyncio
    @patch("custom_components.iopool.select.IopoolSelect")
    async def test_async_setup_entry_with_filtration(
        self,
        mock_select_class,
        hass: HomeAssistant,
        mock_config_entry,
        mock_iopool_coordinator,
    ) -> None:
        """Test select platform setup with filtration enabled."""
        # Mock async_add_entities
        async_add_entities = AsyncMock()

        # Mock config data
        config_data = MagicMock(spec=IopoolConfigData)
        config_data.options = MagicMock()
        config_data.options.filtration = {"switch_entity": "switch.pool_pump"}

        # Mock filtration enabled
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

        # Verify async_add_entities was called with selects
        async_add_entities.assert_called_once()
        call_args = async_add_entities.call_args[0][0]
        assert len(call_args) == len(POOL_SELECTS_CONDITIONAL_FILTRATION)

    @pytest.mark.asyncio
    async def test_async_setup_entry_no_filtration(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_iopool_coordinator,
    ) -> None:
        """Test select platform setup with filtration disabled."""
        # Mock async_add_entities
        async_add_entities = AsyncMock()

        # Mock config data
        config_data = MagicMock(spec=IopoolConfigData)
        config_data.options = MagicMock()
        config_data.options.filtration = {}

        # Mock filtration disabled
        filtration_mock = MagicMock()
        filtration_mock.configuration_filtration_enabled = False

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

        # Should not add any entities when filtration is disabled
        async_add_entities.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_async_setup_entry_no_pool_data(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ) -> None:
        """Test select platform setup with no pool data."""
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

        # Call setup entry - should return early with no entities
        await async_setup_entry(hass, mock_config_entry, async_add_entities)

        # Should not call async_add_entities when no pool data
        async_add_entities.assert_not_called()


class TestIopoolSelect:
    """Test class for iopool select entity."""

    def test_select_initialization(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test select initialization."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert select_entity.entity_description == select_description
        assert (
            select_entity.unique_id
            == f"test_entry_id_{TEST_POOL_ID}_{select_description.key}"
        )

    def test_boost_selector_options(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test boost selector options."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert select_entity.options == BOOST_OPTIONS

    def test_pool_mode_options(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test pool mode options."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[1]  # pool_mode
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert select_entity.options == MODE_OPTIONS

    @pytest.mark.asyncio
    async def test_async_select_option_boost_start(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test selecting boost option."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()
        filtration_mock.async_start_filtration = AsyncMock()
        filtration_mock.publish_event = AsyncMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )
        select_entity.hass = hass
        select_entity.async_write_ha_state = MagicMock()

        # Test selecting 2H boost
        await select_entity.async_select_option("2H")

        # Verify filtration was started
        filtration_mock.async_start_filtration.assert_called_once()
        filtration_mock.publish_event.assert_called_once()
        assert select_entity.current_option == "2H"

    @pytest.mark.asyncio
    async def test_async_select_option_boost_stop(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test stopping boost."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()
        filtration_mock.async_start_filtration = AsyncMock()
        filtration_mock.async_stop_filtration = AsyncMock()  # This should be AsyncMock
        filtration_mock.update_filtration_attributes = AsyncMock()
        filtration_mock.publish_event = AsyncMock()  # Add this
        filtration_mock.get_filtration_attributes = AsyncMock(
            return_value=(None, None, {})
        )  # Add this

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )
        select_entity.hass = hass
        select_entity.async_write_ha_state = MagicMock()

        # Simulate boost active state first
        await select_entity.async_select_option("2H")
        # Test selecting None to stop boost
        await select_entity.async_select_option("None")

        # Verify filtration was stopped
        filtration_mock.async_stop_filtration.assert_called_once()
        assert select_entity.current_option == "None"

    @pytest.mark.asyncio
    async def test_async_select_option_pool_mode(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test selecting pool mode."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[1]  # pool_mode
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )
        select_entity.hass = hass
        select_entity.async_write_ha_state = MagicMock()
        hass.config_entries.async_schedule_reload = MagicMock()

        # Test selecting Active-Winter mode
        await select_entity.async_select_option("Active-Winter")

        # Verify reload was scheduled
        hass.config_entries.async_schedule_reload.assert_called_once()
        assert select_entity.current_option == "Active-Winter"

    @pytest.mark.asyncio
    async def test_async_added_to_hass_no_last_state(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test async_added_to_hass with no last state."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )
        select_entity.hass = hass

        # Mock no last state
        select_entity.async_get_last_state = AsyncMock(return_value=None)

        await select_entity.async_added_to_hass()

        # Should initialize with default value
        assert select_entity.current_option == "None"

    @pytest.mark.asyncio
    async def test_async_will_remove_from_hass(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test cleanup when entity is removed."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Mock timer to verify cleanup
        with patch.object(select_entity, "_boost_timer", MagicMock()) as mock_timer:
            await select_entity.async_will_remove_from_hass()
            # Timer should be cancelled if it exists
            if mock_timer:
                mock_timer.assert_called()

    def test_icon_property(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test icon property."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert select_entity.icon == select_description.icon
