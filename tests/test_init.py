"""Test the iopool integration init module."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from custom_components.iopool import (
    async_setup_entry,
    async_unload_entry,
    update_listener,
    PLATFORMS,
)
from custom_components.iopool.const import DOMAIN
from custom_components.iopool.models import IopoolConfigEntry


@pytest.mark.asyncio
async def test_async_setup_entry(
    hass_instance: HomeAssistant,
    mock_config_entry_data,
    mock_iopool_api_response,
    mock_aiohttp_session,
    mock_coordinator_update,
):
    """Test successful setup of config entry."""
    # Create a mock config entry
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.options = {}
    config_entry.entry_id = "test_entry_id"
    config_entry.runtime_data = None
    config_entry.async_on_unload = Mock()
    config_entry.add_update_listener = Mock(return_value=Mock())

    # Mock coordinator
    mock_coordinator_update.return_value = mock_iopool_api_response

    with patch("custom_components.iopool.IopoolDataUpdateCoordinator") as mock_coord_class, \
         patch("custom_components.iopool.Filtration") as mock_filtration_class, \
         patch.object(hass_instance.config_entries, "async_forward_entry_setups") as mock_forward:
        
        # Set up mock coordinator instance
        mock_coordinator = Mock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coord_class.return_value = mock_coordinator

        # Set up mock filtration instance
        mock_filtration = Mock()
        mock_filtration.config_filtration_enabled.return_value = False
        mock_filtration_class.return_value = mock_filtration

        # Mock forward setup to return True
        mock_forward.return_value = True

        # Call the function under test
        result = await async_setup_entry(hass_instance, config_entry)

        # Assertions
        assert result is True
        assert DOMAIN in hass_instance.data
        assert config_entry.entry_id in hass_instance.data[DOMAIN]
        
        # Check coordinator was created and refreshed
        mock_coord_class.assert_called_once()
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()
        
        # Check platforms were set up
        mock_forward.assert_called_once_with(config_entry, PLATFORMS)
        
        # Check runtime data was set
        assert config_entry.runtime_data is not None


@pytest.mark.asyncio
async def test_async_setup_entry_with_filtration_enabled(
    hass_instance: HomeAssistant,
    mock_config_entry_data,
    mock_iopool_api_response,
    mock_aiohttp_session,
    mock_coordinator_update,
):
    """Test setup with filtration enabled."""
    # Create a mock config entry
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.options = {}
    config_entry.entry_id = "test_entry_id"
    config_entry.runtime_data = None
    config_entry.async_on_unload = Mock()
    config_entry.add_update_listener = Mock(return_value=Mock())

    # Mock coordinator
    mock_coordinator_update.return_value = mock_iopool_api_response

    with patch("custom_components.iopool.IopoolDataUpdateCoordinator") as mock_coord_class, \
         patch("custom_components.iopool.Filtration") as mock_filtration_class, \
         patch.object(hass_instance.config_entries, "async_forward_entry_setups") as mock_forward:
        
        # Set up mock coordinator instance
        mock_coordinator = Mock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coord_class.return_value = mock_coordinator

        # Set up mock filtration instance with filtration enabled
        mock_filtration = Mock()
        mock_filtration.config_filtration_enabled.return_value = True
        mock_filtration.setup_time_events = Mock()
        mock_filtration_class.return_value = mock_filtration

        # Mock forward setup to return True
        mock_forward.return_value = True

        # Call the function under test
        result = await async_setup_entry(hass_instance, config_entry)

        # Assertions
        assert result is True
        # Check that setup_time_events was called when filtration is enabled
        mock_filtration.setup_time_events.assert_called()


@pytest.mark.asyncio
async def test_async_unload_entry(
    hass_instance: HomeAssistant,
    mock_config_entry_data,
):
    """Test successful unload of config entry."""
    # Create a mock config entry with runtime data
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    
    # Mock runtime data with time listeners
    mock_runtime_data = Mock()
    mock_runtime_data.remove_time_listeners = [Mock(), Mock()]
    config_entry.runtime_data = mock_runtime_data

    # Set up hass_instance.data
    hass_instance.data[DOMAIN] = {config_entry.entry_id: {"test": "data"}}

    with patch.object(hass_instance.config_entries, "async_unload_platforms") as mock_unload:
        mock_unload.return_value = True

        # Call the function under test
        result = await async_unload_entry(hass_instance, config_entry)

        # Assertions
        assert result is True
        mock_unload.assert_called_once_with(config_entry, PLATFORMS)
        
        # Check that time listeners were called
        for remove_listener in mock_runtime_data.remove_time_listeners:
            remove_listener.assert_called_once()
        
        # Check that entry was removed from hass_instance.data
        assert config_entry.entry_id not in hass_instance.data[DOMAIN]


@pytest.mark.asyncio
async def test_async_unload_entry_failed(
    hass_instance: HomeAssistant,
    mock_config_entry_data,
):
    """Test failed unload of config entry."""
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    config_entry.runtime_data = None

    with patch.object(hass_instance.config_entries, "async_unload_platforms") as mock_unload:
        mock_unload.return_value = False

        # Call the function under test
        result = await async_unload_entry(hass_instance, config_entry)

        # Assertions
        assert result is False
        mock_unload.assert_called_once_with(config_entry, PLATFORMS)


@pytest.mark.asyncio
async def test_update_listener(
    hass_instance: HomeAssistant,
    mock_config_entry_data,
):
    """Test config entry update listener."""
    # Create a mock config entry
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    
    # Mock runtime data
    mock_runtime_data = Mock()
    config_entry.runtime_data = mock_runtime_data

    with patch.object(hass_instance.config_entries, "async_reload") as mock_reload, \
         patch("custom_components.iopool.IopoolConfigData.from_config_entry") as mock_from_config:
        
        mock_new_config = Mock()
        mock_from_config.return_value = mock_new_config

        # Call the function under test
        await update_listener(hass_instance, config_entry)

        # Assertions
        mock_from_config.assert_called_once_with(config_entry)
        assert mock_runtime_data.config == mock_new_config
        mock_reload.assert_called_once_with(config_entry.entry_id)


@pytest.mark.asyncio
async def test_update_listener_no_runtime_data(
    hass_instance: HomeAssistant,
    mock_config_entry_data,
):
    """Test config entry update listener with no runtime data."""
    # Create a mock config entry without runtime data
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    config_entry.runtime_data = None

    with patch.object(hass_instance.config_entries, "async_reload") as mock_reload:
        # Call the function under test
        await update_listener(hass_instance, config_entry)

        # Assertions - should not fail and should still reload
        mock_reload.assert_called_once_with(config_entry.entry_id)


@pytest.mark.unit
def test_platforms_constant():
    """Test that PLATFORMS constant contains expected platforms."""
    expected_platforms = [Platform.SENSOR, Platform.SELECT, Platform.BINARY_SENSOR]
    assert PLATFORMS == expected_platforms
    # Ensure sensor comes before binary_sensor as noted in the code comment
    assert PLATFORMS.index(Platform.SENSOR) < PLATFORMS.index(Platform.BINARY_SENSOR)