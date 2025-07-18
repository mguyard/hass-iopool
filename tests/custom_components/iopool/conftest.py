"""Common fixtures for iopool tests."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.iopool.const import CONF_API_KEY, CONF_POOL_ID, DOMAIN

# Test configuration data
TEST_API_KEY = "test_api_key_12345"
TEST_POOL_ID = "test_pool_123"
TEST_CONFIG = {
    CONF_API_KEY: TEST_API_KEY,
    CONF_POOL_ID: TEST_POOL_ID,
}

# Mock API response data (matches actual API structure)
MOCK_POOL_DATA = {
    "id": TEST_POOL_ID,
    "title": "Test Pool",
    "mode": "STANDARD",
    "hasAnActionRequired": False,
    "latestMeasure": {
        "temperature": 22.5,
        "ph": 7.2,
        "orp": 650,
        "mode": "standard",
        "isValid": True,
        "ecoId": "eco_123",
        "measuredAt": "2024-01-15T14:30:00Z",
    },
    "advice": {
        "filtrationDuration": 8.5,
    },
}

# API returns list of pools directly
MOCK_API_RESPONSE = [MOCK_POOL_DATA]


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MagicMock(
        data=TEST_CONFIG,
        options={},
        entry_id="test_entry",
        title="Test Pool",
        runtime_data=None,
    )


@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator."""
    from custom_components.iopool.api_models import IopoolAPIResponse
    
    coordinator = MagicMock()
    # Create proper API response object
    api_response = IopoolAPIResponse.from_dict(MOCK_API_RESPONSE)
    coordinator.data = api_response
    coordinator.last_update_success = True
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    
    # Mock get_pool_data to return the first pool
    def mock_get_pool_data(pool_id):
        if pool_id == TEST_POOL_ID and api_response.pools:
            return api_response.pools[0]
        return None
    
    coordinator.get_pool_data = mock_get_pool_data
    return coordinator


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session."""
    session = AsyncMock()
    response = AsyncMock()
    response.json.return_value = MOCK_API_RESPONSE
    response.status = 200
    session.get.return_value.__aenter__.return_value = response
    return session


@pytest.fixture
async def mock_hass():
    """Return a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_reload = AsyncMock()
    hass.bus = MagicMock()
    hass.bus.async_listen_once = MagicMock()
    hass.state = "running"
    return hass


@pytest.fixture
def mock_async_get_clientsession():
    """Mock the async_get_clientsession function."""
    with patch(
        "custom_components.iopool.coordinator.async_get_clientsession"
    ) as mock_session:
        yield mock_session