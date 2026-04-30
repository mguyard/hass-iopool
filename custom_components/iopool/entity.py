"""Base entity classes for iopool integration."""

from __future__ import annotations

import re
import unicodedata

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api_models import IopoolAPIResponsePool
from .const import DOMAIN, MANUFACTURER
from .coordinator import IopoolDataUpdateCoordinator


def slugify_pool_name(name: str) -> str:
    """Convert a pool name to a valid entity ID slug.

    Normalizes accented characters, lowercases, and replaces any sequence
    of non-alphanumeric characters with a single underscore.
    """
    # Normalize accented characters via NFKD: à→a, é→e, ç→c, etc.
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    # Replace any sequence of non [a-z0-9] chars with a single underscore
    slugged = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower())
    return slugged.strip("_")


class IopoolEntity(CoordinatorEntity, RestoreEntity):
    """Base class for all iopool entities."""

    coordinator: IopoolDataUpdateCoordinator

    def __init__(
        self,
        coordinator: IopoolDataUpdateCoordinator,
        config_entry_id: str,
        pool_id: str,
        pool_name: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._pool_id = pool_id
        self._pool_name = pool_name
        self._config_entry_id = config_entry_id
        self._attr_has_entity_name = True

    def _get_pool(self) -> IopoolAPIResponsePool | None:
        """Get the pool data from coordinator."""
        if not self.coordinator.data:
            return None

        return next(
            (pool for pool in self.coordinator.data.pools if pool.id == self._pool_id),
            None,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        pool = self._get_pool()

        # If pool not found or no latest measure, return minimal device info
        if not pool or not pool.latest_measure:
            return DeviceInfo(
                identifiers={(DOMAIN, self._pool_id)},
                name=self._pool_name,
                manufacturer=MANUFACTURER,
                model="iopool ECO",
            )

        # Return complete device info with up-to-date data
        return DeviceInfo(
            identifiers={(DOMAIN, self._pool_id)},
            name=pool.title,
            manufacturer=MANUFACTURER,
            model="iopool ECO",
            hw_version=pool.latest_measure.eco_id,
        )
