"""Tests for iopool integration init."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.iopool import (
    async_setup_entry,
    async_unload_entry,
    update_listener,
)
from custom_components.iopool.const import DOMAIN
import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CoreState, Event, HomeAssistant

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

        # Mock bus listener
        hass.bus = MagicMock()
        hass.bus.async_listen_once = MagicMock()

        # Mock state as not running
        hass.state = CoreState.not_running

        result = await async_setup_entry(hass, config_entry)

        assert result is True
        mock_coordinator_class.assert_called_once_with(hass, TEST_API_KEY)
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()
        mock_filtration_class.assert_called_once()

        # Check that runtime data was set up correctly
        assert config_entry.runtime_data is not None
        assert config_entry.runtime_data.coordinator == mock_coordinator
        assert config_entry.runtime_data.filtration == mock_filtration

        # Check that hass.data was set up
        assert DOMAIN in hass.data
        assert config_entry.entry_id in hass.data[DOMAIN]

        # Check that platforms were set up
        hass.config_entries.async_forward_entry_setups.assert_called_once()

        # Check that started event listener was registered
        hass.bus.async_listen_once.assert_called_once()

    @pytest.mark.asyncio
    @patch("custom_components.iopool.IopoolDataUpdateCoordinator")
    @patch("custom_components.iopool.Filtration")
    async def test_async_setup_entry_filtration_enabled_running(
        self,
        mock_filtration_class,
        mock_coordinator_class,
        hass: HomeAssistant,
    ) -> None:
        """Test setup when filtration is enabled and HA is running."""
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

        # Mock coordinator
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        # Mock filtration as enabled
        mock_filtration = MagicMock()
        mock_filtration.config_filtration_enabled.return_value = True
        mock_filtration.setup_time_events = MagicMock()
        mock_filtration_class.return_value = mock_filtration

        # Mock platform setup
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

        # Mock bus listener
        hass.bus = MagicMock()
        hass.bus.async_listen_once = MagicMock()

        # Mock state as running
        hass.state = CoreState.running

        result = await async_setup_entry(hass, config_entry)

        assert result is True
        # Check that setup_time_events was called because filtration is enabled and HA is running
        mock_filtration.setup_time_events.assert_called()

    @pytest.mark.asyncio
    async def test_on_started_event_filtration_enabled(
        self, hass: HomeAssistant
    ) -> None:
        """Test the _on_started event handler when filtration is enabled."""
        # Setup a mock filtration that's enabled
        mock_filtration = MagicMock()
        mock_filtration.config_filtration_enabled.return_value = True
        mock_filtration.setup_time_events = MagicMock()

        # Create the config entry and runtime data
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

        # We need to test the _on_started function by calling async_setup_entry
        # and capturing the registered callback
        captured_callback = None

        def capture_callback(event_type, callback):
            nonlocal captured_callback
            captured_callback = callback

        hass.bus = MagicMock()
        hass.bus.async_listen_once = capture_callback

        with (
            patch(
                "custom_components.iopool.IopoolDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch("custom_components.iopool.Filtration") as mock_filtration_class,
        ):
            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            mock_filtration_class.return_value = mock_filtration

            hass.config_entries.async_forward_entry_setups = AsyncMock(
                return_value=True
            )
            hass.state = CoreState.not_running

            # Call setup to register the callback
            await async_setup_entry(hass, config_entry)

            # Now call the captured callback with a mock event
            if captured_callback:
                mock_event = MagicMock(spec=Event)
                await captured_callback(mock_event)

                # Verify that setup_time_events was called
                mock_filtration.setup_time_events.assert_called()

    @pytest.mark.asyncio
    async def test_on_started_event_filtration_disabled(
        self, hass: HomeAssistant
    ) -> None:
        """Test the _on_started event handler when filtration is disabled."""
        # Setup a mock filtration that's disabled
        mock_filtration = MagicMock()
        mock_filtration.config_filtration_enabled.return_value = False
        mock_filtration.setup_time_events = MagicMock()

        # Create the config entry
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

        # Capture the registered callback
        captured_callback = None

        def capture_callback(event_type, callback):
            nonlocal captured_callback
            captured_callback = callback

        hass.bus = MagicMock()
        hass.bus.async_listen_once = capture_callback

        with (
            patch(
                "custom_components.iopool.IopoolDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch("custom_components.iopool.Filtration") as mock_filtration_class,
        ):
            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            mock_filtration_class.return_value = mock_filtration

            hass.config_entries.async_forward_entry_setups = AsyncMock(
                return_value=True
            )
            hass.state = CoreState.not_running

            # Call setup to register the callback
            await async_setup_entry(hass, config_entry)

            # Now call the captured callback with a mock event
            if captured_callback:
                mock_event = MagicMock(spec=Event)
                await captured_callback(mock_event)

                # Verify that setup_time_events was NOT called
                mock_filtration.setup_time_events.assert_not_called()

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
    async def test_async_unload_entry_no_runtime_data(
        self, hass: HomeAssistant
    ) -> None:
        """Test unload entry when runtime_data is None."""
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

        # No runtime data
        config_entry.runtime_data = None

        # Mock platform unload
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        result = await async_unload_entry(hass, config_entry)

        assert result is True

    @pytest.mark.asyncio
    async def test_async_unload_entry_no_remove_listeners(
        self, hass: HomeAssistant
    ) -> None:
        """Test unload entry when runtime_data has no remove_time_listeners."""
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

        # Runtime data without remove_time_listeners attribute
        runtime_data = MagicMock()
        del runtime_data.remove_time_listeners  # Remove the attribute
        config_entry.runtime_data = runtime_data

        # Mock platform unload
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        result = await async_unload_entry(hass, config_entry)

        assert result is True

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

    @pytest.mark.asyncio
    async def test_async_unload_entry_domain_not_in_data(
        self, hass: HomeAssistant
    ) -> None:
        """Test unload entry when domain is not in hass.data."""
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

        # Don't initialize hass.data for domain
        # hass.data should not contain DOMAIN

        # Mock platform unload
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        result = await async_unload_entry(hass, config_entry)

        assert result is True

    @pytest.mark.asyncio
    async def test_update_listener(self, hass: HomeAssistant) -> None:
        """Test update listener function."""
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
                    "switch_entity": "switch.pool_pump",
                    "summer_filtration": {
                        "status": True,
                        "min_duration": 4,
                        "max_duration": 12,
                    },
                }
            },
            source="user",
            unique_id=TEST_POOL_ID,
            discovery_keys=frozenset(),
            subentries_data={},
        )

        # Mock runtime data
        runtime_data = MagicMock()
        config_entry.runtime_data = runtime_data

        # Mock reload
        hass.config_entries.async_reload = AsyncMock()

        await update_listener(hass, config_entry)

        # Check that config was updated in runtime_data
        assert runtime_data.config is not None

        # Check that reload was called
        hass.config_entries.async_reload.assert_called_once_with(config_entry.entry_id)

    @pytest.mark.asyncio
    async def test_update_listener_no_runtime_data(self, hass: HomeAssistant) -> None:
        """Test update listener when runtime_data is None."""
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

        # No runtime data
        config_entry.runtime_data = None

        # Mock reload
        hass.config_entries.async_reload = AsyncMock()

        await update_listener(hass, config_entry)

        # Check that reload was still called
        hass.config_entries.async_reload.assert_called_once_with(config_entry.entry_id)
