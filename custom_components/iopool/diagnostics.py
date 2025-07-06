"""Diagnostics support for iopool."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "api_key",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    # Get coordinator data
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Prepare diagnostics data
    diagnostics_data = {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "data": None,
    }

    # Add coordinator data if available
    if hasattr(coordinator, "data") and coordinator.data:
        # Create a simplified representation of the data
        # that's safe to include in diagnostics
        pools_data = []
        for pool in coordinator.data.pools:
            pool_data = {
                "id": pool.id,
                "title": pool.title,
                "mode": pool.mode,
                "has_action_required": pool.has_action_required,
            }

            # Add latest measure data if available
            if pool.latest_measure:
                pool_data["latest_measure"] = {
                    "temperature": pool.latest_measure.temperature,
                    "ph": pool.latest_measure.ph,
                    "orp": pool.latest_measure.orp,
                    "mode": pool.latest_measure.mode,
                    "is_valid": pool.latest_measure.is_valid,
                    "measured_at": str(pool.latest_measure.measured_at),
                }

            # Add advice data if available
            if pool.advice:
                pool_data["advice"] = {
                    "filtration_duration": pool.advice.filtration_duration
                }

            pools_data.append(pool_data)

        diagnostics_data["data"] = pools_data

    return diagnostics_data
