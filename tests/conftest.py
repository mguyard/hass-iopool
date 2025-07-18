"""Test fixtures for iopool integration."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from custom_components.iopool.const import DOMAIN, CONF_API_KEY, CONF_POOL_ID
from custom_components.iopool.api_models import IopoolAPIResponse, IopoolAPIResponsePool


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
        "poolId": "test_pool_123",
        "name": "Test Pool",
        "hasAnECO": True,
        "isECOConnected": True,
        "ecoMode": "auto",
        "mode": "normal",
        "ph": {"value": 7.2, "isValid": True, "measuredAt": "2024-01-01T12:00:00Z"},
        "orp": {"value": 650, "isValid": True, "measuredAt": "2024-01-01T12:00:00Z"},
        "temperature": {"value": 22.5, "isValid": True, "measuredAt": "2024-01-01T12:00:00Z"},
        "actionRequired": False,
        "filtrationRecommendation": {"hours": 8, "reason": "temperature"},
    }


@pytest.fixture
def mock_api_response(mock_pool_data):
    """Mock API response."""
    return {
        "pools": [mock_pool_data]
    }


@pytest.fixture
def mock_iopool_api_response(mock_api_response):
    """Mock IopoolAPIResponse object."""
    return IopoolAPIResponse.from_dict(mock_api_response)


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session."""
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session:
        mock_client = Mock()
        mock_session.return_value = mock_client
        yield mock_client


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