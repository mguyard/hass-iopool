"""Test the iopool API models."""

import unittest
from datetime import datetime
import sys
import os

# Add the custom_components directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../custom_components/iopool'))

# Import directly from the module file to avoid __init__.py
from api_models import (
    IopoolLatestMeasure,
    IopoolAdvice,
    IopoolAPIResponsePool,
    IopoolAPIResponse,
)


class TestIopoolAPIModels(unittest.TestCase):
    """Test the iopool API models."""

    def setUp(self):
        """Set up test data."""
        self.measure_data = {
            "temperature": 22.5,
            "ph": 7.2,
            "orp": 650,
            "mode": "standard",
            "isValid": True,
            "ecoId": "eco_123",
            "measuredAt": "2024-01-15T14:30:00Z",
        }
        
        self.advice_data = {
            "filtrationDuration": 8.5,
        }
        
        self.pool_data = {
            "id": "pool_123",
            "title": "Test Pool",
            "mode": "STANDARD",
            "hasAnActionRequired": False,
            "latestMeasure": self.measure_data,
            "advice": self.advice_data,
        }

    def test_iopool_latest_measure_from_dict(self):
        """Test IopoolLatestMeasure.from_dict method."""
        measure = IopoolLatestMeasure.from_dict(self.measure_data)
        
        self.assertEqual(measure.temperature, 22.5)
        self.assertEqual(measure.ph, 7.2)
        self.assertEqual(measure.orp, 650)
        self.assertEqual(measure.mode, "standard")
        self.assertTrue(measure.is_valid)
        self.assertEqual(measure.eco_id, "eco_123")
        self.assertIsInstance(measure.measured_at, datetime)

    def test_iopool_latest_measure_datetime_parsing(self):
        """Test datetime parsing in IopoolLatestMeasure."""
        # Test with Z timezone indicator
        measure_z = IopoolLatestMeasure.from_dict(self.measure_data)
        self.assertIsInstance(measure_z.measured_at, datetime)
        
        # Test with explicit timezone
        data_with_tz = self.measure_data.copy()
        data_with_tz["measuredAt"] = "2024-01-15T14:30:00+02:00"
        measure_tz = IopoolLatestMeasure.from_dict(data_with_tz)
        self.assertIsInstance(measure_tz.measured_at, datetime)

    def test_iopool_advice_from_dict(self):
        """Test IopoolAdvice.from_dict method."""
        advice = IopoolAdvice.from_dict(self.advice_data)
        
        self.assertEqual(advice.filtration_duration, 8.5)

    def test_iopool_advice_from_dict_none(self):
        """Test IopoolAdvice.from_dict with None filtration duration."""
        advice_none = IopoolAdvice.from_dict({})
        
        self.assertIsNone(advice_none.filtration_duration)

    def test_iopool_api_response_pool_from_dict(self):
        """Test IopoolAPIResponsePool.from_dict method."""
        pool = IopoolAPIResponsePool.from_dict(self.pool_data)
        
        self.assertEqual(pool.id, "pool_123")
        self.assertEqual(pool.title, "Test Pool")
        self.assertEqual(pool.mode, "STANDARD")
        self.assertFalse(pool.has_action_required)
        
        # Check latest measure
        self.assertIsNotNone(pool.latest_measure)
        self.assertEqual(pool.latest_measure.temperature, 22.5)
        
        # Check advice
        self.assertIsNotNone(pool.advice)
        self.assertEqual(pool.advice.filtration_duration, 8.5)

    def test_iopool_api_response_pool_from_dict_no_measure(self):
        """Test IopoolAPIResponsePool.from_dict without latest measure."""
        pool_data_no_measure = self.pool_data.copy()
        del pool_data_no_measure["latestMeasure"]
        
        pool = IopoolAPIResponsePool.from_dict(pool_data_no_measure)
        
        self.assertIsNone(pool.latest_measure)
        self.assertIsNotNone(pool.advice)

    def test_iopool_api_response_pool_from_dict_no_advice(self):
        """Test IopoolAPIResponsePool.from_dict without advice."""
        pool_data_no_advice = self.pool_data.copy()
        del pool_data_no_advice["advice"]
        
        pool = IopoolAPIResponsePool.from_dict(pool_data_no_advice)
        
        self.assertIsNotNone(pool.latest_measure)
        self.assertIsNotNone(pool.advice)  # Should create empty advice

    def test_iopool_api_response_from_dict(self):
        """Test IopoolAPIResponse.from_dict method."""
        api_data = [self.pool_data]
        
        response = IopoolAPIResponse.from_dict(api_data)
        
        self.assertEqual(len(response.pools), 1)
        self.assertEqual(response.pools[0].id, "pool_123")
        self.assertEqual(response.pools[0].title, "Test Pool")

    def test_iopool_api_response_from_dict_empty(self):
        """Test IopoolAPIResponse.from_dict with empty data."""
        response = IopoolAPIResponse.from_dict([])
        
        self.assertEqual(len(response.pools), 0)

    def test_iopool_api_response_from_dict_multiple_pools(self):
        """Test IopoolAPIResponse.from_dict with multiple pools."""
        pool_data_2 = self.pool_data.copy()
        pool_data_2["id"] = "pool_456"
        pool_data_2["title"] = "Test Pool 2"
        
        api_data = [self.pool_data, pool_data_2]
        
        response = IopoolAPIResponse.from_dict(api_data)
        
        self.assertEqual(len(response.pools), 2)
        self.assertEqual(response.pools[0].id, "pool_123")
        self.assertEqual(response.pools[1].id, "pool_456")


if __name__ == '__main__':
    unittest.main()