"""Test the iopool models."""

import unittest
from datetime import time, timedelta
import sys
import os

# Add the custom_components directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../custom_components/iopool'))

# Import directly from the module file to avoid __init__.py
from models import (
    IopoolOptionsFiltrationSlot,
    IopoolOptionsSummerFiltration,
    IopoolOptionsWinterFiltration,
    IopoolOptionsFiltration,
    IopoolOptionsData,
)


class TestIopoolModels(unittest.TestCase):
    """Test the iopool models."""

    def test_iopool_options_filtration_slot_default(self):
        """Test IopoolOptionsFiltrationSlot with defaults."""
        slot = IopoolOptionsFiltrationSlot()
        
        self.assertIsNone(slot.name)
        self.assertIsNone(slot.start)
        self.assertEqual(slot.duration_percent, 50)

    def test_iopool_options_filtration_slot_with_values(self):
        """Test IopoolOptionsFiltrationSlot with values."""
        start_time = time(10, 30, 0)
        slot = IopoolOptionsFiltrationSlot(
            name="Morning Slot",
            start=start_time,
            duration_percent=75
        )
        
        self.assertEqual(slot.name, "Morning Slot")
        self.assertEqual(slot.start, start_time)
        self.assertEqual(slot.duration_percent, 75)

    def test_iopool_options_summer_filtration_default(self):
        """Test IopoolOptionsSummerFiltration with defaults."""
        summer = IopoolOptionsSummerFiltration()
        
        self.assertFalse(summer.status)
        self.assertIsNone(summer.min_duration)
        self.assertIsNone(summer.max_duration)
        self.assertIsNotNone(summer.slot1)
        self.assertIsNotNone(summer.slot2)

    def test_iopool_options_winter_filtration_default(self):
        """Test IopoolOptionsWinterFiltration with defaults."""
        winter = IopoolOptionsWinterFiltration()
        
        self.assertFalse(winter.status)
        self.assertIsNone(winter.start)
        self.assertIsNone(winter.duration)

    def test_iopool_options_winter_filtration_with_values(self):
        """Test IopoolOptionsWinterFiltration with values."""
        start_time = time(8, 0, 0)
        duration = timedelta(hours=2)
        winter = IopoolOptionsWinterFiltration(
            status=True,
            start=start_time,
            duration=duration
        )
        
        self.assertTrue(winter.status)
        self.assertEqual(winter.start, start_time)
        self.assertEqual(winter.duration, duration)

    def test_iopool_options_filtration_default(self):
        """Test IopoolOptionsFiltration with defaults."""
        filtration = IopoolOptionsFiltration()
        
        self.assertIsNone(filtration.switch_entity)
        self.assertIsNotNone(filtration.summer_filtration)
        self.assertIsNotNone(filtration.winter_filtration)

    def test_iopool_options_data_default(self):
        """Test IopoolOptionsData with defaults."""
        options = IopoolOptionsData()
        
        self.assertIsNotNone(options.filtration)

    def test_iopool_options_data_from_dict_empty(self):
        """Test IopoolOptionsData.from_dict with empty data."""
        options = IopoolOptionsData.from_dict({})
        
        self.assertIsNotNone(options.filtration)
        self.assertIsNone(options.filtration.switch_entity)

    def test_iopool_options_data_from_dict_none(self):
        """Test IopoolOptionsData.from_dict with None."""
        options = IopoolOptionsData.from_dict(None)
        
        self.assertIsNotNone(options.filtration)

    def test_iopool_options_data_from_dict_full(self):
        """Test IopoolOptionsData.from_dict with full data."""
        data = {
            "filtration": {
                "switch_entity": "switch.pool_pump",
                "summer_filtration": {
                    "status": True,
                    "min_duration": 4,
                    "max_duration": 12,
                    "slot1": {
                        "name": "Morning",
                        "start": "08:00:00",
                        "duration_percent": 60
                    },
                    "slot2": {
                        "name": "Evening",
                        "start": "20:00:00",
                        "duration_percent": 40
                    }
                },
                "winter_filtration": {
                    "status": True,
                    "start": "10:00:00",
                    "duration": 120  # minutes
                }
            }
        }
        
        options = IopoolOptionsData.from_dict(data)
        
        # Check filtration
        self.assertEqual(options.filtration.switch_entity, "switch.pool_pump")
        
        # Check summer filtration
        self.assertTrue(options.filtration.summer_filtration.status)
        self.assertEqual(options.filtration.summer_filtration.min_duration, 4)
        self.assertEqual(options.filtration.summer_filtration.max_duration, 12)
        
        # Check slot1
        slot1 = options.filtration.summer_filtration.slot1
        self.assertEqual(slot1.name, "Morning")
        self.assertEqual(slot1.start, time(8, 0, 0))
        self.assertEqual(slot1.duration_percent, 60)
        
        # Check slot2
        slot2 = options.filtration.summer_filtration.slot2
        self.assertEqual(slot2.name, "Evening")
        self.assertEqual(slot2.start, time(20, 0, 0))
        self.assertEqual(slot2.duration_percent, 40)
        
        # Check winter filtration
        self.assertTrue(options.filtration.winter_filtration.status)
        self.assertEqual(options.filtration.winter_filtration.start, time(10, 0, 0))
        self.assertEqual(options.filtration.winter_filtration.duration, timedelta(minutes=120))

    def test_iopool_options_data_to_dict(self):
        """Test IopoolOptionsData.to_dict method."""
        # Create options with data
        slot1 = IopoolOptionsFiltrationSlot(
            name="Morning",
            start=time(8, 0, 0),
            duration_percent=60
        )
        slot2 = IopoolOptionsFiltrationSlot(
            name="Evening",
            start=time(20, 0, 0),
            duration_percent=40
        )
        summer = IopoolOptionsSummerFiltration(
            status=True,
            min_duration=4,
            max_duration=12,
            slot1=slot1,
            slot2=slot2
        )
        winter = IopoolOptionsWinterFiltration(
            status=True,
            start=time(10, 0, 0),
            duration=timedelta(minutes=120)
        )
        filtration = IopoolOptionsFiltration(
            switch_entity="switch.pool_pump",
            summer_filtration=summer,
            winter_filtration=winter
        )
        options = IopoolOptionsData(filtration=filtration)
        
        # Convert to dict
        result = options.to_dict()
        
        # Verify structure
        self.assertIn("filtration", result)
        self.assertEqual(result["filtration"]["switch_entity"], "switch.pool_pump")
        
        # Verify summer filtration
        summer_data = result["filtration"]["summer_filtration"]
        self.assertTrue(summer_data["status"])
        self.assertEqual(summer_data["min_duration"], 4)
        self.assertEqual(summer_data["max_duration"], 12)
        
        # Verify slots
        self.assertEqual(summer_data["slot1"]["name"], "Morning")
        self.assertEqual(summer_data["slot1"]["start"], "08:00:00")
        self.assertEqual(summer_data["slot1"]["duration_percent"], 60)
        
        # Verify winter filtration
        winter_data = result["filtration"]["winter_filtration"]
        self.assertTrue(winter_data["status"])
        self.assertEqual(winter_data["start"], "10:00:00")
        self.assertEqual(winter_data["duration"], 120)

    def test_time_parsing_edge_cases(self):
        """Test time parsing with various edge cases."""
        # Test with invalid time strings
        data_invalid_time = {
            "filtration": {
                "summer_filtration": {
                    "slot1": {
                        "start": "invalid_time"
                    }
                },
                "winter_filtration": {
                    "start": "25:00:00"  # Invalid hour
                }
            }
        }
        
        options = IopoolOptionsData.from_dict(data_invalid_time)
        
        # Should handle invalid times gracefully
        self.assertIsNone(options.filtration.summer_filtration.slot1.start)
        self.assertIsNone(options.filtration.winter_filtration.start)

    def test_round_trip_conversion(self):
        """Test that data survives a round trip conversion."""
        original_data = {
            "filtration": {
                "switch_entity": "switch.pool_pump",
                "summer_filtration": {
                    "status": True,
                    "min_duration": 6,
                    "max_duration": 10,
                    "slot1": {
                        "name": "Morning",
                        "start": "09:00:00",
                        "duration_percent": 70
                    },
                    "slot2": {
                        "name": "Afternoon",
                        "start": "15:00:00",
                        "duration_percent": 30
                    }
                },
                "winter_filtration": {
                    "status": False,
                    "start": "12:00:00",
                    "duration": 90
                }
            }
        }
        
        # Convert to model and back
        options = IopoolOptionsData.from_dict(original_data)
        result_data = options.to_dict()
        
        # Compare key values (structure should be preserved)
        self.assertEqual(
            result_data["filtration"]["switch_entity"],
            original_data["filtration"]["switch_entity"]
        )
        self.assertEqual(
            result_data["filtration"]["summer_filtration"]["status"],
            original_data["filtration"]["summer_filtration"]["status"]
        )
        self.assertEqual(
            result_data["filtration"]["winter_filtration"]["duration"],
            original_data["filtration"]["winter_filtration"]["duration"]
        )


if __name__ == '__main__':
    unittest.main()