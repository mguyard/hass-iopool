"""Test the iopool coordinator."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from aiohttp import ClientError
import aioresponses
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.iopool.coordinator import IopoolDataUpdateCoordinator
from custom_components.iopool.const import POOLS_ENDPOINT, DEFAULT_SCAN_INTERVAL
from custom_components.iopool.api_models import IopoolAPIResponse


@pytest.mark.asyncio
async def test_coordinator_init(hass: HomeAssistant, mock_api_key, mock_aiohttp_session):
    """Test coordinator initialization."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    
    assert coordinator.api_key == mock_api_key
    assert coordinator.headers == {"x-api-key": mock_api_key}
    assert coordinator.hass is hass
    assert coordinator.update_interval == DEFAULT_SCAN_INTERVAL


@pytest.mark.asyncio
async def test_coordinator_update_data_success(
    hass: HomeAssistant,
    mock_api_key,
    mock_api_response,
):
    """Test successful data update."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, payload=mock_api_response)
        
        result = await coordinator._async_update_data()
        
        assert isinstance(result, IopoolAPIResponse)
        assert len(result.pools) == 1
        assert result.pools[0].id == "test_pool_123"


@pytest.mark.asyncio
async def test_coordinator_update_data_client_error(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test data update with client error."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, exception=ClientError("Connection failed"))
        
        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_update_data_timeout(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test data update with timeout error."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, exception=TimeoutError("Request timed out"))
        
        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_update_data_json_error(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test data update with JSON parsing error."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, payload="invalid_json", content_type='text/plain')
        
        with pytest.raises(UpdateFailed, match="Error parsing API response"):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_update_data_key_error(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test data update with key error in response."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    
    # Invalid response structure missing required fields
    invalid_response = {"invalid": "structure"}
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, payload=invalid_response)
        
        with pytest.raises(UpdateFailed, match="Error parsing API response"):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_get_pool_data_found(
    hass: HomeAssistant,
    mock_api_key,
    mock_pool_id,
    mock_iopool_api_response,
):
    """Test getting pool data when pool exists."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    coordinator.data = mock_iopool_api_response
    
    result = coordinator.get_pool_data(mock_pool_id)
    
    assert result is not None
    assert result.id == mock_pool_id


@pytest.mark.asyncio
async def test_coordinator_get_pool_data_not_found(
    hass: HomeAssistant,
    mock_api_key,
    mock_iopool_api_response,
):
    """Test getting pool data when pool doesn't exist."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    coordinator.data = mock_iopool_api_response
    
    result = coordinator.get_pool_data("nonexistent_pool")
    
    assert result is None


@pytest.mark.asyncio
async def test_coordinator_get_pool_data_no_data(
    hass: HomeAssistant,
    mock_api_key,
    mock_pool_id,
):
    """Test getting pool data when no data is available."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    coordinator.data = None
    
    result = coordinator.get_pool_data(mock_pool_id)
    
    assert result is None


@pytest.mark.asyncio
async def test_coordinator_get_pool_data_empty_pools(
    hass: HomeAssistant,
    mock_api_key,
    mock_pool_id,
):
    """Test getting pool data when pools list is empty."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    
    # Create empty response
    empty_response = IopoolAPIResponse.from_dict({"pools": []})
    coordinator.data = empty_response
    
    result = coordinator.get_pool_data(mock_pool_id)
    
    assert result is None


@pytest.mark.asyncio
async def test_coordinator_headers_property(hass: HomeAssistant, mock_api_key):
    """Test that headers are correctly set."""
    coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
    
    expected_headers = {"x-api-key": mock_api_key}
    assert coordinator.headers == expected_headers


@pytest.mark.asyncio 
async def test_coordinator_session_property(hass: HomeAssistant, mock_api_key):
    """Test that session is correctly initialized."""
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session:
        mock_client = Mock()
        mock_session.return_value = mock_client
        
        coordinator = IopoolDataUpdateCoordinator(hass, mock_api_key)
        
        assert coordinator.session is mock_client
        mock_session.assert_called_once_with(hass)