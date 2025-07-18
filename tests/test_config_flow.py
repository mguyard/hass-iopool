"""Test the iopool config flow."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch
from aiohttp import ClientError
import aioresponses
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
    hass: HomeAssistant,
    mock_api_key,
    mock_api_response,
):
    """Test successful API data retrieval."""
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, payload=mock_api_response, status=200)
        
        result = await get_iopool_data(hass, mock_api_key)
        
        assert result.result_code == ApiKeyValidationResult.SUCCESS
        assert result.result_data is not None
        assert len(result.result_data.pools) == 1


@pytest.mark.asyncio
async def test_get_iopool_data_invalid_auth(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test API data retrieval with invalid authentication."""
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, status=401)
        
        result = await get_iopool_data(hass, mock_api_key)
        
        assert result.result_code == ApiKeyValidationResult.INVALID_AUTH
        assert result.result_data is None


@pytest.mark.asyncio
async def test_get_iopool_data_forbidden(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test API data retrieval with forbidden access."""
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, status=403)
        
        result = await get_iopool_data(hass, mock_api_key)
        
        assert result.result_code == ApiKeyValidationResult.INVALID_AUTH
        assert result.result_data is None


@pytest.mark.asyncio
async def test_get_iopool_data_server_error(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test API data retrieval with server error."""
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, status=500)
        
        result = await get_iopool_data(hass, mock_api_key)
        
        assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert result.result_data is None


@pytest.mark.asyncio
async def test_get_iopool_data_client_error(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test API data retrieval with client error."""
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, exception=ClientError("Connection failed"))
        
        result = await get_iopool_data(hass, mock_api_key)
        
        assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert result.result_data is None


@pytest.mark.asyncio
async def test_get_iopool_data_unexpected_error(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test API data retrieval with unexpected error."""
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session:
        mock_session.side_effect = Exception("Unexpected error")
        
        result = await get_iopool_data(hass, mock_api_key)
        
        assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert result.result_data is None


@pytest.mark.asyncio
async def test_config_flow_user_step_success(
    hass: HomeAssistant,
    mock_api_key,
    mock_api_response,
):
    """Test successful user step in config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, payload=mock_api_response, status=200)
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: mock_api_key},
        )
        
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "choose_pool"


@pytest.mark.asyncio
async def test_config_flow_user_step_invalid_auth(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test user step with invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, status=401)
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: mock_api_key},
        )
        
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "user"
        assert result2["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_config_flow_user_step_cannot_connect(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test user step with connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, status=500)
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: mock_api_key},
        )
        
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "user"
        assert result2["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_config_flow_user_step_no_pools(
    hass: HomeAssistant,
    mock_api_key,
):
    """Test user step when no pools are found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    empty_response = {"pools": []}
    
    with aioresponses.aioresponses() as m:
        m.get(POOLS_ENDPOINT, payload=empty_response, status=200)
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: mock_api_key},
        )
        
        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "no_pools_found"


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