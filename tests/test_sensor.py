"""Test the iopool sensor platform."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfTemperature, UnitOfTime

from custom_components.iopool.sensor import (
    async_setup_entry,
    IopoolSensor,
    POOL_SENSORS,
)
from custom_components.iopool.const import (
    CONF_POOL_ID,
    SENSOR_TEMPERATURE,
    SENSOR_PH,
    SENSOR_ORP,
    SENSOR_FILTRATION_RECOMMENDATION,
    SENSOR_IOPOOL_MODE,
)
from custom_components.iopool.models import IopoolConfigEntry


@pytest.mark.asyncio
async def test_async_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry_data,
    mock_pool_data,
    mock_iopool_api_response,
):
    """Test successful sensor setup."""
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
    
    # Should have 5 entities (temperature, pH, ORP, filtration recommendation, iopool mode)
    assert len(entities) == 5
    
    # Check entity types
    for entity in entities:
        assert isinstance(entity, IopoolSensor)


@pytest.mark.asyncio
async def test_async_setup_entry_no_pool(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test sensor setup when pool is not found."""
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


@pytest.mark.asyncio
async def test_async_setup_entry_with_switch_entity(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test sensor setup with switch entity configured."""
    # Create mock config entry with switch entity
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    
    # Create mock runtime data with switch entity
    mock_runtime_data = Mock()
    mock_coordinator = Mock()
    mock_coordinator.get_pool_data.return_value = Mock(
        id="test_pool_123",
        title="Test Pool"
    )
    mock_runtime_data.coordinator = mock_coordinator
    mock_runtime_data.config.options.filtration = {
        "switch_entity": "switch.pool_pump"
    }
    config_entry.runtime_data = mock_runtime_data
    
    # Mock async_add_entities
    async_add_entities = AsyncMock()
    
    with patch("custom_components.iopool.sensor.HistoryStatsUpdateCoordinator"), \
         patch("custom_components.iopool.sensor.HistoryStats"), \
         patch("custom_components.iopool.sensor.HistoryStatsSensor"), \
         patch("homeassistant.helpers.template.Template"):
        
        # Call the function
        await async_setup_entry(hass, config_entry, async_add_entities)
        
        # Verify entities were added (should be called twice: once for main sensors, once for history sensor)
        assert async_add_entities.call_count == 2


@pytest.mark.unit
def test_pool_sensors_definitions():
    """Test that all required sensors are defined."""
    sensor_keys = [sensor.key for sensor in POOL_SENSORS]
    
    expected_sensors = [
        SENSOR_TEMPERATURE,
        SENSOR_PH, 
        SENSOR_ORP,
        SENSOR_FILTRATION_RECOMMENDATION,
        SENSOR_IOPOOL_MODE,
    ]
    
    for sensor in expected_sensors:
        assert sensor in sensor_keys


@pytest.mark.unit
def test_temperature_sensor_config():
    """Test temperature sensor configuration."""
    temp_sensor = next(s for s in POOL_SENSORS if s.key == SENSOR_TEMPERATURE)
    
    assert temp_sensor.device_class.value == "temperature"
    assert temp_sensor.state_class.value == "measurement"
    assert temp_sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert temp_sensor.suggested_display_precision == 2


@pytest.mark.unit
def test_ph_sensor_config():
    """Test pH sensor configuration."""
    ph_sensor = next(s for s in POOL_SENSORS if s.key == SENSOR_PH)
    
    assert ph_sensor.state_class.value == "measurement"
    assert ph_sensor.suggested_display_precision == 2
    assert ph_sensor.icon == "mdi:alpha-p-box-outline"


@pytest.mark.unit
def test_orp_sensor_config():
    """Test ORP sensor configuration."""
    orp_sensor = next(s for s in POOL_SENSORS if s.key == SENSOR_ORP)
    
    assert orp_sensor.state_class.value == "measurement"
    assert orp_sensor.native_unit_of_measurement == "mV"
    assert orp_sensor.icon == "mdi:alpha-o-box-outline"


@pytest.mark.unit
def test_filtration_recommendation_sensor_config():
    """Test filtration recommendation sensor configuration."""
    filtration_sensor = next(s for s in POOL_SENSORS if s.key == SENSOR_FILTRATION_RECOMMENDATION)
    
    assert filtration_sensor.device_class.value == "duration"
    assert filtration_sensor.state_class.value == "measurement"
    assert filtration_sensor.native_unit_of_measurement == UnitOfTime.MINUTES
    assert filtration_sensor.icon == "mdi:clock-time-two-outline"


@pytest.mark.unit
def test_iopool_mode_sensor_config():
    """Test iopool mode sensor configuration."""
    mode_sensor = next(s for s in POOL_SENSORS if s.key == SENSOR_IOPOOL_MODE)
    
    assert mode_sensor.icon == "mdi:auto-mode"
    # Mode sensor should not have device_class or state_class for non-numeric values
    assert mode_sensor.device_class is None
    assert mode_sensor.state_class is None


class TestIopoolSensor:
    """Test IopoolSensor class."""
    
    @pytest.fixture
    def mock_sensor_description(self):
        """Create a mock sensor description."""
        from homeassistant.components.sensor import SensorEntityDescription
        return SensorEntityDescription(
            key=SENSOR_TEMPERATURE,
            translation_key=SENSOR_TEMPERATURE,
            icon="mdi:thermometer",
        )
    
    @pytest.fixture 
    def iopool_sensor(self, mock_sensor_description):
        """Create an IopoolSensor instance."""
        coordinator = Mock()
        return IopoolSensor(
            coordinator=coordinator,
            description=mock_sensor_description,
            entry_id="test_entry",
            pool_id="test_pool_123",
            pool_title="Test Pool",
        )
    
    def test_sensor_initialization(self, iopool_sensor, mock_sensor_description):
        """Test sensor initialization."""
        assert iopool_sensor.entity_description == mock_sensor_description
        assert iopool_sensor._attr_unique_id == "test_entry_test_pool_123_temperature"
        assert iopool_sensor._pool_id == "test_pool_123"
    
    def test_sensor_properties(self, iopool_sensor):
        """Test sensor properties."""
        # Mock pool data
        mock_pool = Mock()
        mock_pool.temperature = Mock(value=25.5, is_valid=True, measured_at="2024-01-01T12:00:00Z")
        
        iopool_sensor.coordinator.get_pool_data.return_value = mock_pool
        
        # Test native_value property
        assert iopool_sensor.native_value == 25.5
        
        # Test extra_state_attributes
        attributes = iopool_sensor.extra_state_attributes
        assert attributes["is_valid"] is True
        assert attributes["measured_at"] == "2024-01-01T12:00:00Z"
    
    def test_sensor_no_pool_data(self, iopool_sensor):
        """Test sensor when pool data is not available."""
        iopool_sensor.coordinator.get_pool_data.return_value = None
        
        assert iopool_sensor.native_value is None
        assert iopool_sensor.extra_state_attributes == {}
    
    def test_sensor_no_attribute_data(self, iopool_sensor):
        """Test sensor when specific attribute is not available."""
        mock_pool = Mock()
        # Mock pool without temperature attribute
        del mock_pool.temperature
        
        iopool_sensor.coordinator.get_pool_data.return_value = mock_pool
        
        assert iopool_sensor.native_value is None
        assert iopool_sensor.extra_state_attributes == {}