"""The iopool integration models."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import time, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import CONF_API_KEY, CONF_POOL_ID
from .coordinator import IopoolDataUpdateCoordinator

# Define a type alias for the config entry
type IopoolConfigEntry = ConfigEntry[IopoolData]


@dataclass
class IopoolData:
    """Data class for Iopool integration.

    This class stores essential components needed for the Iopool integration to function:
    - Configuration data
    - Data update coordinator
    - Filtration information
    - Listeners for time events
    - Setup time events function

    Attributes:
        config: Configuration data for the Iopool integration
        coordinator: The data update coordinator that manages polling and data updates
        filtration: Information about the pool filtration system
        remove_time_listeners: A list of functions to remove time listeners
        setup_time_events: A function to set up time events for filtration scheduling

    """

    config: IopoolConfigData
    coordinator: IopoolDataUpdateCoordinator
    filtration: Any
    remove_time_listeners: list[Callable[[], None]] = field(default_factory=list)
    setup_time_events: Callable[[], None] | None = None


@dataclass
class IopoolOptionsFiltrationSlot:
    """iopoolOptionsFiltrationSlot defines the summer filtration slot options."""

    name: str | None = None
    start: time | None = None
    duration_percent: int | None = 50


@dataclass
class IopoolOptionsSummerFiltration:
    """iopoolOptionsFiltration defines the summer filtration options."""

    status: bool | None = False
    min_duration: int | None = None
    max_duration: int | None = None
    slot1: IopoolOptionsFiltrationSlot = field(
        default_factory=IopoolOptionsFiltrationSlot
    )
    slot2: IopoolOptionsFiltrationSlot = field(
        default_factory=IopoolOptionsFiltrationSlot
    )


@dataclass
class IopoolOptionsWinterFiltration:
    """iopoolOptionsFiltration defines the winter filtration options."""

    status: bool | None = False
    start: time | None = None
    duration: timedelta | None = None


@dataclass
class IopoolOptionsFiltration:
    """iopoolOptionsFiltration defines the filtration options."""

    switch_entity: str | None = None
    summer_filtration: IopoolOptionsSummerFiltration = field(
        default_factory=IopoolOptionsSummerFiltration
    )
    winter_filtration: IopoolOptionsWinterFiltration = field(
        default_factory=IopoolOptionsWinterFiltration
    )


@dataclass
class IopoolOptionsData:
    """iopoolOptionsData defines the options data for iopool integration."""

    filtration: IopoolOptionsFiltration = field(default_factory=IopoolOptionsFiltration)

    @classmethod
    def from_dict(cls, data: dict) -> IopoolOptionsData:
        """Create instance from structured dictionary.

        Args:
            data: A structured dictionary representing options

        Returns:
            A properly structured IopoolOptionsData instance

        """
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
        slot1 = IopoolOptionsFiltrationSlot(
            name=slot1_data.get("name"),
            start=parse_time(slot1_data.get("start")),
            duration_percent=slot1_data.get("duration_percent"),
        )
        slot2_data = filtration_data.get("summer_filtration", {}).get("slot2", {})
        slot2 = IopoolOptionsFiltrationSlot(
            name=slot2_data.get("name"),
            start=parse_time(slot2_data.get("start")),
            duration_percent=slot2_data.get("duration_percent"),
        )

        # Process summer filtration
        summer_data = filtration_data.get("summer_filtration", {})
        summer_filtration = IopoolOptionsSummerFiltration(
            status=summer_data.get("status"),
            min_duration=summer_data.get("min_duration"),
            max_duration=summer_data.get("max_duration"),
            slot1=slot1,
            slot2=slot2,
        )

        # Process winter filtration
        winter_data = filtration_data.get("winter_filtration", {})
        winter_duration = winter_data.get("duration")

        winter_filtration = IopoolOptionsWinterFiltration(
            status=winter_data.get("status"),
            start=parse_time(winter_data.get("start")),
            duration=parse_duration(winter_duration),
        )

        # Create filtration options
        filtration_options = IopoolOptionsFiltration(
            switch_entity=filtration_data.get("switch_entity"),
            summer_filtration=summer_filtration,
            winter_filtration=winter_filtration,
        )

        return cls(filtration=filtration_options)

    def to_dict(self) -> dict:
        """Convert the instance to a dictionary.

        Returns:
            A dictionary representation of the options

        """

        # Function to format time object to string
        def format_time(time_obj) -> str | None:
            """Format time object to string."""
            if time_obj is None:
                return None
            return time_obj.strftime("%H:%M:%S")

        def format_duration(duration) -> int | None:
            """Convert timedelta to minutes."""
            if duration is None:
                return None
            return int(duration.total_seconds() / 60)

        # Process summer filtration slots
        slot1_dict = {
            "name": self.filtration.summer_filtration.slot1.name,
            "start": format_time(self.filtration.summer_filtration.slot1.start),
            "duration_percent": self.filtration.summer_filtration.slot1.duration_percent,
        }

        slot2_dict = {
            "name": self.filtration.summer_filtration.slot2.name,
            "start": format_time(self.filtration.summer_filtration.slot2.start),
            "duration_percent": self.filtration.summer_filtration.slot2.duration_percent,
        }

        # Process summer filtration
        summer_dict = {
            "status": self.filtration.summer_filtration.status,
            "min_duration": self.filtration.summer_filtration.min_duration,
            "max_duration": self.filtration.summer_filtration.max_duration,
            "slot1": slot1_dict,
            "slot2": slot2_dict,
        }

        # Process winter filtration
        winter_dict = {
            "status": self.filtration.winter_filtration.status,
            "start": format_time(self.filtration.winter_filtration.start),
            "duration": format_duration(self.filtration.winter_filtration.duration),
        }

        # Build complete dictionary
        return {
            "filtration": {
                "switch_entity": self.filtration.switch_entity,
                "summer_filtration": summer_dict,
                "winter_filtration": winter_dict,
            }
        }

    @classmethod
    def from_config_flow_data(cls, data: dict) -> IopoolOptionsData:
        """Create instance from config flow data.

        Args:
            data: The flattened data from the config flow

        Returns:
            A properly structured IopoolOptionsData instance

        """
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

        def safe_int(value) -> int | None:
            """Safely convert a value to int."""
            if value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        # Create slot objects
        slot1 = IopoolOptionsFiltrationSlot(
            name=filtration_data.get("summer_filtration.slot1.name"),
            start=parse_time(filtration_data.get("summer_filtration.slot1.start")),
            duration_percent=safe_int(
                filtration_data.get("summer_filtration.slot1.duration_percent")
            ),
        )
        slot2 = IopoolOptionsFiltrationSlot(
            name=filtration_data.get("summer_filtration.slot2.name"),
            start=parse_time(filtration_data.get("summer_filtration.slot2.start")),
            duration_percent=safe_int(
                filtration_data.get("summer_filtration.slot2.duration_percent")
            ),
        )

        # Create summer filtration object
        summer_filtration = IopoolOptionsSummerFiltration(
            status=filtration_data.get("summer_filtration.status", False),
            min_duration=safe_int(
                filtration_data.get("summer_filtration.min_duration")
            ),
            max_duration=safe_int(
                filtration_data.get("summer_filtration.max_duration")
            ),
            slot1=slot1,
            slot2=slot2,
        )

        # Create winter filtration object
        winter_duration_minutes = safe_int(
            filtration_data.get("winter_filtration.duration")
        )
        winter_duration = (
            timedelta(minutes=winter_duration_minutes)
            if winter_duration_minutes is not None
            else None
        )
        winter_filtration = IopoolOptionsWinterFiltration(
            status=filtration_data.get("winter_filtration.status", False),
            start=parse_time(filtration_data.get("winter_filtration.start")),
            duration=winter_duration,
        )

        # Create filtration options
        filtration_options = IopoolOptionsFiltration(
            switch_entity=filtration_data.get("switch_entity"),
            summer_filtration=summer_filtration,
            winter_filtration=winter_filtration,
        )

        # Create and return the options data
        return cls(filtration=filtration_options)


@dataclass
class IopoolConfigData:
    """A class representing IOPool configuration data.

    This class encapsulates the configuration settings needed for the IOPool integration,
    including the API key and options.

    Attributes:
        api_key (str): The API key used for authenticating with the IOPool service.
        pool_id (str): The ID of the pool associated with this configuration.
        options (IopoolOptionsData): Configuration options for the IOPool integration.

    """

    api_key: str
    pool_id: str
    options: IopoolOptionsData

    @classmethod
    def from_config_entry(cls, entry: ConfigEntry) -> IopoolConfigData:
        """Create instance from configuration entry."""
        return cls(
            api_key=entry.data[CONF_API_KEY],
            pool_id=entry.data[CONF_POOL_ID],
            options=IopoolOptionsData(**entry.options),
        )
