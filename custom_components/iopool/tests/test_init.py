"""Tests for iopool integration init."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.iopool import async_setup_entry, async_unload_entry
from custom_components.iopool.const import DOMAIN
import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .conftest import TEST_API_KEY, TEST_POOL_ID, TEST_POOL_TITLE


class TestIntegrationInit:
    """Test iopool integration initialization."""

    @pytest.mark.asyncio
    @patch("custom_components.iopool.IopoolDataUpdateCoordinator")
    @patch("custom_components.iopool.Filtration")
    async def test_async_setup_entry_success(
        self,
        mock_filtration_class,
        mock_coordinator_class,
        hass: HomeAssistant,
    ) -> None:
        """Test successful setup of config entry."""
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
            options={
                "filtration": {
                    "switch_entity": None,
                    "summer_filtration": {
                        "status": False,
                        "min_duration": None,
                        "max_duration": None,
                        "slot1": {
                            "name": None,
                            "start": None,
                            "duration_percent": 50,
                        },
                        "slot2": {
                            "name": None,
                            "start": None,
                            "duration_percent": 50,
                        },
                    },
                    "winter_filtration": {
                        "status": False,
                        "start": None,
                        "duration": None,
                    },
                }
            },
            source="user",
            unique_id=TEST_POOL_ID,
            discovery_keys=frozenset(),
            subentries_data={},
        )

        # Mock coordinator
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        # Mock filtration
        mock_filtration = MagicMock()
        mock_filtration.config_filtration_enabled.return_value = False
        mock_filtration.setup_time_events = MagicMock()
        mock_filtration_class.return_value = mock_filtration

        # Mock platform setup
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

        result = await async_setup_entry(hass, config_entry)

        assert result is True
        mock_coordinator_class.assert_called_once_with(hass, TEST_API_KEY)
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()
        mock_filtration_class.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.iopool.IopoolDataUpdateCoordinator")
    async def test_async_setup_entry_coordinator_fails(
        self,
        mock_coordinator_class,
        hass: HomeAssistant,
    ) -> None:
        """Test setup failure when coordinator refresh fails."""
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

        # Mock coordinator that fails
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh.side_effect = Exception(
            "API Error"
        )
        mock_coordinator_class.return_value = mock_coordinator

        with pytest.raises(Exception, match="API Error"):
            await async_setup_entry(hass, config_entry)

    @pytest.mark.asyncio
    async def test_async_unload_entry_success(self, hass: HomeAssistant) -> None:
        """Test successful unloading of config entry."""
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

        # Mock runtime data with remove listeners
        remove_listener_mock = MagicMock()
        runtime_data = MagicMock()
        runtime_data.remove_time_listeners = [remove_listener_mock]
        config_entry.runtime_data = runtime_data

        # Initialize hass.data for domain
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][config_entry.entry_id] = {"test": "data"}

        # Mock platform unload
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        result = await async_unload_entry(hass, config_entry)

        assert result is True
        remove_listener_mock.assert_called_once()
        # Check that entry was removed from hass.data
        assert config_entry.entry_id not in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_async_unload_entry_platform_fails(self, hass: HomeAssistant) -> None:
        """Test unload entry when platform unload fails."""
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
        config_entry.runtime_data = MagicMock()
        config_entry.runtime_data.remove_time_listeners = []

        # Mock platform unload failure
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        result = await async_unload_entry(hass, config_entry)

        assert result is False
