"""Test configuration and fixtures for iopool integration."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from custom_components.iopool.api_models import IopoolAPIResponse, IopoolAPIResponsePool
from custom_components.iopool.const import CONF_POOL_ID, DOMAIN
from custom_components.iopool.coordinator import IopoolDataUpdateCoordinator
import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


@pytest.fixture
def hass():
    """Create a HomeAssistant instance for testing."""
    hass_mock = MagicMock(spec=HomeAssistant)

    # Add required attributes for basic functionality
    hass_mock.data = {}
    hass_mock.loop = asyncio.get_event_loop()

    # Add required data for Home Assistant components
    hass_mock.data["network"] = MagicMock()
    hass_mock.data["network"].adapters = []

    # Add config with language attribute for sensor tests
    hass_mock.config = MagicMock()
    hass_mock.config.language = "en"

    # Add states for entity state management
    hass_mock.states = MagicMock()
    hass_mock.states.get = MagicMock()
    hass_mock.states.async_set = MagicMock()

    # Add bus for event handling
    hass_mock.bus = MagicMock()
    hass_mock.bus.fire = MagicMock()

    # Add config entries for flow management
    hass_mock.config_entries = MagicMock()
    hass_mock.config_entries.flow = MagicMock()
    # Return a clean form for initial async_init calls
    hass_mock.config_entries.flow.async_init = AsyncMock(
        return_value={
            "type": FlowResultType.FORM,
            "step_id": "user",
            "errors": {},
            "flow_id": "test_flow_id",
        }
    )
    # Return success for async_configure by default (individual tests can override)
    hass_mock.config_entries.flow.async_configure = AsyncMock(
        return_value={
            "type": FlowResultType.FORM,
            "step_id": "choose_pool",
            "errors": {},
            "flow_id": "test_flow_id",
        }
    )

    # Add async methods that can be awaited
    hass_mock.async_add_executor_job = AsyncMock()
    hass_mock.async_create_task = AsyncMock()

    return hass_mock


# Constants
TEST_API_KEY = "test-api-key-12345"
TEST_POOL_ID = "test_pool_id_67890"
TEST_POOL_TITLE = "Test Pool"

# Mock pools API response data (based on real API structure)
MOCK_POOLS_API_RESPONSE = [
    {
        "id": "test_pool_id_67890",
        "title": "Test Pool",
        "latestMeasure": {
            "temperature": 25.5,
            "ph": 7.2,
            "orp": 750,
            "mode": "gateway",
            "isValid": True,
            "ecoId": "eco456",
            "measuredAt": "2024-01-01T12:00:00Z",
        },
        "mode": "STANDARD",
        "hasAnActionRequired": False,
        "advice": {"filtrationDuration": 8.5},
    }
]


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session with proper async context manager support."""
    session = AsyncMock()

    # Create a proper mock response
    response_mock = AsyncMock()
    response_mock.status = 200
    response_mock.json = AsyncMock(return_value=MOCK_POOLS_API_RESPONSE)
    response_mock.raise_for_status = AsyncMock()

    # Create a proper context manager
    context_manager = AsyncMock()
    context_manager.__aenter__ = AsyncMock(return_value=response_mock)
    context_manager.__aexit__ = AsyncMock(return_value=None)

    # Assign the context manager to session.get
    session.get = MagicMock(return_value=context_manager)

    return session


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {
        CONF_API_KEY: TEST_API_KEY,
        CONF_POOL_ID: TEST_POOL_ID,
    }
    entry.entry_id = "test_entry_id"
    entry.title = TEST_POOL_TITLE
    entry.domain = DOMAIN

    # Add runtime_data with proper structure
    runtime_data = MagicMock()
    runtime_data.coordinator = MagicMock()
    runtime_data.config = MagicMock()
    runtime_data.filtration = MagicMock()

    # Add required attributes to config
    runtime_data.config.pool_id = TEST_POOL_ID
    runtime_data.config.summer_mode = True
    runtime_data.config.winter_mode = False
    runtime_data.config.ph_max = 7.6
    runtime_data.config.ph_min = 7.2
    runtime_data.config.orp_max = 650
    runtime_data.config.orp_min = 550
    runtime_data.config.temp_max = 28.0
    runtime_data.config.temp_min = 10.0

    # Add required attributes to filtration
    runtime_data.filtration.is_running = False
    runtime_data.filtration.enabled = True
    runtime_data.filtration.async_start_filtration = AsyncMock()
    runtime_data.filtration.async_stop_filtration = AsyncMock()
    runtime_data.filtration.publish_event = AsyncMock()
    runtime_data.filtration.get_switch_entity = MagicMock(
        return_value="switch.pool_pump"
    )
    runtime_data.filtration.get_filtration_pool_mode = MagicMock(
        return_value="Standard"
    )
    runtime_data.filtration.configuration_filtration_enabled = True
    runtime_data.filtration.configuration_filtration_enabled_summer = True
    runtime_data.filtration.configuration_filtration_enabled_winter = False
    runtime_data.filtration.get_summer_filtration_duration = MagicMock(return_value=8.5)

    # Add config_entry to coordinator for binary sensor
    runtime_data.coordinator.config_entry = entry

    entry.runtime_data = runtime_data

    return entry


@pytest.fixture
def mock_api_response():
    """Mock API response with pool data."""
    return IopoolAPIResponse.from_dict(MOCK_POOLS_API_RESPONSE)


@pytest.fixture
def mock_api_response_no_pools():
    """Mock API response with no pools."""
    return IopoolAPIResponse([])


@pytest.fixture
def mock_pool_data():
    """Mock pool data."""
    return IopoolAPIResponsePool.from_dict(MOCK_POOLS_API_RESPONSE[0])


@pytest.fixture
def mock_iopool_coordinator(hass, mock_config_entry, mock_api_response):
    """Mock iopool coordinator with test data."""
    coordinator = MagicMock(spec=IopoolDataUpdateCoordinator)
    coordinator.hass = hass
    coordinator.data = mock_api_response
    coordinator.config_entry = mock_config_entry
    coordinator.get_pool_data = MagicMock(return_value=mock_api_response.pools[0])

    return coordinator
