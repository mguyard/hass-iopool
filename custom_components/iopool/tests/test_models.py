"""Test the iopool models module."""

from datetime import time, timedelta
from unittest.mock import MagicMock

from custom_components.iopool.models import (
    IopoolConfigData,
    IopoolData,
    IopoolOptionsData,
    IopoolOptionsFiltration,
    IopoolOptionsFiltrationSlot,
    IopoolOptionsSummerFiltration,
    IopoolOptionsWinterFiltration,
)


class TestIopoolOptionsFiltrationSlot:
    """Test class for IopoolOptionsFiltrationSlot."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        slot = IopoolOptionsFiltrationSlot()
        assert slot.name is None
        assert slot.start is None
        assert slot.duration_percent == 50

    def test_init_with_values(self) -> None:
        """Test initialization with values."""
        start_time = time(8, 0, 0)
        slot = IopoolOptionsFiltrationSlot(
            name="Morning", start=start_time, duration_percent=75
        )
        assert slot.name == "Morning"
        assert slot.start == start_time
        assert slot.duration_percent == 75


class TestIopoolOptionsSummerFiltration:
    """Test class for IopoolOptionsSummerFiltration."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        summer = IopoolOptionsSummerFiltration()
        assert summer.status is False
        assert summer.min_duration is None
        assert summer.max_duration is None
        assert isinstance(summer.slot1, IopoolOptionsFiltrationSlot)
        assert isinstance(summer.slot2, IopoolOptionsFiltrationSlot)

    def test_init_with_values(self) -> None:
        """Test initialization with values."""
        slot1 = IopoolOptionsFiltrationSlot(name="Morning")
        slot2 = IopoolOptionsFiltrationSlot(name="Evening")
        summer = IopoolOptionsSummerFiltration(
            status=True, min_duration=60, max_duration=480, slot1=slot1, slot2=slot2
        )
        assert summer.status is True
        assert summer.min_duration == 60
        assert summer.max_duration == 480
        assert summer.slot1.name == "Morning"
        assert summer.slot2.name == "Evening"


class TestIopoolOptionsWinterFiltration:
    """Test class for IopoolOptionsWinterFiltration."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        winter = IopoolOptionsWinterFiltration()
        assert winter.status is False
        assert winter.start is None
        assert winter.duration is None

    def test_init_with_values(self) -> None:
        """Test initialization with values."""
        start_time = time(10, 0, 0)
        duration = timedelta(minutes=120)
        winter = IopoolOptionsWinterFiltration(
            status=True, start=start_time, duration=duration
        )
        assert winter.status is True
        assert winter.start == start_time
        assert winter.duration == duration


class TestIopoolOptionsFiltration:
    """Test class for IopoolOptionsFiltration."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        filtration = IopoolOptionsFiltration()
        assert filtration.switch_entity is None
        assert isinstance(filtration.summer_filtration, IopoolOptionsSummerFiltration)
        assert isinstance(filtration.winter_filtration, IopoolOptionsWinterFiltration)

    def test_init_with_values(self) -> None:
        """Test initialization with values."""
        summer = IopoolOptionsSummerFiltration(status=True)
        winter = IopoolOptionsWinterFiltration(status=True)
        filtration = IopoolOptionsFiltration(
            switch_entity="switch.pool_pump",
            summer_filtration=summer,
            winter_filtration=winter,
        )
        assert filtration.switch_entity == "switch.pool_pump"
        assert filtration.summer_filtration.status is True
        assert filtration.winter_filtration.status is True


class TestIopoolOptionsData:
    """Test class for IopoolOptionsData."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        options = IopoolOptionsData()
        assert isinstance(options.filtration, IopoolOptionsFiltration)

    def test_from_dict_empty(self) -> None:
        """Test from_dict with empty data."""
        options = IopoolOptionsData.from_dict({})
        assert isinstance(options.filtration, IopoolOptionsFiltration)

    def test_from_dict_none(self) -> None:
        """Test from_dict with None data."""
        options = IopoolOptionsData.from_dict(None)
        assert isinstance(options.filtration, IopoolOptionsFiltration)

    def test_from_dict_complete(self) -> None:
        """Test from_dict with complete data."""
        data = {
            "filtration": {
                "switch_entity": "switch.pool_pump",
                "summer_filtration": {
                    "status": True,
                    "min_duration": 60,
                    "max_duration": 480,
                    "slot1": {
                        "name": "Morning",
                        "start": "08:00:00",
                        "duration_percent": 50,
                    },
                    "slot2": {
                        "name": "Evening",
                        "start": "20:00:00",
                        "duration_percent": 50,
                    },
                },
                "winter_filtration": {
                    "status": True,
                    "start": "10:00:00",
                    "duration": 120,
                },
            }
        }

        options = IopoolOptionsData.from_dict(data)

        # Check filtration options
        assert options.filtration.switch_entity == "switch.pool_pump"

        # Check summer filtration
        summer = options.filtration.summer_filtration
        assert summer.status is True
        assert summer.min_duration == 60
        assert summer.max_duration == 480

        # Check summer slots
        assert summer.slot1.name == "Morning"
        assert summer.slot1.start == time(8, 0, 0)
        assert summer.slot1.duration_percent == 50

        assert summer.slot2.name == "Evening"
        assert summer.slot2.start == time(20, 0, 0)
        assert summer.slot2.duration_percent == 50

        # Check winter filtration
        winter = options.filtration.winter_filtration
        assert winter.status is True
        assert winter.start == time(10, 0, 0)
        assert winter.duration == timedelta(minutes=120)

    def test_from_dict_invalid_time(self) -> None:
        """Test from_dict with invalid time format."""
        data = {
            "filtration": {
                "summer_filtration": {"slot1": {"start": "invalid_time"}},
                "winter_filtration": {"start": "not_a_time"},
            }
        }

        options = IopoolOptionsData.from_dict(data)

        # Should handle invalid times gracefully
        assert options.filtration.summer_filtration.slot1.start is None
        assert options.filtration.winter_filtration.start is None

    def test_from_dict_partial_data(self) -> None:
        """Test from_dict with partial data."""
        data = {
            "filtration": {
                "switch_entity": "switch.test",
                "summer_filtration": {"status": True},
            }
        }

        options = IopoolOptionsData.from_dict(data)

        assert options.filtration.switch_entity == "switch.test"
        assert options.filtration.summer_filtration.status is True
        # Winter filtration defaults to None when not specified in data
        assert options.filtration.winter_filtration.status is None

    def test_to_dict_default(self) -> None:
        """Test to_dict with default values."""
        options = IopoolOptionsData()
        result = options.to_dict()

        expected = {
            "filtration": {
                "switch_entity": None,
                "summer_filtration": {
                    "status": False,
                    "min_duration": None,
                    "max_duration": None,
                    "slot1": {"name": None, "start": None, "duration_percent": 50},
                    "slot2": {"name": None, "start": None, "duration_percent": 50},
                },
                "winter_filtration": {"status": False, "start": None, "duration": None},
            }
        }

        assert result == expected

    def test_to_dict_with_values(self) -> None:
        """Test to_dict with actual values."""
        # Create test data
        slot1 = IopoolOptionsFiltrationSlot(
            name="Morning", start=time(8, 0, 0), duration_percent=60
        )
        slot2 = IopoolOptionsFiltrationSlot(
            name="Evening", start=time(20, 0, 0), duration_percent=40
        )
        summer = IopoolOptionsSummerFiltration(
            status=True, min_duration=60, max_duration=480, slot1=slot1, slot2=slot2
        )
        winter = IopoolOptionsWinterFiltration(
            status=True, start=time(10, 30, 0), duration=timedelta(minutes=90)
        )
        filtration = IopoolOptionsFiltration(
            switch_entity="switch.pool_pump",
            summer_filtration=summer,
            winter_filtration=winter,
        )
        options = IopoolOptionsData(filtration=filtration)

        result = options.to_dict()

        # Verify the result
        assert result["filtration"]["switch_entity"] == "switch.pool_pump"

        summer_result = result["filtration"]["summer_filtration"]
        assert summer_result["status"] is True
        assert summer_result["min_duration"] == 60
        assert summer_result["max_duration"] == 480

        assert summer_result["slot1"]["name"] == "Morning"
        assert summer_result["slot1"]["start"] == "08:00:00"
        assert summer_result["slot1"]["duration_percent"] == 60

        assert summer_result["slot2"]["name"] == "Evening"
        assert summer_result["slot2"]["start"] == "20:00:00"
        assert summer_result["slot2"]["duration_percent"] == 40

        winter_result = result["filtration"]["winter_filtration"]
        assert winter_result["status"] is True
        assert winter_result["start"] == "10:30:00"
        assert winter_result["duration"] == 90

    def test_roundtrip_conversion(self) -> None:
        """Test that from_dict and to_dict are inverse operations."""
        original_data = {
            "filtration": {
                "switch_entity": "switch.pool_pump",
                "summer_filtration": {
                    "status": True,
                    "min_duration": 60,
                    "max_duration": 480,
                    "slot1": {
                        "name": "Morning",
                        "start": "08:00:00",
                        "duration_percent": 50,
                    },
                    "slot2": {
                        "name": "Evening",
                        "start": "20:00:00",
                        "duration_percent": 50,
                    },
                },
                "winter_filtration": {
                    "status": True,
                    "start": "10:00:00",
                    "duration": 120,
                },
            }
        }

        # Convert to object and back to dict
        options = IopoolOptionsData.from_dict(original_data)
        result_data = options.to_dict()

        # Should be the same
        assert result_data == original_data


class TestIopoolConfigData:
    """Test class for IopoolConfigData."""

    def test_init(self) -> None:
        """Test IopoolConfigData initialization."""
        pool_id = "test_pool_id"
        api_key = "test_api_key"
        options = IopoolOptionsData()

        config = IopoolConfigData(pool_id=pool_id, api_key=api_key, options=options)

        assert config.pool_id == pool_id
        assert config.api_key == api_key
        assert config.options == options


class TestIopoolData:
    """Test class for IopoolData."""

    def test_init_default(self) -> None:
        """Test IopoolData initialization with defaults."""
        config = MagicMock()
        coordinator = MagicMock()
        filtration = MagicMock()

        data = IopoolData(config=config, coordinator=coordinator, filtration=filtration)

        assert data.config == config
        assert data.coordinator == coordinator
        assert data.filtration == filtration
        assert data.remove_time_listeners == []
        assert data.setup_time_events is None

    def test_init_with_values(self) -> None:
        """Test IopoolData initialization with values."""
        config = MagicMock()
        coordinator = MagicMock()
        filtration = MagicMock()
        listeners = [MagicMock(), MagicMock()]
        setup_func = MagicMock()

        data = IopoolData(
            config=config,
            coordinator=coordinator,
            filtration=filtration,
            remove_time_listeners=listeners,
            setup_time_events=setup_func,
        )

        assert data.config == config
        assert data.coordinator == coordinator
        assert data.filtration == filtration
        assert data.remove_time_listeners == listeners
        assert data.setup_time_events == setup_func
