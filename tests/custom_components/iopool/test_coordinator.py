"""Test the iopool coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.client_exceptions import ClientError

from custom_components.iopool.coordinator import IopoolDataUpdateCoordinator
from custom_components.iopool.const import DOMAIN
from custom_components.iopool.api_models import IopoolAPIResponse

from .conftest import MOCK_API_RESPONSE, TEST_API_KEY, TEST_POOL_ID


class TestIopoolDataUpdateCoordinator:
    """Test the IopoolDataUpdateCoordinator class."""

    @pytest.fixture
    async def coordinator(self, mock_hass, mock_aiohttp_session):
        """Create a coordinator instance for testing."""
        with patch(
            "custom_components.iopool.coordinator.async_get_clientsession",
            return_value=mock_aiohttp_session,
        ):
            coordinator = IopoolDataUpdateCoordinator(mock_hass, TEST_API_KEY)
            return coordinator

    async def test_coordinator_init(self, coordinator, mock_hass):
        """Test coordinator initialization."""
        assert coordinator.api_key == TEST_API_KEY
        assert coordinator.headers == {"x-api-key": TEST_API_KEY}
        assert coordinator.hass == mock_hass
        assert coordinator.name == DOMAIN

    async def test_get_pool_data_success(self, coordinator):
        """Test successful pool data retrieval."""
        api_response = IopoolAPIResponse.from_dict(MOCK_API_RESPONSE)
        coordinator.data = api_response
        
        result = coordinator.get_pool_data(TEST_POOL_ID)
        
        assert result is not None
        assert result.id == TEST_POOL_ID
        assert result.title == "Test Pool"

    async def test_get_pool_data_not_found(self, coordinator):
        """Test pool data retrieval when pool not found."""
        api_response = IopoolAPIResponse.from_dict(MOCK_API_RESPONSE)
        coordinator.data = api_response
        
        result = coordinator.get_pool_data("nonexistent_pool")
        
        assert result is None

    async def test_get_pool_data_no_data(self, coordinator):
        """Test pool data retrieval when no data available."""
        coordinator.data = None
        
        result = coordinator.get_pool_data(TEST_POOL_ID)
        
        assert result is None

    async def test_get_pool_data_empty_pools(self, coordinator):
        """Test pool data retrieval when pools list is empty."""
        coordinator.data = IopoolAPIResponse(pools=[])
        
        result = coordinator.get_pool_data(TEST_POOL_ID)
        
        assert result is None

    async def test_update_data_success(self, coordinator, mock_aiohttp_session):
        """Test successful data update."""
        response_mock = AsyncMock()
        response_mock.json.return_value = MOCK_API_RESPONSE
        response_mock.status = 200
        response_mock.raise_for_status = AsyncMock()
        mock_aiohttp_session.get.return_value.__aenter__.return_value = response_mock
        
        result = await coordinator._async_update_data()
        
        assert isinstance(result, IopoolAPIResponse)
        assert len(result.pools) == 1
        assert result.pools[0].id == TEST_POOL_ID
        mock_aiohttp_session.get.assert_called_once()

    async def test_update_data_client_error(self, coordinator, mock_aiohttp_session):
        """Test data update with client error."""
        from homeassistant.helpers.update_coordinator import UpdateFailed
        
        mock_aiohttp_session.get.side_effect = ClientError("Connection failed")
        
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_update_data_http_error(self, coordinator, mock_aiohttp_session):
        """Test data update with HTTP error."""
        from homeassistant.helpers.update_coordinator import UpdateFailed
        
        response_mock = AsyncMock()
        response_mock.raise_for_status.side_effect = Exception("HTTP 404")
        mock_aiohttp_session.get.return_value.__aenter__.return_value = response_mock
        
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_update_data_invalid_json(self, coordinator, mock_aiohttp_session):
        """Test data update with invalid JSON response."""
        from homeassistant.helpers.update_coordinator import UpdateFailed
        
        response_mock = AsyncMock()
        response_mock.raise_for_status = AsyncMock()
        response_mock.json.side_effect = ValueError("Invalid JSON")
        mock_aiohttp_session.get.return_value.__aenter__.return_value = response_mock
        
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_coordinator_headers(self, coordinator):
        """Test that coordinator sets correct headers."""
        expected_headers = {"x-api-key": TEST_API_KEY}
        assert coordinator.headers == expected_headers