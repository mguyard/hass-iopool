"""Test the iopool select platform."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.core import HomeAssistant

from custom_components.iopool.select import (
    async_setup_entry,
    IopoolBoostSelect,
    IopoolPoolModeSelect,
    POOL_SELECTS_CONDITIONAL_FILTRATION,
    BOOST_OPTIONS,
    MODE_OPTIONS,
)
from custom_components.iopool.const import (
    CONF_POOL_ID,
    SENSOR_BOOST_SELECTOR,
    SENSOR_POOL_MODE,
    CONF_OPTIONS_FILTRATION_SWITCH_ENTITY,
)
from custom_components.iopool.models import IopoolConfigEntry


@pytest.mark.asyncio
async def test_async_setup_entry_with_filtration(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test select setup with filtration switch entity configured."""
    # Create mock config entry with filtration enabled
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
        CONF_OPTIONS_FILTRATION_SWITCH_ENTITY: "switch.pool_pump"
    }
    config_entry.runtime_data = mock_runtime_data
    
    # Mock async_add_entities
    async_add_entities = AsyncMock()
    
    # Call the function
    await async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify entities were added
    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    
    # Should have 2 select entities (boost selector and pool mode)
    assert len(entities) == 2
    
    # Check entity types
    entity_types = [type(entity).__name__ for entity in entities]
    assert "IopoolBoostSelect" in entity_types
    assert "IopoolPoolModeSelect" in entity_types


@pytest.mark.asyncio
async def test_async_setup_entry_without_filtration(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test select setup without filtration switch entity configured."""
    # Create mock config entry without filtration
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    
    # Create mock runtime data without switch entity
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
    
    # Verify no entities were added
    async_add_entities.assert_not_called()


@pytest.mark.asyncio
async def test_async_setup_entry_no_pool(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test select setup when pool is not found."""
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
def test_pool_selects_definitions():
    """Test that all required select entities are defined."""
    select_keys = [select.key for select in POOL_SELECTS_CONDITIONAL_FILTRATION]
    
    expected_selects = [
        SENSOR_BOOST_SELECTOR,
        SENSOR_POOL_MODE,
    ]
    
    for select in expected_selects:
        assert select in select_keys


@pytest.mark.unit
def test_boost_selector_config():
    """Test boost selector configuration."""
    boost_select = next(s for s in POOL_SELECTS_CONDITIONAL_FILTRATION if s.key == SENSOR_BOOST_SELECTOR)
    
    assert boost_select.icon == "mdi:plus-box-multiple"
    assert boost_select.translation_key == SENSOR_BOOST_SELECTOR


@pytest.mark.unit
def test_pool_mode_selector_config():
    """Test pool mode selector configuration."""
    mode_select = next(s for s in POOL_SELECTS_CONDITIONAL_FILTRATION if s.key == SENSOR_POOL_MODE)
    
    assert mode_select.icon == "mdi:sun-snowflake-variant"
    assert mode_select.translation_key == SENSOR_POOL_MODE


@pytest.mark.unit
def test_boost_options():
    """Test boost options constant."""
    expected_options = ["None", "1H", "4H", "8H", "24H"]
    assert BOOST_OPTIONS == expected_options


@pytest.mark.unit
def test_mode_options():
    """Test mode options constant."""
    expected_options = ["Standard", "Active-Winter", "Passive-Winter"]
    assert MODE_OPTIONS == expected_options


class TestIopoolBoostSelect:
    """Test IopoolBoostSelect class."""
    
    @pytest.fixture
    def mock_boost_select_description(self):
        """Create a mock boost select description."""
        from homeassistant.components.select import SelectEntityDescription
        return SelectEntityDescription(
            key=SENSOR_BOOST_SELECTOR,
            translation_key=SENSOR_BOOST_SELECTOR,
            icon="mdi:plus-box-multiple",
        )
    
    @pytest.fixture 
    def iopool_boost_select(self, mock_boost_select_description):
        """Create an IopoolBoostSelect instance."""
        coordinator = Mock()
        entry = Mock()
        entry.runtime_data.filtration = Mock()
        return IopoolBoostSelect(
            coordinator=coordinator,
            description=mock_boost_select_description,
            entry_id="test_entry",
            pool_id="test_pool_123",
            pool_title="Test Pool",
            entry=entry,
        )
    
    def test_boost_select_initialization(self, iopool_boost_select, mock_boost_select_description):
        """Test boost select initialization."""
        assert iopool_boost_select.entity_description == mock_boost_select_description
        assert iopool_boost_select._attr_unique_id == "test_entry_test_pool_123_boost_selector"
        assert iopool_boost_select._pool_id == "test_pool_123"
        assert iopool_boost_select.options == BOOST_OPTIONS
    
    def test_boost_select_current_option_none(self, iopool_boost_select):
        """Test boost select current option when no boost is active."""
        iopool_boost_select._boost_end_time = None
        
        assert iopool_boost_select.current_option == "None"
    
    def test_boost_select_current_option_active(self, iopool_boost_select):
        """Test boost select current option when boost is active."""
        # Mock an active boost
        from datetime import datetime, timedelta
        import homeassistant.util.dt as dt_util
        
        future_time = dt_util.now() + timedelta(hours=2)
        iopool_boost_select._boost_end_time = future_time
        
        assert iopool_boost_select.current_option != "None"


class TestIopoolPoolModeSelect:
    """Test IopoolPoolModeSelect class."""
    
    @pytest.fixture
    def mock_mode_select_description(self):
        """Create a mock mode select description."""
        from homeassistant.components.select import SelectEntityDescription
        return SelectEntityDescription(
            key=SENSOR_POOL_MODE,
            translation_key=SENSOR_POOL_MODE,
            icon="mdi:sun-snowflake-variant",
        )
    
    @pytest.fixture 
    def iopool_mode_select(self, mock_mode_select_description):
        """Create an IopoolPoolModeSelect instance."""
        coordinator = Mock()
        return IopoolPoolModeSelect(
            coordinator=coordinator,
            description=mock_mode_select_description,
            entry_id="test_entry",
            pool_id="test_pool_123",
            pool_title="Test Pool",
        )
    
    def test_mode_select_initialization(self, iopool_mode_select, mock_mode_select_description):
        """Test mode select initialization."""
        assert iopool_mode_select.entity_description == mock_mode_select_description
        assert iopool_mode_select._attr_unique_id == "test_entry_test_pool_123_pool_mode"
        assert iopool_mode_select._pool_id == "test_pool_123"
        assert iopool_mode_select.options == MODE_OPTIONS
    
    def test_mode_select_current_option_standard(self, iopool_mode_select):
        """Test mode select current option for standard mode."""
        # Mock pool data with standard mode
        mock_pool = Mock()
        mock_pool.mode = "normal"
        mock_pool.eco_mode = "auto"
        
        iopool_mode_select.coordinator.get_pool_data.return_value = mock_pool
        
        assert iopool_mode_select.current_option == "Standard"
    
    def test_mode_select_current_option_no_pool_data(self, iopool_mode_select):
        """Test mode select current option when pool data is not available."""
        iopool_mode_select.coordinator.get_pool_data.return_value = None
        
        assert iopool_mode_select.current_option is None


@pytest.mark.integration
async def test_select_entities_integration(
    hass: HomeAssistant,
    mock_config_entry_data,
):
    """Test select entities integration."""
    # Create config entry with filtration
    config_entry = Mock(spec=IopoolConfigEntry)
    config_entry.data = mock_config_entry_data
    config_entry.entry_id = "test_entry_id"
    
    # Create mock runtime data
    mock_runtime_data = Mock()
    mock_coordinator = Mock()
    
    # Mock pool data
    pool_data = Mock()
    pool_data.id = "test_pool_123"
    pool_data.title = "Test Pool"
    pool_data.mode = "normal"
    pool_data.eco_mode = "auto"
    
    mock_coordinator.get_pool_data.return_value = pool_data
    mock_runtime_data.coordinator = mock_coordinator
    mock_runtime_data.config.options.filtration = {
        CONF_OPTIONS_FILTRATION_SWITCH_ENTITY: "switch.pool_pump"
    }
    mock_runtime_data.filtration = Mock()
    config_entry.runtime_data = mock_runtime_data
    
    # Mock async_add_entities
    async_add_entities = AsyncMock()
    
    # Set up entities
    await async_setup_entry(hass, config_entry, async_add_entities)
    
    entities = async_add_entities.call_args[0][0]
    
    # Find the boost and mode selects
    boost_select = next(e for e in entities if e.entity_description.key == SENSOR_BOOST_SELECTOR)
    mode_select = next(e for e in entities if e.entity_description.key == SENSOR_POOL_MODE)
    
    # Test initial states
    assert boost_select.current_option == "None"
    assert mode_select.current_option == "Standard"