"""Test the iopool select platform."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.core import HomeAssistant

from custom_components.iopool.select import (
    async_setup_entry,
    IopoolSelect,
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
    mock_filtration = Mock()
    mock_filtration.configuration_filtration_enabled = True  # Need this to be True
    mock_runtime_data.coordinator = mock_coordinator
    mock_runtime_data.filtration = mock_filtration
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
    assert "IopoolSelect" in entity_types


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
    mock_filtration = Mock()
    mock_filtration.configuration_filtration_enabled = False
    mock_runtime_data.coordinator = mock_coordinator
    mock_runtime_data.filtration = mock_filtration
    mock_runtime_data.config.options.filtration = {}
    config_entry.runtime_data = mock_runtime_data
    
    # Mock async_add_entities
    async_add_entities = AsyncMock()
    
    # Call the function
    await async_setup_entry(hass, config_entry, async_add_entities)
    
    # Verify entities were added (called once with empty list)
    async_add_entities.assert_called_once_with([])


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
    mock_filtration = Mock()
    mock_filtration.configuration_filtration_enabled = False
    mock_runtime_data.coordinator = mock_coordinator
    mock_runtime_data.filtration = mock_filtration
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


class TestIopoolSelect:
    """Test IopoolSelect class."""
    
    @pytest.fixture
    def mock_select_description(self):
        """Create a mock select description."""
        from homeassistant.components.select import SelectEntityDescription
        return SelectEntityDescription(
            key=SENSOR_BOOST_SELECTOR,
            translation_key=SENSOR_BOOST_SELECTOR,
            icon="mdi:plus-box-multiple",
        )
    
    @pytest.fixture 
    def iopool_select(self, mock_select_description):
        """Create an IopoolSelect instance."""
        coordinator = Mock()
        filtration = Mock()
        return IopoolSelect(
            coordinator=coordinator,
            filtration=filtration,
            description=mock_select_description,
            config_entry_id="test_entry",
            pool_id="test_pool_123",
            pool_name="Test Pool",
        )
    
    def test_select_initialization(self, iopool_select, mock_select_description):
        """Test select initialization."""
        assert iopool_select.entity_description == mock_select_description
        assert iopool_select._attr_unique_id == "test_entry_test_pool_123_boost_selector"
        assert iopool_select._pool_id == "test_pool_123"
    
    def test_select_options_boost(self):
        """Test select options for boost selector."""
        coordinator = Mock()
        filtration = Mock()
        from homeassistant.components.select import SelectEntityDescription
        description = SelectEntityDescription(
            key=SENSOR_BOOST_SELECTOR,
            translation_key=SENSOR_BOOST_SELECTOR,
        )
        iopool_select = IopoolSelect(
            coordinator=coordinator,
            filtration=filtration,
            description=description,
            config_entry_id="test_entry",
            pool_id="test_pool_123",
            pool_name="Test Pool",
        )
        assert iopool_select.options == BOOST_OPTIONS
    
    def test_select_options_pool_mode(self):
        """Test select options for pool mode selector."""
        coordinator = Mock()
        filtration = Mock()
        from homeassistant.components.select import SelectEntityDescription
        description = SelectEntityDescription(
            key=SENSOR_POOL_MODE,
            translation_key=SENSOR_POOL_MODE,
        )
        iopool_select = IopoolSelect(
            coordinator=coordinator,
            filtration=filtration,
            description=description,
            config_entry_id="test_entry",
            pool_id="test_pool_123",
            pool_name="Test Pool",
        )
        assert iopool_select.options == MODE_OPTIONS
    
    def test_select_options_unknown(self):
        """Test select options for unknown selector."""
        coordinator = Mock()
        filtration = Mock()
        from homeassistant.components.select import SelectEntityDescription
        description = SelectEntityDescription(
            key="unknown_key",
            translation_key="unknown_key",
        )
        iopool_select = IopoolSelect(
            coordinator=coordinator,
            filtration=filtration,
            description=description,
            config_entry_id="test_entry",
            pool_id="test_pool_123",
            pool_name="Test Pool",
        )
        assert iopool_select.options == []


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
    
    mock_coordinator.get_pool_data.return_value = pool_data
    mock_runtime_data.coordinator = mock_coordinator
    mock_filtration = Mock()
    mock_filtration.configuration_filtration_enabled = True
    mock_runtime_data.filtration = mock_filtration
    mock_runtime_data.config.options.filtration = {
        CONF_OPTIONS_FILTRATION_SWITCH_ENTITY: "switch.pool_pump"
    }
    config_entry.runtime_data = mock_runtime_data
    
    # Mock async_add_entities
    async_add_entities = AsyncMock()
    
    # Set up entities
    await async_setup_entry(hass, config_entry, async_add_entities)
    
    entities = async_add_entities.call_args[0][0]
    
    # Should have 2 select entities
    assert len(entities) == 2
    
    # Find the boost and mode selects
    boost_select = next(e for e in entities if e.entity_description.key == SENSOR_BOOST_SELECTOR)
    mode_select = next(e for e in entities if e.entity_description.key == SENSOR_POOL_MODE)
    
    # Test entity types
    assert isinstance(boost_select, IopoolSelect)
    assert isinstance(mode_select, IopoolSelect)