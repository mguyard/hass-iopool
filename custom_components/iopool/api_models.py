"""The iopool integration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class IopoolLatestMeasure:
    """IopoolLatestMeasure is a TypedDict that defines the latest measure data for iopool integration."""

    temperature: float
    ph: float
    orp: float
    mode: Literal["standard", "live", "maintenance", "manual", "backup", "gateway"]
    is_valid: bool
    eco_id: str
    measured_at: datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IopoolLatestMeasure:
        """Create instance from API response dictionary."""
        temperature: float = data["temperature"]
        ph: float = data["ph"]
        orp: float = data["orp"]
        mode: Literal[
            "standard", "live", "maintenance", "manual", "backup", "gateway"
        ] = data["mode"]
        is_valid: bool = data["isValid"]
        eco_id: str = data["ecoId"]
        measured_at_str: str = data["measuredAt"]
        # Convert ISO 8601 format string to datetime
        # Handle the 'Z' timezone indicator by replacing with +00:00
        if measured_at_str.endswith("Z"):
            measured_at_str = measured_at_str[:-1] + "+00:00"
        measured_at: datetime = datetime.fromisoformat(measured_at_str)

        return cls(
            temperature=temperature,
            ph=ph,
            orp=orp,
            mode=mode,
            is_valid=is_valid,
            eco_id=eco_id,
            measured_at=measured_at,
        )


@dataclass
class IopoolAdvice:
    """IopoolAdvice is a TypedDict that defines the advice data for iopool integration."""

    filtration_duration: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IopoolAdvice:
        """Create instance from API response dictionary."""
        filtration_duration: float | None = data.get("filtrationDuration")

        return cls(
            filtration_duration=filtration_duration,
        )


@dataclass
class IopoolAPIResponsePool:
    """IopoolAPIResponsePool is a TypedDict that defines the pool data for iopool integration."""

    id: str
    title: str
    mode: Literal["STANDARD", "OPENING", "ACTIVE_WINTER", "WINTER", "INITIALIZATION"]
    has_action_required: bool
    latest_measure: IopoolLatestMeasure | None = None
    advice: IopoolAdvice | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IopoolAPIResponsePool:
        """Create instance from API response dictionary."""
        id_pool: str = data["id"]
        title: str = data["title"]
        mode: Literal[
            "STANDARD", "OPENING", "ACTIVE_WINTER", "WINTER", "INITIALIZATION"
        ] = data["mode"]
        has_action_required: bool = data["hasAnActionRequired"]

        latest_measure: IopoolLatestMeasure | None = None
        if data.get("latestMeasure"):
            latest_measure = IopoolLatestMeasure.from_dict(data["latestMeasure"])

        advice_data = data.get("advice", {})
        advice: IopoolAdvice | None = (
            IopoolAdvice()
            if advice_data is None
            else IopoolAdvice.from_dict(advice_data)
        )

        return cls(
            id=id_pool,
            title=title,
            mode=mode,
            has_action_required=has_action_required,
            latest_measure=latest_measure,
            advice=advice,
        )


@dataclass
class IopoolAPIResponse:
    """IopoolAPIResponse represents a collection of iopool pool data objects."""

    pools: list[IopoolAPIResponsePool] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: list[dict[str, Any]]) -> IopoolAPIResponse:
        """Create instance from API response dictionary."""
        pools: list[IopoolAPIResponsePool] = [
            IopoolAPIResponsePool.from_dict(pool_data) for pool_data in data
        ]

        return cls(pools=pools)
