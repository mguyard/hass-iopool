"""Test the iopool binary sensor platform."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.iopool.binary_sensor import (
    async_setup_entry,
    IopoolBinarySensor,
    POOL_BINARY_SENSORS,
)
from custom_components.iopool.const import (
    CONF_POOL_ID,
    SENSOR_ACTION_REQUIRED,
)
from custom_components.iopool.models import IopoolConfigEntry


@pytest.mark.asyncio
async def test_async_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test successful binary sensor setup."""
    # Create mock config entry
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    
    # Create mock runtime data
    mock_runtime_data = Mock()
    mock_coordinator = Mock()
    mock_coordinator.get_pool_data.return_value = Mock(
        id="test_pool_123",
        title="Test Pool"
    )
    mock_runtime_data.coordinator = mock_coordinator
    mock_runtime_data.config.options.filtration = {}
    config_entry.runtime_data = mock_runtime_data
    
    # Mock async_add_entities
    async_add_entities = AsyncMock()
    
    # Call the function
    await async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify entities were added
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    
    # Should have 1 binary sensor (action required)
    assert len(entities) == 1
    
    # Check entity type
    for entity in entities:
        assert isinstance(entity, IopoolBinarySensor)


@pytest.mark.asyncio
async def test_async_setup_entry_no_pool(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test binary sensor setup when pool is not found."""
    # Create mock config entry
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    
    # Create mock runtime data with no pool data
    mock_runtime_data = Mock()
    mock_coordinator = Mock()
    mock_coordinator.get_pool_data.return_value = None
    mock_runtime_data.coordinator = mock_coordinator
    config_entry.runtime_data = mock_runtime_data
    
    # Mock async_add_entities
    async_add_entities = AsyncMock()
    
    # Call the function
    await async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify no entities were added
    async_add_entities.assert_not_called()


@pytest.mark.unit
def test_pool_binary_sensors_definitions():
    """Test that all required binary sensors are defined."""
    sensor_keys = [sensor.key for sensor in POOL_BINARY_SENSORS]
    
    expected_sensors = [
        SENSOR_ACTION_REQUIRED,
    ]
    
    for sensor in expected_sensors:
        assert sensor in sensor_keys


@pytest.mark.unit
def test_action_required_sensor_config():
    """Test action required sensor configuration."""
    action_sensor = next(s for s in POOL_BINARY_SENSORS if s.key == SENSOR_ACTION_REQUIRED)
    
    assert action_sensor.device_class == BinarySensorDeviceClass.PROBLEM
    assert action_sensor.icon == "mdi:gesture-tap-button"
    assert action_sensor.translation_key == SENSOR_ACTION_REQUIRED


class TestIopoolBinarySensor:
    """Test IopoolBinarySensor class."""
    
    @pytest.fixture
    def mock_binary_sensor_description(self):
        """Create a mock binary sensor description."""
        from homeassistant.components.binary_sensor import BinarySensorEntityDescription
        return BinarySensorEntityDescription(
            key=SENSOR_ACTION_REQUIRED,
            translation_key=SENSOR_ACTION_REQUIRED,
            icon="mdi:gesture-tap-button",
            device_class=BinarySensorDeviceClass.PROBLEM,
        )
    
    @pytest.fixture 
    def iopool_binary_sensor(self, mock_binary_sensor_description):
        """Create an IopoolBinarySensor instance."""
        coordinator = Mock()
        return IopoolBinarySensor(
            coordinator=coordinator,
            description=mock_binary_sensor_description,
            entry_id="test_entry",
            pool_id="test_pool_123",
            pool_title="Test Pool",
        )
    
    def test_binary_sensor_initialization(self, iopool_binary_sensor, mock_binary_sensor_description):
        """Test binary sensor initialization."""
        assert iopool_binary_sensor.entity_description == mock_binary_sensor_description
        assert iopool_binary_sensor._attr_unique_id == "test_entry_test_pool_123_action_required"
        assert iopool_binary_sensor._pool_id == "test_pool_123"
    
    def test_binary_sensor_is_on_true(self, iopool_binary_sensor):
        """Test binary sensor is_on property when action is required."""
        # Mock pool data with action required
        mock_pool = Mock()
        mock_pool.action_required = True
        
        iopool_binary_sensor.coordinator.get_pool_data.return_value = mock_pool
        
        # Test is_on property
        assert iopool_binary_sensor.is_on is True
    
    def test_binary_sensor_is_on_false(self, iopool_binary_sensor):
        """Test binary sensor is_on property when no action is required."""
        # Mock pool data with no action required
        mock_pool = Mock()
        mock_pool.action_required = False
        
        iopool_binary_sensor.coordinator.get_pool_data.return_value = mock_pool
        
        # Test is_on property
        assert iopool_binary_sensor.is_on is False
    
    def test_binary_sensor_no_pool_data(self, iopool_binary_sensor):
        """Test binary sensor when pool data is not available."""
        iopool_binary_sensor.coordinator.get_pool_data.return_value = None
        
        assert iopool_binary_sensor.is_on is None
    
    def test_binary_sensor_no_attribute_data(self, iopool_binary_sensor):
        """Test binary sensor when specific attribute is not available."""
        mock_pool = Mock()
        # Mock pool without action_required attribute
        del mock_pool.action_required
        
        iopool_binary_sensor.coordinator.get_pool_data.return_value = mock_pool
        
        assert iopool_binary_sensor.is_on is None


@pytest.mark.integration
async def test_binary_sensor_integration(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test binary sensor integration with coordinator."""
    # Create a more complete integration test
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    
    # Create mock runtime data
    mock_runtime_data = Mock()
    mock_coordinator = Mock()
    
    # Mock pool data that changes
    pool_data_action_required = Mock()
    pool_data_action_required.id = "test_pool_123"
    pool_data_action_required.title = "Test Pool"
    pool_data_action_required.action_required = True
    
    pool_data_no_action = Mock()
    pool_data_no_action.id = "test_pool_123"
    pool_data_no_action.title = "Test Pool"
    pool_data_no_action.action_required = False
    
    # Set up coordinator to return different data
    mock_coordinator.get_pool_data.side_effect = [
        pool_data_action_required,
        pool_data_no_action,
    ]
    
    mock_runtime_data.coordinator = mock_coordinator
    mock_runtime_data.config.options.filtration = {}
    config_entry.runtime_data = mock_runtime_data
    
    # Mock async_add_entities
    async_add_entities = AsyncMock()
    
    # Set up entities
    await async_setup_entry(hass, config_entry, async_add_entities)
    
    entities = async_add_entities.call_args[0][0]
    binary_sensor = entities[0]
    
    # Test initial state (action required)
    assert binary_sensor.is_on is True
    
    # Test state change (no action required)
    assert binary_sensor.is_on is False