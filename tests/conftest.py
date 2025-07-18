"""Test fixtures for iopool integration."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.iopool.const import DOMAIN, CONF_API_KEY, CONF_POOL_ID
from custom_components.iopool.api_models import IopoolAPIResponse, IopoolAPIResponsePool

# Use proper HomeAssistant fixture from pytest-homeassistant-custom-component

@pytest.fixture
def hass_instance():
    """Return a mock HomeAssistant instance for testing config flow."""
    mock_hass = Mock()
    
    # Mock config_entries and flow
    mock_hass.config_entries = Mock()
    mock_hass.config_entries.flow = Mock()
    mock_hass.config_entries.flow.async_init = AsyncMock()
    mock_hass.config_entries.flow.async_configure = AsyncMock()
    mock_hass.config_entries.async_entries = Mock(return_value=[])
    
    # Mock data attribute for coordinator tests
    mock_hass.data = {}
    
    return mock_hass




@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "test_api_key_12345"


@pytest.fixture
def mock_pool_id():
    """Mock pool ID for testing."""
    return "test_pool_123"


@pytest.fixture
def mock_config_entry_data(mock_api_key, mock_pool_id):
    """Mock config entry data."""
    return {
        CONF_API_KEY: mock_api_key,
        CONF_POOL_ID: mock_pool_id,
    }


@pytest.fixture
def mock_pool_data():
    """Mock pool data from API."""
    return {
        "id": "test_pool_123",
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
            "measuredAt": "2024-01-01T12:00:00Z"
        },
        "advice": {
            "ph": {"value": 7.2, "status": "OK"},
            "orp": {"value": 650, "status": "OK"},
            "temperature": {"value": 22.5, "status": "OK"}
        }
    }


@pytest.fixture
def mock_api_response(mock_pool_data):
    """Mock API response."""
    return [mock_pool_data]


@pytest.fixture
def mock_iopool_api_response(mock_api_response):
    """Mock IopoolAPIResponse object."""
    return IopoolAPIResponse.from_dict(mock_api_response)


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session."""
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session_func:
        # Create a mock session that properly handles async context manager
        mock_session = Mock()
        
        # Mock the get method to return an async context manager
        mock_get_context = AsyncMock()
        mock_session.get.return_value = mock_get_context
        
        # This will be set up in individual tests to return the appropriate response
        mock_get_context.__aenter__ = AsyncMock()
        mock_get_context.__aexit__ = AsyncMock()
        
        mock_session.close = AsyncMock()
        mock_session.connector = Mock()
        mock_session.connector.close = AsyncMock()
        
        mock_session_func.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_coordinator_update():
    """Mock coordinator update."""
    with patch("custom_components.iopool.coordinator.IopoolDataUpdateCoordinator._async_update_data") as mock_update:
        yield mock_update


@pytest.fixture
def mock_time_event():
    """Mock time event functionality."""
    with patch("homeassistant.util.dt.now") as mock_now, \
         patch("homeassistant.helpers.event.async_track_time_interval") as mock_track:
        yield mock_now, mock_track