"""Tests for iopool diagnostics."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from custom_components.iopool.api_models import (
    IopoolAdvice,
    IopoolAPIResponse,
    IopoolAPIResponsePool,
    IopoolLatestMeasure,
)
from custom_components.iopool.const import DOMAIN
from custom_components.iopool.diagnostics import async_get_config_entry_diagnostics
import pytest

from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    # Create a simple mock that behaves like a ConfigEntry
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.title = "Test Pool"
    entry.data = {
        CONF_API_KEY: "test_api_key_12345",
        "pool_id": "test_pool_id",
    }
    entry.options = {}
    entry.as_dict.return_value = {
        "entry_id": "test_entry_id",
        "domain": DOMAIN,
        "title": "Test Pool",
        "data": {
            CONF_API_KEY: "test_api_key_12345",
            "pool_id": "test_pool_id",
        },
        "options": {},
        "source": "user",
        "version": 1,
        "minor_version": 1,
        "unique_id": "test_unique_id",
    }
    return entry


@pytest.fixture
def mock_coordinator_with_data() -> MagicMock:
    """Create a mock coordinator with sample data."""
    coordinator = MagicMock()

    # Create sample pool data
    latest_measure = IopoolLatestMeasure(
        temperature=24.5,
        ph=7.2,
        orp=650,
        mode="standard",
        is_valid=True,
        eco_id="test_eco_id",
        measured_at=datetime.fromisoformat("2023-12-01T10:00:00+00:00"),
    )

    advice = IopoolAdvice(filtration_duration=8)

    pool = IopoolAPIResponsePool(
        id="test_pool_123",
        title="Test Pool",
        mode="STANDARD",
        has_action_required=False,
        latest_measure=latest_measure,
        advice=advice,
    )

    api_response = IopoolAPIResponse(pools=[pool])
    coordinator.data = api_response

    return coordinator


@pytest.fixture
def mock_coordinator_no_data() -> MagicMock:
    """Create a mock coordinator without data."""
    coordinator = MagicMock()
    coordinator.data = None
    return coordinator


@pytest.fixture
def mock_coordinator_empty_pools() -> MagicMock:
    """Create a mock coordinator with empty pools."""
    coordinator = MagicMock()
    coordinator.data = IopoolAPIResponse(pools=[])
    return coordinator


class TestIopoolDiagnostics:
    """Test iopool diagnostics functionality."""

    async def test_async_get_config_entry_diagnostics_with_data(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
        mock_coordinator_with_data: MagicMock,
    ) -> None:
        """Test diagnostics with coordinator data."""
        # Setup hass.data structure
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator_with_data}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify structure
        assert "entry" in diagnostics
        assert "data" in diagnostics

        # Verify entry data is redacted
        assert diagnostics["entry"]["data"]["api_key"] == "**REDACTED**"
        assert "pool_id" in diagnostics["entry"]["data"]

        # Verify pool data
        assert diagnostics["data"] is not None
        assert len(diagnostics["data"]) == 1

        pool_data = diagnostics["data"][0]
        assert pool_data["id"] == "test_pool_123"
        assert pool_data["title"] == "Test Pool"
        assert pool_data["mode"] == "STANDARD"
        assert pool_data["has_action_required"] is False

        # Verify latest measure data
        assert "latest_measure" in pool_data
        measure_data = pool_data["latest_measure"]
        assert measure_data["temperature"] == 24.5
        assert measure_data["ph"] == 7.2
        assert measure_data["orp"] == 650
        assert measure_data["mode"] == "standard"
        assert measure_data["is_valid"] is True
        assert "measured_at" in measure_data

        # Verify advice data
        assert "advice" in pool_data
        assert pool_data["advice"]["filtration_duration"] == 8

    async def test_async_get_config_entry_diagnostics_no_data(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
        mock_coordinator_no_data: MagicMock,
    ) -> None:
        """Test diagnostics when coordinator has no data."""
        # Setup hass.data structure
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator_no_data}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify structure
        assert "entry" in diagnostics
        assert "data" in diagnostics
        assert diagnostics["data"] is None

        # Verify entry data is still redacted
        assert diagnostics["entry"]["data"]["api_key"] == "**REDACTED**"

    async def test_async_get_config_entry_diagnostics_empty_pools(
        self,
        hass: HomeAssistant,
        mock_config_entry: MagicMock,
        mock_coordinator_empty_pools: MagicMock,
    ) -> None:
        """Test diagnostics when coordinator has empty pools."""
        # Setup hass.data structure
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator_empty_pools}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify structure
        assert "entry" in diagnostics
        assert "data" in diagnostics
        assert diagnostics["data"] == []

    async def test_async_get_config_entry_diagnostics_no_latest_measure(
        self, hass: HomeAssistant, mock_config_entry: MagicMock
    ) -> None:
        """Test diagnostics when pool has no latest measure."""
        # Create coordinator with pool but no latest measure
        coordinator = MagicMock()
        pool = IopoolAPIResponsePool(
            id="test_pool_456",
            title="Pool Without Measure",
            mode="WINTER",
            has_action_required=True,
            latest_measure=None,
            advice=IopoolAdvice(filtration_duration=6),
        )
        coordinator.data = IopoolAPIResponse(pools=[pool])

        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify pool data
        pool_data = diagnostics["data"][0]
        assert pool_data["id"] == "test_pool_456"
        assert pool_data["title"] == "Pool Without Measure"
        assert pool_data["mode"] == "WINTER"
        assert pool_data["has_action_required"] is True

        # Verify no latest measure data
        assert "latest_measure" not in pool_data

        # Verify advice data is still present
        assert "advice" in pool_data
        assert pool_data["advice"]["filtration_duration"] == 6

    async def test_async_get_config_entry_diagnostics_no_advice(
        self, hass: HomeAssistant, mock_config_entry: MagicMock
    ) -> None:
        """Test diagnostics when pool has no advice."""
        # Create coordinator with pool but no advice
        coordinator = MagicMock()
        latest_measure = IopoolLatestMeasure(
            temperature=22.0,
            ph=7.0,
            orp=700,
            mode="manual",
            is_valid=True,
            eco_id="test_eco_id_2",
            measured_at=datetime.fromisoformat("2023-12-01T11:00:00+00:00"),
        )
        pool = IopoolAPIResponsePool(
            id="test_pool_789",
            title="Pool Without Advice",
            mode="STANDARD",
            has_action_required=False,
            latest_measure=latest_measure,
            advice=None,
        )
        coordinator.data = IopoolAPIResponse(pools=[pool])

        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify pool data
        pool_data = diagnostics["data"][0]
        assert pool_data["id"] == "test_pool_789"

        # Verify latest measure data is present
        assert "latest_measure" in pool_data
        assert pool_data["latest_measure"]["temperature"] == 22.0

        # Verify no advice data
        assert "advice" not in pool_data

    async def test_async_get_config_entry_diagnostics_multiple_pools(
        self, hass: HomeAssistant, mock_config_entry: MagicMock
    ) -> None:
        """Test diagnostics with multiple pools."""
        # Create coordinator with multiple pools
        coordinator = MagicMock()

        pool1 = IopoolAPIResponsePool(
            id="pool_1",
            title="Pool 1",
            mode="STANDARD",
            has_action_required=False,
            latest_measure=IopoolLatestMeasure(
                temperature=25.0,
                ph=7.1,
                orp=600,
                mode="standard",
                is_valid=True,
                eco_id="test_eco_id_3",
                measured_at=datetime.fromisoformat("2023-12-01T10:00:00+00:00"),
            ),
            advice=IopoolAdvice(filtration_duration=10),
        )

        pool2 = IopoolAPIResponsePool(
            id="pool_2",
            title="Pool 2",
            mode="WINTER",
            has_action_required=True,
            latest_measure=None,
            advice=None,
        )

        coordinator.data = IopoolAPIResponse(pools=[pool1, pool2])

        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify multiple pools
        assert len(diagnostics["data"]) == 2

        # Verify first pool
        pool1_data = diagnostics["data"][0]
        assert pool1_data["id"] == "pool_1"
        assert "latest_measure" in pool1_data
        assert "advice" in pool1_data

        # Verify second pool
        pool2_data = diagnostics["data"][1]
        assert pool2_data["id"] == "pool_2"
        assert "latest_measure" not in pool2_data
        assert "advice" not in pool2_data

    async def test_async_get_config_entry_diagnostics_coordinator_no_hasattr(
        self, hass: HomeAssistant, mock_config_entry: MagicMock
    ) -> None:
        """Test diagnostics when coordinator doesn't have data attribute."""
        # Create coordinator without data attribute
        coordinator = MagicMock()
        del coordinator.data  # Remove data attribute

        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify structure
        assert "entry" in diagnostics
        assert "data" in diagnostics
        assert diagnostics["data"] is None

    async def test_async_get_config_entry_diagnostics_api_key_redaction(
        self, hass: HomeAssistant, mock_coordinator_no_data: MagicMock
    ) -> None:
        """Test that API key is properly redacted in diagnostics."""
        # Create config entry with sensitive data
        config_entry = MagicMock()
        config_entry.entry_id = str(uuid4())
        config_entry.domain = DOMAIN
        config_entry.title = "Test Pool"
        config_entry.data = {
            CONF_API_KEY: "super_secret_api_key_12345",
            "pool_id": "visible_pool_id",
            "api_key": "another_secret_key",  # Additional field to redact
        }
        config_entry.options = {}
        config_entry.as_dict.return_value = {
            "entry_id": config_entry.entry_id,
            "domain": DOMAIN,
            "title": "Test Pool",
            "data": config_entry.data,
            "options": {},
            "source": "user",
            "version": 1,
            "minor_version": 1,
            "unique_id": str(uuid4()),
        }

        hass.data[DOMAIN] = {config_entry.entry_id: mock_coordinator_no_data}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)

        # Verify API keys are redacted
        entry_data = diagnostics["entry"]["data"]
        assert "api_key" not in entry_data or entry_data["api_key"] == "**REDACTED**"
        assert (
            entry_data["pool_id"] == "visible_pool_id"
        )  # Non-sensitive data preserved

    async def test_async_get_config_entry_diagnostics_measure_data_completeness(
        self, hass: HomeAssistant, mock_config_entry: MagicMock
    ) -> None:
        """Test diagnostics include all measure data fields."""
        # Create coordinator with comprehensive measure data
        coordinator = MagicMock()
        latest_measure = IopoolLatestMeasure(
            temperature=26.5,
            ph=7.4,
            orp=720,
            mode="live",
            is_valid=False,  # Test with invalid measure
            eco_id="test_eco_id_4",
            measured_at=datetime.fromisoformat("2023-12-01T15:30:00+01:00"),
        )

        pool = IopoolAPIResponsePool(
            id="comprehensive_pool",
            title="Comprehensive Pool",
            mode="STANDARD",
            has_action_required=True,
            latest_measure=latest_measure,
            advice=IopoolAdvice(filtration_duration=12),
        )

        coordinator.data = IopoolAPIResponse(pools=[pool])
        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        # Get diagnostics
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Verify all measure fields are included
        measure_data = diagnostics["data"][0]["latest_measure"]
        assert measure_data["temperature"] == 26.5
        assert measure_data["ph"] == 7.4
        assert measure_data["orp"] == 720
        assert measure_data["mode"] == "live"
        assert measure_data["is_valid"] is False
        assert measure_data["measured_at"] == "2023-12-01 15:30:00+01:00"
