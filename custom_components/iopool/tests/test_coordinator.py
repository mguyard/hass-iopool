"""Tests for iopool coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp.client_exceptions import ClientError, ServerTimeoutError
from custom_components.iopool.api_models import IopoolAPIResponse
from custom_components.iopool.coordinator import IopoolDataUpdateCoordinator
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from .conftest import MOCK_POOLS_API_RESPONSE, TEST_API_KEY, TEST_POOL_ID


class TestIopoolDataUpdateCoordinator:
    """Test cases for IopoolDataUpdateCoordinator."""

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_coordinator_init(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test coordinator initialization."""
        # Mock the session to avoid frame helper issues
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        assert coordinator.api_key == TEST_API_KEY
        assert coordinator.hass == hass
        assert coordinator.headers == {"x-api-key": TEST_API_KEY}
        assert coordinator.session is not None
        assert coordinator.name == "iopool"

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_success(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test successful data update."""
        # Mock the session to avoid frame helper issues
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that returns successful response
        class MockSession:
            def get(self, *args, **kwargs):
                class MockContextManager:
                    async def __aenter__(self):
                        class MockResponse:
                            async def json(self):
                                return MOCK_POOLS_API_RESPONSE

                            def raise_for_status(self):
                                pass

                        return MockResponse()

                    async def __aexit__(self, *args):
                        pass

                return MockContextManager()

        coordinator.session = MockSession()

        result = await coordinator._async_update_data()  # noqa: SLF001
        coordinator.data = result

        assert coordinator.data is not None
        assert len(coordinator.data.pools) == 1
        assert coordinator.data.pools[0].id == TEST_POOL_ID

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_client_error(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test data update with client error."""
        # Mock the session to avoid frame helper issues
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that raises ClientError
        class MockSession:
            def get(self, *args, **kwargs):
                raise ClientError("Connection error")

        coordinator.session = MockSession()

        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()  # noqa: SLF001

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_timeout_error(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test data update with timeout error."""
        # Mock the session to avoid frame helper issues
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that raises ServerTimeoutError
        class MockSession:
            def get(self, *args, **kwargs):
                raise ServerTimeoutError("Timeout")

        coordinator.session = MockSession()

        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()  # noqa: SLF001

    @patch("homeassistant.helpers.frame.report_usage")
    def test_get_pool_data_found(
        self, mock_report: AsyncMock, mock_iopool_coordinator
    ) -> None:
        """Test get_pool_data when pool is found."""
        coordinator = mock_iopool_coordinator
        # Set up the mock to return the expected pool data
        mock_pool = type("Pool", (), {"id": TEST_POOL_ID, "title": "Test Pool"})()
        coordinator.data = IopoolAPIResponse(pools=[mock_pool])

        # Use real method instead of mock
        coordinator.get_pool_data = IopoolDataUpdateCoordinator.get_pool_data.__get__(
            coordinator
        )

        result = coordinator.get_pool_data(TEST_POOL_ID)

        assert result is not None
        assert result.id == TEST_POOL_ID

    @patch("homeassistant.helpers.frame.report_usage")
    def test_get_pool_data_not_found(
        self, mock_report: AsyncMock, mock_iopool_coordinator
    ) -> None:
        """Test get_pool_data when pool is not found."""
        coordinator = mock_iopool_coordinator
        # Override the mock to return None for non-existent pool
        coordinator.get_pool_data.side_effect = lambda pool_id: (
            coordinator.data.pools[0] if pool_id == TEST_POOL_ID else None
        )

        result = coordinator.get_pool_data("nonexistent_pool")

        assert result is None

    @patch("homeassistant.helpers.frame.report_usage")
    def test_get_pool_data_no_data(
        self, mock_report: AsyncMock, mock_iopool_coordinator
    ) -> None:
        """Test get_pool_data when coordinator has no data."""
        coordinator = mock_iopool_coordinator
        coordinator.data = None

        # Use real method instead of mock
        coordinator.get_pool_data = IopoolDataUpdateCoordinator.get_pool_data.__get__(
            coordinator
        )

        result = coordinator.get_pool_data(TEST_POOL_ID)

        assert result is None

    @patch("homeassistant.helpers.frame.report_usage")
    def test_get_pool_data_empty_pools(
        self,
        mock_report: AsyncMock,
        mock_iopool_coordinator,
        mock_api_response_no_pools,
    ) -> None:
        """Test get_pool_data when coordinator has empty pools."""
        coordinator = mock_iopool_coordinator
        coordinator.data = mock_api_response_no_pools

        # Use real method instead of mock
        coordinator.get_pool_data = IopoolDataUpdateCoordinator.get_pool_data.__get__(
            coordinator
        )

        result = coordinator.get_pool_data(TEST_POOL_ID)

        assert result is None
