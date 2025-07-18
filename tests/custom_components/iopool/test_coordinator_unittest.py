"""Test the iopool coordinator using unittest."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os

# Add the custom_components directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from custom_components.iopool.coordinator import IopoolDataUpdateCoordinator
from custom_components.iopool.const import DOMAIN
from custom_components.iopool.api_models import IopoolAPIResponse


class TestIopoolDataUpdateCoordinator(unittest.TestCase):
    """Test the IopoolDataUpdateCoordinator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_api_key = "test_api_key_12345"
        self.test_pool_id = "test_pool_123"
        
        # Mock API response data (matches actual API structure)
        self.mock_pool_data = {
            "id": self.test_pool_id,
            "title": "Test Pool",
            "mode": "STANDARD",
            "hasAnActionRequired": False,
            "latestMeasure": {
                "temperature": 22.5,
                "ph": 7.2,
                "orp": 650,
                "mode": "standard",
                "isValid": True,
                "ecoId": "eco_123",
                "measuredAt": "2024-01-15T14:30:00Z",
            },
            "advice": {
                "filtrationDuration": 8.5,
            },
        }
        
        # API returns list of pools directly
        self.mock_api_response = [self.mock_pool_data]
        
        # Mock Home Assistant
        self.mock_hass = MagicMock()
        self.mock_hass.data = {}
        
        # Mock aiohttp session
        self.mock_session = AsyncMock()

    def test_coordinator_init(self):
        """Test coordinator initialization."""
        with patch('custom_components.iopool.coordinator.async_get_clientsession', return_value=self.mock_session):
            coordinator = IopoolDataUpdateCoordinator(self.mock_hass, self.test_api_key)
            
            self.assertEqual(coordinator.api_key, self.test_api_key)
            self.assertEqual(coordinator.headers, {"x-api-key": self.test_api_key})
            self.assertEqual(coordinator.hass, self.mock_hass)
            self.assertEqual(coordinator.name, DOMAIN)

    def test_get_pool_data_success(self):
        """Test successful pool data retrieval."""
        with patch('custom_components.iopool.coordinator.async_get_clientsession', return_value=self.mock_session):
            coordinator = IopoolDataUpdateCoordinator(self.mock_hass, self.test_api_key)
            
            # Set up coordinator data
            api_response = IopoolAPIResponse.from_dict(self.mock_api_response)
            coordinator.data = api_response
            
            result = coordinator.get_pool_data(self.test_pool_id)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.id, self.test_pool_id)
            self.assertEqual(result.title, "Test Pool")

    def test_get_pool_data_not_found(self):
        """Test pool data retrieval when pool not found."""
        with patch('custom_components.iopool.coordinator.async_get_clientsession', return_value=self.mock_session):
            coordinator = IopoolDataUpdateCoordinator(self.mock_hass, self.test_api_key)
            
            # Set up coordinator data
            api_response = IopoolAPIResponse.from_dict(self.mock_api_response)
            coordinator.data = api_response
            
            result = coordinator.get_pool_data("nonexistent_pool")
            
            self.assertIsNone(result)

    def test_get_pool_data_no_data(self):
        """Test pool data retrieval when no data available."""
        with patch('custom_components.iopool.coordinator.async_get_clientsession', return_value=self.mock_session):
            coordinator = IopoolDataUpdateCoordinator(self.mock_hass, self.test_api_key)
            
            # No data set
            coordinator.data = None
            
            result = coordinator.get_pool_data(self.test_pool_id)
            
            self.assertIsNone(result)

    async def _test_async_update_data_success(self):
        """Test successful data update (async helper)."""
        with patch('custom_components.iopool.coordinator.async_get_clientsession', return_value=self.mock_session):
            coordinator = IopoolDataUpdateCoordinator(self.mock_hass, self.test_api_key)
            
            # Mock successful response
            response_mock = AsyncMock()
            response_mock.json.return_value = self.mock_api_response
            response_mock.raise_for_status = AsyncMock()
            self.mock_session.get.return_value.__aenter__.return_value = response_mock
            
            result = await coordinator._async_update_data()
            
            self.assertIsInstance(result, IopoolAPIResponse)
            self.assertEqual(len(result.pools), 1)
            self.assertEqual(result.pools[0].id, self.test_pool_id)

    def test_update_data_success(self):
        """Test successful data update."""
        asyncio.run(self._test_async_update_data_success())

    def test_coordinator_headers(self):
        """Test that coordinator sets correct headers."""
        with patch('custom_components.iopool.coordinator.async_get_clientsession', return_value=self.mock_session):
            coordinator = IopoolDataUpdateCoordinator(self.mock_hass, self.test_api_key)
            
            expected_headers = {"x-api-key": self.test_api_key}
            self.assertEqual(coordinator.headers, expected_headers)


if __name__ == '__main__':
    unittest.main()