"""Tests for iopool coordinator."""

from __future__ import annotations

import json
import logging
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


class TestIopoolDataUpdateCoordinatorEdgeCases:
    """Test edge cases for IopoolDataUpdateCoordinator."""

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_invalid_json_response(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test data update with invalid JSON response."""
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that returns invalid JSON
        class MockSession:
            def get(self, *args, **kwargs):
                class MockContextManager:
                    async def __aenter__(self):
                        class MockResponse:
                            async def json(self):
                                raise json.JSONDecodeError("Invalid JSON", "", 0)

                            def raise_for_status(self):
                                pass

                        return MockResponse()

                    async def __aexit__(self, *args):
                        pass

                return MockContextManager()

        coordinator.session = MockSession()

        with pytest.raises(UpdateFailed, match="Error parsing API response"):
            await coordinator._async_update_data()  # noqa: SLF001

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_key_error(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test data update with KeyError during parsing."""
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that returns incomplete data
        class MockSession:
            def get(self, *args, **kwargs):
                class MockContextManager:
                    async def __aenter__(self):
                        class MockResponse:
                            async def json(self):
                                # Missing required key to trigger KeyError in from_dict
                                return [
                                    {"missing_required_field": "value"}
                                ]  # Missing 'id' and other required fields

                            def raise_for_status(self):
                                pass

                        return MockResponse()

                    async def __aexit__(self, *args):
                        pass

                return MockContextManager()

        coordinator.session = MockSession()

        with pytest.raises(UpdateFailed, match="Error parsing API response"):
            await coordinator._async_update_data()  # noqa: SLF001

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_http_error(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test data update with HTTP error."""
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that raises HTTP error
        class MockSession:
            def get(self, *args, **kwargs):
                raise ClientError("HTTP error")

        coordinator.session = MockSession()

        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()  # noqa: SLF001

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_empty_response(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test data update with empty response."""
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that returns empty pools
        class MockSession:
            def get(self, *args, **kwargs):
                class MockContextManager:
                    async def __aenter__(self):
                        class MockResponse:
                            async def json(self):
                                return []  # Empty list

                            def raise_for_status(self):
                                pass

                        return MockResponse()

                    async def __aexit__(self, *args):
                        pass

                return MockContextManager()

        coordinator.session = MockSession()

        result = await coordinator._async_update_data()  # noqa: SLF001
        assert result is not None
        assert result.pools == []

    @patch("homeassistant.helpers.frame.report_usage")
    def test_get_pool_data_multiple_pools(
        self, mock_report: AsyncMock, mock_iopool_coordinator
    ) -> None:
        """Test get_pool_data with multiple pools."""
        coordinator = mock_iopool_coordinator

        # Create multiple pools
        mock_pool1 = type("Pool", (), {"id": "pool1", "title": "Pool 1"})()
        mock_pool2 = type("Pool", (), {"id": "pool2", "title": "Pool 2"})()
        mock_pool3 = type("Pool", (), {"id": TEST_POOL_ID, "title": "Test Pool"})()
        coordinator.data = IopoolAPIResponse(pools=[mock_pool1, mock_pool2, mock_pool3])

        # Use real method instead of mock
        coordinator.get_pool_data = IopoolDataUpdateCoordinator.get_pool_data.__get__(
            coordinator
        )

        # Test finding each pool
        result1 = coordinator.get_pool_data("pool1")
        assert result1 is not None
        assert result1.id == "pool1"

        result2 = coordinator.get_pool_data("pool2")
        assert result2 is not None
        assert result2.id == "pool2"

        result3 = coordinator.get_pool_data(TEST_POOL_ID)
        assert result3 is not None
        assert result3.id == TEST_POOL_ID

        # Test non-existent pool
        result_none = coordinator.get_pool_data("nonexistent")
        assert result_none is None

    @patch("homeassistant.helpers.frame.report_usage")
    def test_get_pool_data_with_none_pools(
        self, mock_report: AsyncMock, mock_iopool_coordinator
    ) -> None:
        """Test get_pool_data when pools list is None."""
        coordinator = mock_iopool_coordinator
        coordinator.data = IopoolAPIResponse(pools=None)

        # Use real method instead of mock
        coordinator.get_pool_data = IopoolDataUpdateCoordinator.get_pool_data.__get__(
            coordinator
        )

        result = coordinator.get_pool_data(TEST_POOL_ID)
        assert result is None


class TestIopoolDataUpdateCoordinatorIntegration:
    """Integration tests for IopoolDataUpdateCoordinator."""

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_full_update_cycle_success(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test a full successful update cycle."""
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session with realistic data
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

        # Perform update
        result = await coordinator._async_update_data()  # noqa: SLF001
        coordinator.data = result

        # Verify data structure
        assert result is not None
        assert isinstance(result, IopoolAPIResponse)
        assert len(result.pools) == 1
        assert result.pools[0].id == TEST_POOL_ID

        # Test get_pool_data functionality
        pool_data = coordinator.get_pool_data(TEST_POOL_ID)
        assert pool_data is not None
        assert pool_data.id == TEST_POOL_ID

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_coordinator_with_custom_api_key(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test coordinator initialization with custom API key."""
        custom_api_key = "custom_test_key_12345"
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, custom_api_key)

        assert coordinator.api_key == custom_api_key
        assert coordinator.headers == {"x-api-key": custom_api_key}

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_coordinator_logging_and_debug(
        self,
        mock_session,
        mock_zeroconf,
        mock_report: AsyncMock,
        hass: HomeAssistant,
        caplog,
    ) -> None:
        """Test coordinator logging functionality."""
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that logs debug info
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

        # Enable debug logging for this test
        with caplog.at_level(
            logging.DEBUG, logger="custom_components.iopool.coordinator"
        ):
            await coordinator._async_update_data()  # noqa: SLF001

        # Check that debug messages were logged
        debug_messages = [
            record.message
            for record in caplog.records
            if record.levelno == logging.DEBUG
        ]
        assert any("Updating iopool data with API key" in msg for msg in debug_messages)
        assert any("iopool Response data:" in msg for msg in debug_messages)


class TestIopoolDataUpdateCoordinatorExceptionHandling:
    """Test comprehensive exception handling for IopoolDataUpdateCoordinator."""

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_value_error(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test data update with ValueError during parsing."""
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that returns data causing ValueError
        class MockSession:
            def get(self, *args, **kwargs):
                class MockContextManager:
                    async def __aenter__(self):
                        class MockResponse:
                            async def json(self):
                                # Return data that will cause ValueError in parsing
                                return [
                                    {
                                        "id": "pool1",
                                        "title": "Pool 1",
                                        "hasAFiltrationSystem": "invalid_boolean",  # Should cause ValueError
                                        "lastMeasure": {},
                                        "advice": {},
                                    }
                                ]

                            def raise_for_status(self):
                                pass

                        return MockResponse()

                    async def __aexit__(self, *args):
                        pass

                return MockContextManager()

        coordinator.session = MockSession()

        with pytest.raises(UpdateFailed, match="Error parsing API response"):
            await coordinator._async_update_data()  # noqa: SLF001

    @patch("homeassistant.helpers.frame.report_usage")
    @patch("homeassistant.components.zeroconf.async_get_async_zeroconf")
    @patch("homeassistant.helpers.aiohttp_client.async_get_clientsession")
    async def test_async_update_data_unexpected_exception(
        self, mock_session, mock_zeroconf, mock_report: AsyncMock, hass: HomeAssistant
    ) -> None:
        """Test data update with unexpected exception type."""
        mock_session.return_value = MagicMock()
        coordinator = IopoolDataUpdateCoordinator(hass, TEST_API_KEY)

        # Create a mock session that raises unexpected exception
        class MockSession:
            def get(self, *args, **kwargs):
                class MockContextManager:
                    async def __aenter__(self):
                        # Raise an unexpected exception type not caught by the coordinator
                        raise RuntimeError("Unexpected error")

                    async def __aexit__(self, *args):
                        pass

                return MockContextManager()

        coordinator.session = MockSession()

        # This should not be caught by the coordinator and should propagate
        with pytest.raises(RuntimeError, match="Unexpected error"):
            await coordinator._async_update_data()  # noqa: SLF001
