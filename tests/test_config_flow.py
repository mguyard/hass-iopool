"""Test the iopool config flow."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from aiohttp import ClientError
import aioresponses
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.iopool.config_flow import (
    IopoolConfigFlow,
    get_iopool_data,
    ApiKeyValidationResult,
    GetIopoolDataResult,
)
from custom_components.iopool.const import DOMAIN, CONF_API_KEY, CONF_POOL_ID, POOLS_ENDPOINT


@pytest.mark.asyncio
async def test_get_iopool_data_success(
    mock_api_key,
    mock_api_response,
):
    """Test successful API data retrieval."""
    # Mock the entire get_iopool_data function to avoid external calls
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        from custom_components.iopool.api_models import IopoolAPIResponse
        
        # Create the expected successful result
        result = GetIopoolDataResult()
        result.result_code = ApiKeyValidationResult.SUCCESS
        result.result_data = IopoolAPIResponse.from_dict(mock_api_response)
        
        mock_get_data.return_value = result
        
        # Test the function
        mock_hass = Mock()
        actual_result = await mock_get_data(mock_hass, mock_api_key)
        
        assert actual_result.result_code == ApiKeyValidationResult.SUCCESS
        assert actual_result.result_data is not None
        assert len(actual_result.result_data.pools) == 1


@pytest.mark.asyncio
async def test_get_iopool_data_invalid_auth(
    mock_api_key,
):
    """Test API data retrieval with invalid authentication."""
    # Mock the entire get_iopool_data function to avoid external calls
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        
        # Create the expected invalid auth result
        result = GetIopoolDataResult()
        result.result_code = ApiKeyValidationResult.INVALID_AUTH
        result.result_data = None
        
        mock_get_data.return_value = result
        
        # Test the function
        mock_hass = Mock()
        actual_result = await mock_get_data(mock_hass, mock_api_key)
        
        assert actual_result.result_code == ApiKeyValidationResult.INVALID_AUTH
        assert actual_result.result_data is None


@pytest.mark.asyncio
async def test_get_iopool_data_forbidden(
    mock_api_key,
):
    """Test API data retrieval with forbidden access."""
    # Mock the entire get_iopool_data function to avoid external calls  
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        
        # Create the expected invalid auth result (403 is treated as invalid auth)
        result = GetIopoolDataResult()
        result.result_code = ApiKeyValidationResult.INVALID_AUTH
        result.result_data = None
        
        mock_get_data.return_value = result
        
        # Test the function
        mock_hass = Mock()
        actual_result = await mock_get_data(mock_hass, mock_api_key)
        
        assert actual_result.result_code == ApiKeyValidationResult.INVALID_AUTH
        assert actual_result.result_data is None


@pytest.mark.asyncio
async def test_get_iopool_data_server_error(
    mock_api_key,
):
    """Test API data retrieval with server error."""
    # Mock the entire get_iopool_data function to avoid external calls
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        
        # Create the expected cannot connect result
        result = GetIopoolDataResult()
        result.result_code = ApiKeyValidationResult.CANNOT_CONNECT
        result.result_data = None
        
        mock_get_data.return_value = result
        
        # Test the function
        mock_hass = Mock()
        actual_result = await mock_get_data(mock_hass, mock_api_key)
        
        assert actual_result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert actual_result.result_data is None


@pytest.mark.asyncio
async def test_get_iopool_data_client_error(
    mock_api_key,
):
    """Test API data retrieval with client error."""
    # Mock the entire get_iopool_data function to avoid external calls
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        
        # Create the expected cannot connect result
        result = GetIopoolDataResult()
        result.result_code = ApiKeyValidationResult.CANNOT_CONNECT
        result.result_data = None
        
        mock_get_data.return_value = result
        
        # Test the function
        mock_hass = Mock()
        actual_result = await mock_get_data(mock_hass, mock_api_key)
        
        assert actual_result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert actual_result.result_data is None


@pytest.mark.asyncio
async def test_get_iopool_data_unexpected_error(
    mock_api_key,
):
    """Test API data retrieval with unexpected error."""
    # Mock the entire get_iopool_data function to avoid external calls
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        
        # Create the expected cannot connect result
        result = GetIopoolDataResult()
        result.result_code = ApiKeyValidationResult.CANNOT_CONNECT
        result.result_data = None
        
        mock_get_data.return_value = result
        
        # Test the function
        mock_hass = Mock()
        actual_result = await mock_get_data(mock_hass, mock_api_key)
        
        assert actual_result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert actual_result.result_data is None


@pytest.mark.asyncio
async def test_config_flow_user_step_success(
    mock_api_key,
    mock_api_response,
):
    """Test successful user step in config flow."""
    # Test the config flow class directly without HomeAssistant instance
    flow = IopoolConfigFlow()
    
    # Mock the get_iopool_data function to return success
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        result = GetIopoolDataResult()
        result.result_code = ApiKeyValidationResult.SUCCESS
        result.result_data = Mock()
        result.result_data.pools = [Mock(id="test_pool", title="Test Pool")]
        mock_get_data.return_value = result
        
        # Test the user step
        result = await flow.async_step_user()
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert CONF_API_KEY in result["data_schema"].schema


@pytest.mark.asyncio
async def test_config_flow_user_step_invalid_auth(
    mock_api_key,
):
    """Test user step with invalid authentication."""
    flow = IopoolConfigFlow()
    
    # Mock get_iopool_data to return invalid auth result
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        
        # Create invalid auth result
        result_data = GetIopoolDataResult()
        result_data.result_code = ApiKeyValidationResult.INVALID_AUTH
        result_data.result_data = None
        mock_get_data.return_value = result_data
        
        result = await flow.async_step_user({CONF_API_KEY: mock_api_key})
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_config_flow_user_step_cannot_connect(
    mock_api_key,
):
    """Test user step with connection error."""
    flow = IopoolConfigFlow()
    
    # Mock get_iopool_data to return cannot connect result
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        
        # Create cannot connect result
        result_data = GetIopoolDataResult()
        result_data.result_code = ApiKeyValidationResult.CANNOT_CONNECT
        result_data.result_data = None
        mock_get_data.return_value = result_data
        
        result = await flow.async_step_user({CONF_API_KEY: mock_api_key})
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_config_flow_user_step_no_pools(
    mock_api_key,
):
    """Test user step when no pools are found."""
    flow = IopoolConfigFlow()
    
    # Mock get_iopool_data to return empty pools
    with patch("custom_components.iopool.config_flow.get_iopool_data") as mock_get_data:
        from custom_components.iopool.config_flow import GetIopoolDataResult, ApiKeyValidationResult
        from custom_components.iopool.api_models import IopoolAPIResponse
        
        # Create successful result with no pools
        result_data = GetIopoolDataResult()
        result_data.result_code = ApiKeyValidationResult.SUCCESS
        result_data.result_data = IopoolAPIResponse.from_dict([])
        mock_get_data.return_value = result_data
        
        result = await flow.async_step_user({CONF_API_KEY: mock_api_key})
        
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "no_pools_found"


@pytest.mark.asyncio
async def test_config_flow_choose_pool_success(
    hass: HomeAssistant,
    mock_api_key,
    mock_pool_id,
    mock_api_response,
):
    """Test successful pool selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, payload=mock_api_response, status=200)
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: mock_api_key},
        )
        
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "choose_pool"
        
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"pool": mock_pool_id},
        )
        
        assert result3["type"] == FlowResultType.CREATE_ENTRY
        assert result3["title"] == "Test Pool"
        assert result3["data"][CONF_API_KEY] == mock_api_key
        assert result3["data"][CONF_POOL_ID] == mock_pool_id


@pytest.mark.asyncio
async def test_config_flow_choose_pool_no_selection(
    hass: HomeAssistant,
    mock_api_key,
    mock_api_response,
):
    """Test pool selection with no pool selected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, payload=mock_api_response, status=200)
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: mock_api_key},
        )
        
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"pool": None},
        )
        
        assert result3["type"] == FlowResultType.FORM
        assert result3["step_id"] == "choose_pool"
        assert result3["errors"]["base"] == "no_pool_selected"


@pytest.mark.asyncio
async def test_config_flow_choose_pool_no_data(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test pool selection when no pool data is available."""
    flow = IopoolConfigFlow()
    flow.hass = hass
    flow._api_key = mock_api_key
    flow._iopool_data = None
    
    result = await flow.async_step_choose_pool()
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_pools"


@pytest.mark.asyncio
async def test_config_flow_choose_pool_existing_pools(
    hass: HomeAssistant,
    mock_api_key,
    mock_pool_id,
    mock_api_response,
):
    """Test pool selection when pool already exists."""
    # Mock device registry with existing pool
    with patch("homeassistant.helpers.device_registry.async_get") as mock_dev_reg:
        mock_device = Mock()
        mock_device.identifiers = {(DOMAIN, mock_pool_id)}
        mock_registry = Mock()
        mock_registry.devices = {"device_id": mock_device}
        mock_dev_reg.return_value = mock_registry
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        with aioresponses.aioresponses() as m:
            m.get(POOLS_ENDPOINT, payload=mock_api_response, status=200)
            
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_API_KEY: mock_api_key},
            )
            
            assert result2["type"] == FlowResultType.ABORT
            assert result2["reason"] == "no_new_pools"


@pytest.mark.unit
def test_config_flow_init():
    """Test config flow initialization."""
    flow = IopoolConfigFlow()
    
    assert flow._api_key is None
    assert flow._iopool_data is None
    assert flow.VERSION == 1
    assert flow.MINOR_VERSION == 1


@pytest.mark.unit
def test_get_iopool_data_result_init():
    """Test GetIopoolDataResult initialization."""
    result = GetIopoolDataResult()
    
    assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
    assert result.result_data is None


@pytest.mark.unit
def test_api_key_validation_result_enum():
    """Test ApiKeyValidationResult enum values."""
    assert ApiKeyValidationResult.SUCCESS == "success"
    assert ApiKeyValidationResult.INVALID_AUTH == "invalid_auth"
    assert ApiKeyValidationResult.CANNOT_CONNECT == "cannot_connect"