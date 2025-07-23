"""Test the iopool select entities."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.iopool.select import (
    BOOST_OPTIONS,
    MODE_OPTIONS,
    POOL_SELECTS_CONDITIONAL_FILTRATION,
    IopoolSelect,
)
import pytest

from homeassistant.components.select import SelectEntityDescription

TEST_POOL_ID = "pool_123"
TEST_POOL_TITLE = "My Pool"


@pytest.fixture
def mock_iopool_coordinator():
    """Return a mocked iopool coordinator."""
    coordinator = MagicMock()
    coordinator.get_pool_data.return_value = MagicMock()
    return coordinator


class TestIopoolSelect:
    """Test the iopool select entity."""

    @pytest.mark.parametrize(
        ("select_index", "expected_key", "expected_options"),
        [
            (0, "boost_selector", BOOST_OPTIONS),
            (1, "pool_mode", MODE_OPTIONS),
        ],
    )
    def test_iopool_select_properties(
        self,
        mock_iopool_coordinator,
        select_index,
        expected_key,
        expected_options,
    ) -> None:
        """Test iopool select entity properties."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[select_index]
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        assert select_entity.unique_id == f"test_entry_id_{TEST_POOL_ID}_{expected_key}"
        assert select_entity.options == expected_options

    def test_iopool_select_icon(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test iopool select icon."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]
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


class TestIopoolSelectAdvanced:
    """Test advanced functionality."""

    @pytest.mark.asyncio
    async def test_boost_selector_basic_functionality(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test basic boost selector functionality."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()
        filtration_mock.async_start_filtration = AsyncMock()
        filtration_mock.async_stop_filtration = AsyncMock()
        filtration_mock.get_filtration_attributes = AsyncMock(
            return_value=(None, None, {})
        )
        filtration_mock.update_filtration_attributes = AsyncMock()
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
        select_entity.async_get_last_state = AsyncMock(return_value=None)

        # Initialize state
        await select_entity.async_added_to_hass()

        # For boost selector, initial option should be "None"
        assert select_entity.current_option == "None"

        # Test selecting boost option
        await select_entity.async_select_option("2H")
        assert select_entity.current_option == "2H"

    @pytest.mark.asyncio
    async def test_pool_mode_basic_functionality(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test basic pool mode functionality."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[1]  # pool_mode
        filtration_mock = MagicMock()

        # Mock pool with STANDARD mode
        mock_pool = MagicMock()
        mock_pool.mode = "STANDARD"
        mock_pool.id = TEST_POOL_ID

        # Mock coordinator.data with pools list
        mock_iopool_coordinator.data = MagicMock()
        mock_iopool_coordinator.data.pools = [mock_pool]

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )
        select_entity.hass = hass
        select_entity.async_get_last_state = AsyncMock(return_value=None)

        await select_entity.async_added_to_hass()

        assert select_entity.current_option == "Standard"

    @pytest.mark.asyncio
    async def test_boost_timer_functionality(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test boost timer advanced functionality."""

        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()
        filtration_mock.async_start_filtration = AsyncMock()
        filtration_mock.async_stop_filtration = AsyncMock()
        filtration_mock.get_filtration_attributes = AsyncMock(
            return_value=(None, None, {})
        )
        filtration_mock.update_filtration_attributes = AsyncMock()
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
        select_entity.async_get_last_state = AsyncMock(return_value=None)

        # Mock timer tracking
        with patch(
            "custom_components.iopool.select.async_track_point_in_time"
        ) as mock_track:
            mock_track.return_value = MagicMock()

            # Initialize state
            await select_entity.async_added_to_hass()

            # Test boost with valid time format
            await select_entity.async_select_option("2H")
            assert select_entity.current_option == "2H"

            # Verify timer was set
            mock_track.assert_called()

            # Test canceling boost
            await select_entity.async_select_option("None")
            assert select_entity.current_option == "None"

    @pytest.mark.asyncio
    async def test_boost_with_last_state_restoration(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test boost state restoration from last state."""

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

        # Mock last state with boost still active
        mock_last_state = MagicMock()
        mock_last_state.state = "2H"
        mock_last_state.attributes = {
            "boost_end_time": "2025-01-01T15:00:00+01:00",
            "boost_start_time": "2025-01-01T13:00:00+01:00",
        }
        select_entity.async_get_last_state = AsyncMock(return_value=mock_last_state)

        # Mock timer and datetime
        with (
            patch(
                "custom_components.iopool.select.async_track_point_in_time"
            ) as mock_track,
            patch("homeassistant.util.dt.parse_datetime") as mock_parse,
            patch("homeassistant.util.dt.utcnow") as mock_now,
        ):
            # Setup times so boost is still active
            future_time = datetime(2025, 1, 1, 15, 0, 0)
            current_time = datetime(2025, 1, 1, 14, 0, 0)

            mock_parse.return_value = future_time
            mock_now.return_value = current_time
            mock_track.return_value = MagicMock()

            await select_entity.async_added_to_hass()

            # Should restore the boost state
            assert select_entity.current_option == "2H"
            # Timer should be set up
            mock_track.assert_called_once()

    @pytest.mark.asyncio
    async def test_boost_expired_restoration(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test boost expired during restoration."""

        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()
        filtration_mock.async_stop_filtration = AsyncMock()
        filtration_mock.get_filtration_attributes = AsyncMock(
            return_value=(None, None, {})
        )
        filtration_mock.update_filtration_attributes = AsyncMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            select_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )
        select_entity.hass = hass

        # Mock last state with expired boost
        mock_last_state = MagicMock()
        mock_last_state.state = "2H"
        mock_last_state.attributes = {
            "boost_end_time": "2025-01-01T13:00:00+01:00",
            "boost_start_time": "2025-01-01T11:00:00+01:00",
        }
        select_entity.async_get_last_state = AsyncMock(return_value=mock_last_state)

        with (
            patch("homeassistant.util.dt.parse_datetime") as mock_parse,
            patch("homeassistant.util.dt.utcnow") as mock_now,
        ):
            # Setup times so boost is expired
            past_time = datetime(2025, 1, 1, 13, 0, 0)
            current_time = datetime(2025, 1, 1, 15, 0, 0)

            mock_parse.return_value = past_time
            mock_now.return_value = current_time

            await select_entity.async_added_to_hass()

            # Should reset to None and stop filtration
            assert select_entity.current_option == "None"
            filtration_mock.async_stop_filtration.assert_called_once()

    @pytest.mark.asyncio
    async def test_pool_mode_selection(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test pool mode selection functionality."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[1]  # pool_mode
        filtration_mock = MagicMock()
        filtration_mock.async_change_pool_mode = AsyncMock()

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

        # Test mode selection - this should set the option
        await select_entity.async_select_option("Active-Winter")
        assert select_entity.current_option == "Active-Winter"

        # For now, the pool mode change is done via integration reload
        # not via async_change_pool_mode direct call

    @pytest.mark.asyncio
    async def test_options_property_unknown_key(
        self,
        mock_iopool_coordinator,
    ) -> None:
        """Test options property with unknown key."""
        # Create description with unknown key
        unknown_description = SelectEntityDescription(
            key="unknown_key",
            translation_key="unknown",
        )
        filtration_mock = MagicMock()

        select_entity = IopoolSelect(
            mock_iopool_coordinator,
            filtration_mock,
            unknown_description,
            "test_entry_id",
            TEST_POOL_ID,
            TEST_POOL_TITLE,
        )

        # Should return empty list for unknown key
        assert select_entity.options == []

    @pytest.mark.asyncio
    async def test_invalid_boost_format(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test boost with invalid time format."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()
        filtration_mock.async_start_filtration = AsyncMock()

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

        # Test invalid boost format
        await select_entity.async_select_option("InvalidTime")
        assert select_entity.current_option == "InvalidTime"

        # Should not start filtration with invalid format
        filtration_mock.async_start_filtration.assert_not_called()

    @pytest.mark.asyncio
    async def test_boost_filtration_with_active_slot(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test boost when filtration already has active slot."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()
        filtration_mock.async_start_filtration = AsyncMock()
        filtration_mock.publish_event = AsyncMock()
        filtration_mock.get_filtration_attributes = AsyncMock(
            return_value=(None, None, {"active_slot": "existing_slot"})
        )

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

        # Test boost with existing active slot
        await select_entity.async_select_option("2H")
        assert select_entity.current_option == "2H"

        # Should still start boost filtration
        filtration_mock.async_start_filtration.assert_called_once()


class TestIopoolSelectEdgeCases:
    """Test edge cases for IopoolSelect."""

    @pytest.mark.asyncio
    async def test_clean_filtration_attributes_via_boost_stop(
        self,
        mock_iopool_coordinator,
        hass,
    ) -> None:
        """Test cleaning filtration attributes when stopping boost."""
        select_description = POOL_SELECTS_CONDITIONAL_FILTRATION[0]  # boost_selector
        filtration_mock = MagicMock()
        filtration_mock.async_start_filtration = AsyncMock()
        filtration_mock.async_stop_filtration = AsyncMock()
        filtration_mock.publish_event = AsyncMock()
        filtration_mock.get_filtration_attributes = AsyncMock(
            return_value=(None, None, {"active_slot": "boost"})
        )
        filtration_mock.update_filtration_attributes = AsyncMock()

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

        # Set a boost first, then cancel it to trigger cleanup
        await select_entity.async_select_option("2H")
        await select_entity.async_select_option("None")

        # Verify it was called to clean the boost slot
        filtration_mock.update_filtration_attributes.assert_called_with(
            active_slot=None
        )
