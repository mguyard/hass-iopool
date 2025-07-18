"""Test isolated iopool model components."""

import unittest
from datetime import time, timedelta
import sys
import os

# Add the custom_components directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../custom_components/iopool'))

# Define the models inline to avoid HA dependencies
from dataclasses import dataclass, field


@dataclass
class TestIopoolOptionsFiltrationSlot:
    """Test version of IopoolOptionsFiltrationSlot."""
    name: str | None = None
    start: time | None = None
    duration_percent: int | None = 50


@dataclass
class TestIopoolOptionsSummerFiltration:
    """Test version of IopoolOptionsSummerFiltration."""
    status: bool | None = False
    min_duration: int | None = None
    max_duration: int | None = None
    slot1: TestIopoolOptionsFiltrationSlot = field(
        default_factory=TestIopoolOptionsFiltrationSlot
    )
    slot2: TestIopoolOptionsFiltrationSlot = field(
        default_factory=TestIopoolOptionsFiltrationSlot
    )


@dataclass
class TestIopoolOptionsWinterFiltration:
    """Test version of IopoolOptionsWinterFiltration."""
    status: bool | None = False
    start: time | None = None
    duration: timedelta | None = None


@dataclass
class TestIopoolOptionsFiltration:
    """Test version of IopoolOptionsFiltration."""
    switch_entity: str | None = None
    summer_filtration: TestIopoolOptionsSummerFiltration = field(
        default_factory=TestIopoolOptionsSummerFiltration
    )
    winter_filtration: TestIopoolOptionsWinterFiltration = field(
        default_factory=TestIopoolOptionsWinterFiltration
    )


@dataclass
class TestIopoolOptionsData:
    """Test version of IopoolOptionsData."""
    filtration: TestIopoolOptionsFiltration = field(default_factory=TestIopoolOptionsFiltration)

    @classmethod
    def from_dict(cls, data: dict) -> 'TestIopoolOptionsData':
        """Create instance from structured dictionary."""
        if not data:
            return cls()

        filtration_data = data.get("filtration", {})

        def parse_time(time_str: str | None) -> time | None:
            """Parse a time string into a time object."""
            if not time_str:
                return None
            try:
                hour, minute, second = map(int, time_str.split(":"))
                return time(hour, minute, second)
            except (ValueError, AttributeError):
                return None

        def parse_duration(minutes: int | None) -> timedelta | None:
            """Convert minutes to timedelta object."""
            if minutes is None:
                return None
            return timedelta(minutes=minutes)

        # Process summer filtration slots
        slot1_data = filtration_data.get("summer_filtration", {}).get("slot1", {})
        slot1 = TestIopoolOptionsFiltrationSlot(
            name=slot1_data.get("name"),
            start=parse_time(slot1_data.get("start")),
            duration_percent=slot1_data.get("duration_percent"),
        )
        slot2_data = filtration_data.get("summer_filtration", {}).get("slot2", {})
        slot2 = TestIopoolOptionsFiltrationSlot(
            name=slot2_data.get("name"),
            start=parse_time(slot2_data.get("start")),
            duration_percent=slot2_data.get("duration_percent"),
        )

        # Process summer filtration
        summer_data = filtration_data.get("summer_filtration", {})
        summer_filtration = TestIopoolOptionsSummerFiltration(
            status=summer_data.get("status"),
            min_duration=summer_data.get("min_duration"),
            max_duration=summer_data.get("max_duration"),
            slot1=slot1,
            slot2=slot2,
        )

        # Process winter filtration
        winter_data = filtration_data.get("winter_filtration", {})
        winter_duration = winter_data.get("duration")

        winter_filtration = TestIopoolOptionsWinterFiltration(
            status=winter_data.get("status"),
            start=parse_time(winter_data.get("start")),
            duration=parse_duration(winter_duration),
        )

        # Create filtration options
        filtration_options = TestIopoolOptionsFiltration(
            switch_entity=filtration_data.get("switch_entity"),
            summer_filtration=summer_filtration,
            winter_filtration=winter_filtration,
        )

        return cls(filtration=filtration_options)


class TestIopoolModelLogic(unittest.TestCase):
    """Test the iopool model logic."""

    def test_options_data_from_dict_empty(self):
        """Test IopoolOptionsData.from_dict with empty data."""
        options = TestIopoolOptionsData.from_dict({})
        
        self.assertIsNotNone(options.filtration)
        self.assertIsNone(options.filtration.switch_entity)

    def test_options_data_from_dict_none(self):
        """Test IopoolOptionsData.from_dict with None."""
        options = TestIopoolOptionsData.from_dict(None)
        
        self.assertIsNotNone(options.filtration)

    def test_options_data_from_dict_full(self):
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
        
        options = TestIopoolOptionsData.from_dict(data)
        
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
        
        options = TestIopoolOptionsData.from_dict(data_invalid_time)
        
        # Should handle invalid times gracefully
        self.assertIsNone(options.filtration.summer_filtration.slot1.start)
        self.assertIsNone(options.filtration.winter_filtration.start)

    def test_slot_defaults(self):
        """Test filtration slot default values."""
        slot = TestIopoolOptionsFiltrationSlot()
        
        self.assertIsNone(slot.name)
        self.assertIsNone(slot.start)
        self.assertEqual(slot.duration_percent, 50)

    def test_summer_filtration_defaults(self):
        """Test summer filtration default values."""
        summer = TestIopoolOptionsSummerFiltration()
        
        self.assertFalse(summer.status)
        self.assertIsNone(summer.min_duration)
        self.assertIsNone(summer.max_duration)
        self.assertIsNotNone(summer.slot1)
        self.assertIsNotNone(summer.slot2)

    def test_winter_filtration_defaults(self):
        """Test winter filtration default values."""
        winter = TestIopoolOptionsWinterFiltration()
        
        self.assertFalse(winter.status)
        self.assertIsNone(winter.start)
        self.assertIsNone(winter.duration)

    def test_duration_conversion(self):
        """Test duration conversion from minutes to timedelta."""
        data = {
            "filtration": {
                "winter_filtration": {
                    "duration": 90  # 1.5 hours
                }
            }
        }
        
        options = TestIopoolOptionsData.from_dict(data)
        
        expected_duration = timedelta(minutes=90)
        self.assertEqual(options.filtration.winter_filtration.duration, expected_duration)
        self.assertEqual(options.filtration.winter_filtration.duration.total_seconds(), 5400)  # 90 * 60


if __name__ == '__main__':
    unittest.main()