"""Home Assistant fixtures for iopool tests."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.core import HomeAssistant


@pytest.fixture
def hass():
    """Return a mock Home Assistant instance."""
    hass_mock = MagicMock(spec=HomeAssistant)
    hass_mock.config_entries = MagicMock()
    hass_mock.config_entries.flow = MagicMock()
    hass_mock.config_entries.flow.async_init = AsyncMock()
    hass_mock.config_entries.flow.async_configure = AsyncMock()
    hass_mock.data = {}
    hass_mock.async_add_executor_job = AsyncMock()
    hass_mock.config = MagicMock()
    hass_mock.config.language = "en"

    # Mock event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    return hass_mock
