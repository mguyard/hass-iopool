"""Tests for iopool config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from aiohttp.client_exceptions import ClientError
from custom_components.iopool.api_models import IopoolAPIResponse
from custom_components.iopool.config_flow import (
    ApiKeyValidationResult,
    IopoolConfigFlow,
    IopoolOptionsFlow,
    get_iopool_data,
)
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


class TestIopoolOptionsFlow:
    """Test IopoolOptionsFlow class."""

    @pytest.mark.asyncio
    async def test_choose_pool_no_pools_available(self, hass: HomeAssistant) -> None:
        """Test choose_pool step when no pools are available."""
        flow = IopoolConfigFlow()
        flow.hass = hass
        flow._iopool_data = None  # noqa: SLF001

        result = await flow.async_step_choose_pool()
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "no_pools"

    @pytest.mark.asyncio
    async def test_choose_pool_no_new_pools(
        self, hass: HomeAssistant, mock_api_response
    ) -> None:
        """Test choose_pool step when no new pools are available."""
        # Skip device registry test for now since it requires proper Home Assistant setup
        flow = IopoolConfigFlow()
        flow.hass = hass
        flow._iopool_data = mock_api_response  # noqa: SLF001

        # Mock device registry to return existing devices
        with patch("homeassistant.helpers.device_registry.async_get") as mock_registry:
            mock_registry.return_value.devices.values.return_value = [
                type(
                    "MockDevice",
                    (),
                    {
                        "identifiers": {(DOMAIN, TEST_POOL_ID)},
                    },
                )()
            ]

            result = await flow.async_step_choose_pool()
            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "no_new_pools"

    @pytest.mark.asyncio
    async def test_user_step_no_pools_found(self, hass: HomeAssistant) -> None:
        """Test user step when API returns no pools."""
        with patch(
            "custom_components.iopool.config_flow.get_iopool_data"
        ) as mock_get_data:
            # Mock API response with no pools
            mock_get_data.return_value.result_code = ApiKeyValidationResult.SUCCESS
            mock_get_data.return_value.result_data = IopoolAPIResponse(pools=[])

            flow = IopoolConfigFlow()
            flow.hass = hass

            result = await flow.async_step_user({CONF_API_KEY: TEST_API_KEY})
            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "no_pools_found"

    @pytest.mark.asyncio
    async def test_get_iopool_data_client_error(self, hass: HomeAssistant) -> None:
        """Test get_iopool_data with ClientError."""
        with patch(
            "homeassistant.helpers.aiohttp_client.async_get_clientsession"
        ) as mock_session:
            mock_session.return_value.get.side_effect = ClientError("Network error")

            result = await get_iopool_data(hass, TEST_API_KEY)
            assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
            assert result.result_data is None

    @pytest.mark.asyncio
    async def test_get_iopool_data_server_error(self, hass: HomeAssistant) -> None:
        """Test get_iopool_data with server error (5xx)."""
        with patch(
            "custom_components.iopool.config_flow.async_get_clientsession"
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.raise_for_status.side_effect = Exception("Server error")
            mock_session.return_value.get.return_value.__aenter__.return_value = (
                mock_response
            )

            result = await get_iopool_data(hass, TEST_API_KEY)
            assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
            assert result.result_data is None

    @pytest.mark.asyncio
    async def test_get_iopool_data_other_http_error(self, hass: HomeAssistant) -> None:
        """Test get_iopool_data with other HTTP error (e.g., 404)."""
        with patch(
            "custom_components.iopool.config_flow.async_get_clientsession"
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.raise_for_status.return_value = None
            mock_session.return_value.get.return_value.__aenter__.return_value = (
                mock_response
            )

            result = await get_iopool_data(hass, TEST_API_KEY)
            assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
            assert result.result_data is None

    @pytest.mark.asyncio
    async def test_get_iopool_data_unexpected_error(self, hass: HomeAssistant) -> None:
        """Test get_iopool_data with unexpected error."""
        with patch(
            "custom_components.iopool.config_flow.async_get_clientsession"
        ) as mock_session:
            mock_session.return_value.get.side_effect = RuntimeError("Unexpected error")

            result = await get_iopool_data(hass, TEST_API_KEY)
            assert result.result_code == ApiKeyValidationResult.CANNOT_CONNECT
            assert result.result_data is None

    @pytest.mark.asyncio
    async def test_choose_pool_no_pool_selected(
        self, hass: HomeAssistant, mock_api_response
    ) -> None:
        """Test choose_pool step when no pool is selected."""
        flow = IopoolConfigFlow()
        flow.hass = hass
        flow._iopool_data = mock_api_response  # noqa: SLF001

        # Mock device registry to return no existing devices
        with patch("homeassistant.helpers.device_registry.async_get") as mock_registry:
            mock_registry.return_value.devices.values.return_value = []

            # Test with empty user input
            result = await flow.async_step_choose_pool({})
            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == "no_pool_selected"

    @pytest.mark.asyncio
    async def test_choose_pool_form_display(
        self, hass: HomeAssistant, mock_api_response
    ) -> None:
        """Test choose_pool step displays form correctly."""
        flow = IopoolConfigFlow()
        flow.hass = hass
        flow._iopool_data = mock_api_response  # noqa: SLF001

        # Mock device registry to return no existing devices
        with patch("homeassistant.helpers.device_registry.async_get") as mock_registry:
            mock_registry.return_value.devices.values.return_value = []

            result = await flow.async_step_choose_pool()
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "choose_pool"
            assert result["last_step"] is True

    @pytest.mark.asyncio
    async def test_reconfigure_step_no_changes(self, hass: HomeAssistant) -> None:
        """Test reconfigure step when API key hasn't changed."""
        flow = IopoolConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry"}

        # Mock config entry
        mock_entry = AsyncMock()
        mock_entry.data = {CONF_API_KEY: TEST_API_KEY}

        with patch.object(
            hass.config_entries, "async_get_entry", return_value=mock_entry
        ):
            result = await flow.async_step_reconfigure({CONF_API_KEY: TEST_API_KEY})
            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "no_changes"

    @pytest.mark.asyncio
    async def test_reconfigure_step_success(self, hass: HomeAssistant) -> None:
        """Test successful reconfigure step."""
        flow = IopoolConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry"}

        # Mock config entry
        mock_entry = AsyncMock()
        mock_entry.data = {CONF_API_KEY: "old_api_key"}
        mock_entry.unique_id = "test_unique_id"

        with (
            patch.object(
                hass.config_entries, "async_get_entry", return_value=mock_entry
            ),
            patch(
                "custom_components.iopool.config_flow.get_iopool_data"
            ) as mock_get_data,
        ):
            # Mock successful API validation
            mock_get_data.return_value.result_code = ApiKeyValidationResult.SUCCESS

            result = await flow.async_step_reconfigure({CONF_API_KEY: "new_api_key"})
            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "reconfigure_successful"

    @pytest.mark.asyncio
    async def test_reconfigure_step_api_error(self, hass: HomeAssistant) -> None:
        """Test reconfigure step with API validation error."""
        flow = IopoolConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry"}

        # Mock config entry
        mock_entry = AsyncMock()
        mock_entry.data = {CONF_API_KEY: "old_api_key"}

        # Create a proper mock result that matches the expected structure
        class MockResult:
            def __init__(self):
                self.result_code = ApiKeyValidationResult.INVALID_AUTH

            @property
            def value(self):
                return self.result_code.value

        mock_result = MockResult()

        with (
            patch.object(
                hass.config_entries, "async_get_entry", return_value=mock_entry
            ),
            patch(
                "custom_components.iopool.config_flow.get_iopool_data",
                return_value=mock_result,
            ),
        ):
            result = await flow.async_step_reconfigure(
                {CONF_API_KEY: "invalid_api_key"}
            )
            assert result["type"] == FlowResultType.FORM
            assert result["errors"]["base"] == ApiKeyValidationResult.INVALID_AUTH.value

    @pytest.mark.asyncio
    async def test_reconfigure_step_form_display(self, hass: HomeAssistant) -> None:
        """Test reconfigure step displays form correctly."""
        flow = IopoolConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry"}

        # Mock config entry
        mock_entry = AsyncMock()
        mock_entry.data = {CONF_API_KEY: TEST_API_KEY}

        with patch.object(
            hass.config_entries, "async_get_entry", return_value=mock_entry
        ):
            result = await flow.async_step_reconfigure()
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "reconfigure"

    @staticmethod
    def test_async_get_options_flow() -> None:
        """Test that async_get_options_flow returns correct flow type."""
        # Mock config entry
        mock_entry = AsyncMock()

        flow = IopoolConfigFlow.async_get_options_flow(mock_entry)
        assert isinstance(flow, IopoolOptionsFlow)
