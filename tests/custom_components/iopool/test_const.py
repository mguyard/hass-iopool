"""Test the iopool constants."""

import unittest
from datetime import timedelta
import sys
import os

# Add the custom_components directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../custom_components/iopool'))

# Import directly from the module file to avoid __init__.py
from const import (
    DOMAIN,
    MANUFACTURER,
    CONFIG_VERSION,
    CONFIG_MINOR_VERSION,
    CONF_API_KEY,
    CONF_POOL_ID,
    DEFAULT_SCAN_INTERVAL,
    API_BASE_URL,
    POOLS_ENDPOINT,
    POOL_ENDPOINT,
    SENSOR_TEMPERATURE,
    SENSOR_PH,
    SENSOR_ORP,
    EVENT_TYPE_BOOST_START,
    EVENT_TYPE_BOOST_END,
)


class TestIopoolConstants(unittest.TestCase):
    """Test the iopool constants."""

    def test_domain_and_manufacturer(self):
        """Test basic domain and manufacturer constants."""
        self.assertEqual(DOMAIN, "iopool")
        self.assertEqual(MANUFACTURER, "iopool")

    def test_config_versions(self):
        """Test configuration version constants."""
        self.assertEqual(CONFIG_VERSION, 1)
        self.assertEqual(CONFIG_MINOR_VERSION, 1)

    def test_configuration_keys(self):
        """Test configuration key constants."""
        self.assertEqual(CONF_API_KEY, "api_key")
        self.assertEqual(CONF_POOL_ID, "pool_id")

    def test_scan_interval(self):
        """Test default scan interval."""
        self.assertIsInstance(DEFAULT_SCAN_INTERVAL, timedelta)
        self.assertEqual(DEFAULT_SCAN_INTERVAL.total_seconds(), 300)  # 5 minutes

    def test_api_endpoints(self):
        """Test API endpoint constants."""
        self.assertEqual(API_BASE_URL, "https://api.iopool.com/v1")
        self.assertEqual(POOLS_ENDPOINT, "https://api.iopool.com/v1/pools")
        self.assertTrue(POOL_ENDPOINT.startswith("https://api.iopool.com/v1/pool/"))
        self.assertIn("{pool_id}", POOL_ENDPOINT)

    def test_sensor_types(self):
        """Test sensor type constants."""
        self.assertEqual(SENSOR_TEMPERATURE, "temperature")
        self.assertEqual(SENSOR_PH, "ph")
        self.assertEqual(SENSOR_ORP, "orp")

    def test_event_types(self):
        """Test event type constants."""
        self.assertEqual(EVENT_TYPE_BOOST_START, "BOOST_START")
        self.assertEqual(EVENT_TYPE_BOOST_END, "BOOST_END")

    def test_constants_are_strings(self):
        """Test that all sensor and event type constants are strings."""
        string_constants = [
            DOMAIN,
            MANUFACTURER,
            CONF_API_KEY,
            CONF_POOL_ID,
            SENSOR_TEMPERATURE,
            SENSOR_PH,
            SENSOR_ORP,
            EVENT_TYPE_BOOST_START,
            EVENT_TYPE_BOOST_END,
        ]
        
        for constant in string_constants:
            self.assertIsInstance(constant, str)
            self.assertGreater(len(constant), 0)


if __name__ == '__main__':
    unittest.main()