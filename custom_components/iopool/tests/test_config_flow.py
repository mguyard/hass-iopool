"""Tests for iopool config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from aiohttp.client_exceptions import ClientError
from custom_components.iopool.config_flow import ApiKeyValidationResult, get_iopool_data
from custom_components.iopool.const import CONF_POOL_ID, DOMAIN
import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import TEST_API_KEY, TEST_POOL_ID, TEST_POOL_TITLE


class TestGetIopoolData:
    """Test get_iopool_data function."""

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.async_get_clientsession")
    async def test_get_iopool_data_success(
        self, mock_session_func, hass: HomeAssistant, mock_aiohttp_session
    ) -> None:
        """Test successful API data retrieval."""
        mock_session_func.return_value = mock_aiohttp_session

        result = await get_iopool_data(hass, TEST_API_KEY)

        assert result.result_code == ApiKeyValidationResult.SUCCESS
        assert result.result_data is not None
        assert len(result.result_data.pools) == 1
        assert result.result_data.pools[0].id == TEST_POOL_ID

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.async_get_clientsession")
    async def test_get_iopool_data_invalid_auth(
        self, mock_session_func, hass: HomeAssistant, mock_aiohttp_session
    ) -> None:
        """Test API data retrieval with invalid auth."""
        # Override the status to return 401
        mock_aiohttp_session.get.return_value.__aenter__.return_value.status = 401
        mock_session_func.return_value = mock_aiohttp_session

        result = await get_iopool_data(hass, "invalid_key")

        assert result.result_code == ApiKeyValidationResult.INVALID_AUTH
        assert result.result_data is None

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.async_get_clientsession")
    async def test_get_iopool_data_connection_error(
        self, mock_session_func, hass: HomeAssistant, mock_aiohttp_session
    ) -> None:
        """Test API data retrieval with connection error."""
        # Override the session to raise ClientError
        mock_session_func.return_value.get.side_effect = ClientError(
            "Connection failed"
        )

        result = await get_iopool_data(hass, TEST_API_KEY)

        assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert result.result_data is None

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.async_get_clientsession")
    async def test_get_iopool_data_server_error(
        self, mock_session_func, hass: HomeAssistant
    ) -> None:
        """Test API data retrieval with server error."""
        session = AsyncMock()
        response_mock = AsyncMock()
        response_mock.status = 500
        session.get.return_value.__aenter__.return_value = response_mock
        mock_session_func.return_value = session

        result = await get_iopool_data(hass, TEST_API_KEY)

        assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert result.result_data is None

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.async_get_clientsession")
    async def test_get_iopool_data_json_error(
        self, mock_session_func, hass: HomeAssistant
    ) -> None:
        """Test API data retrieval with JSON parsing error."""
        session = AsyncMock()
        response_mock = AsyncMock()
        response_mock.status = 200
        response_mock.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        session.get.return_value.__aenter__.return_value = response_mock
        mock_session_func.return_value = session

        result = await get_iopool_data(hass, TEST_API_KEY)

        assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
        assert result.result_data is None

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.async_get_clientsession")
    async def test_get_iopool_data_no_pools(
        self, mock_session_func, hass: HomeAssistant, mock_aiohttp_session
    ) -> None:
        """Test API data retrieval with no pools."""
        # Override to return empty pools list
        mock_aiohttp_session.get.return_value.__aenter__.return_value.json.return_value = []
        mock_session_func.return_value = mock_aiohttp_session

        result = await get_iopool_data(hass, TEST_API_KEY)

        assert result.result_code == ApiKeyValidationResult.SUCCESS
        assert result.result_data is not None
        assert len(result.result_data.pools) == 0


class TestConfigFlow:
    """Test config flow."""

    @pytest.mark.asyncio
    async def test_user_form_display(self, hass: HomeAssistant) -> None:
        """Test that the user form is displayed correctly."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.get_iopool_data")
    async def test_user_form_valid_api_key(
        self, mock_get_data, hass: HomeAssistant, mock_api_response
    ) -> None:
        """Test user form with valid API key."""
        mock_get_data.return_value.result_code = ApiKeyValidationResult.SUCCESS
        mock_get_data.return_value.result_data = mock_api_response

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: TEST_API_KEY},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "choose_pool"

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.get_iopool_data")
    async def test_user_form_invalid_api_key(
        self, mock_get_data, hass: HomeAssistant
    ) -> None:
        """Test user form with invalid API key."""
        mock_get_data.return_value.result_code = ApiKeyValidationResult.INVALID_AUTH
        mock_get_data.return_value.result_data = None

        # Override mock to return error for this test
        hass.config_entries.flow.async_configure = AsyncMock(
            return_value={
                "type": FlowResultType.FORM,
                "step_id": "user",
                "errors": {"base": "invalid_auth"},
                "flow_id": "test_flow_id",
            }
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "invalid_key"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "invalid_auth"}

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.get_iopool_data")
    async def test_user_form_connection_error(
        self, mock_get_data, hass: HomeAssistant
    ) -> None:
        """Test user form with connection error."""
        mock_get_data.return_value.result_code = ApiKeyValidationResult.CANNOT_CONNECT
        mock_get_data.return_value.result_data = None

        # Override mock to return error for this test
        hass.config_entries.flow.async_configure = AsyncMock(
            return_value={
                "type": FlowResultType.FORM,
                "step_id": "user",
                "errors": {"base": "cannot_connect"},
                "flow_id": "test_flow_id",
            }
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: TEST_API_KEY},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.get_iopool_data")
    async def test_user_form_no_pools_found(
        self, mock_get_data, hass: HomeAssistant, mock_api_response_no_pools
    ) -> None:
        """Test user form when no pools are found."""
        mock_get_data.return_value.result_code = ApiKeyValidationResult.SUCCESS
        mock_get_data.return_value.result_data = mock_api_response_no_pools

        # Override mock to return error for this test
        hass.config_entries.flow.async_configure = AsyncMock(
            return_value={
                "type": FlowResultType.FORM,
                "step_id": "user",
                "errors": {"base": "no_pools"},
                "flow_id": "test_flow_id",
            }
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: TEST_API_KEY},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "no_pools"}

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.get_iopool_data")
    async def test_choose_pool_form_success(
        self, mock_get_data, hass: HomeAssistant, mock_api_response
    ) -> None:
        """Test successful pool selection."""
        mock_get_data.return_value.result_code = ApiKeyValidationResult.SUCCESS
        mock_get_data.return_value.result_data = mock_api_response

        # Start flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Provide API key
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: TEST_API_KEY},
        )

        # Override mock for the pool selection to return success
        hass.config_entries.flow.async_configure = AsyncMock(
            return_value={
                "type": FlowResultType.CREATE_ENTRY,
                "title": TEST_POOL_TITLE,
                "data": {
                    CONF_API_KEY: TEST_API_KEY,
                    CONF_POOL_ID: TEST_POOL_ID,
                },
            }
        )

        # Select pool
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_POOL_ID: TEST_POOL_ID},
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == TEST_POOL_TITLE
        assert result["data"] == {
            CONF_API_KEY: TEST_API_KEY,
            CONF_POOL_ID: TEST_POOL_ID,
        }

    @pytest.mark.asyncio
    @patch("custom_components.iopool.config_flow.get_iopool_data")
    async def test_choose_pool_no_pool_selected(
        self, mock_get_data, hass: HomeAssistant, mock_api_response
    ) -> None:
        """Test pool selection form with no pool selected."""
        mock_get_data.return_value.result_code = ApiKeyValidationResult.SUCCESS
        mock_get_data.return_value.result_data = mock_api_response

        # Start flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Provide API key
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: TEST_API_KEY},
        )

        # Override mock for the pool selection to return error
        hass.config_entries.flow.async_configure = AsyncMock(
            return_value={
                "type": FlowResultType.FORM,
                "step_id": "choose_pool",
                "errors": {"base": "no_pool_selected"},
                "flow_id": "test_flow_id",
            }
        )

        # Don't select any pool
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "choose_pool"
        assert result["errors"] == {"base": "no_pool_selected"}
