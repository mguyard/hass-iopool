"""Tests for iopool API models."""

from __future__ import annotations

from datetime import datetime

from custom_components.iopool.api_models import (
    IopoolAdvice,
    IopoolAPIResponse,
    IopoolAPIResponsePool,
    IopoolLatestMeasure,
)

from .conftest import MOCK_POOLS_API_RESPONSE


class TestIopoolLatestMeasure:
    """Test IopoolLatestMeasure model."""

    def test_from_dict_valid_data(self) -> None:
        """Test creating IopoolLatestMeasure from valid dictionary."""
        data = {
            "temperature": 24.5,
            "ph": 7.2,
            "orp": 650.0,
            "mode": "standard",
            "isValid": True,
            "ecoId": "eco123",
            "measuredAt": "2025-07-22T10:30:00Z",
        }

        measure = IopoolLatestMeasure.from_dict(data)

        assert measure.temperature == 24.5
        assert measure.ph == 7.2
        assert measure.orp == 650.0
        assert measure.mode == "standard"
        assert measure.is_valid is True
        assert measure.eco_id == "eco123"
        assert isinstance(measure.measured_at, datetime)

    def test_from_dict_without_z_timezone(self) -> None:
        """Test creating IopoolLatestMeasure with different timezone format."""
        data = {
            "temperature": 22.0,
            "ph": 7.0,
            "orp": 600.0,
            "mode": "live",
            "isValid": False,
            "ecoId": "eco456",
            "measuredAt": "2025-07-22T08:00:00+00:00",
        }

        measure = IopoolLatestMeasure.from_dict(data)

        assert measure.temperature == 22.0
        assert measure.is_valid is False
        assert isinstance(measure.measured_at, datetime)


class TestIopoolAdvice:
    """Test IopoolAdvice model."""

    def test_from_dict_with_filtration_duration(self) -> None:
        """Test creating IopoolAdvice with filtration duration."""
        data = {"filtrationDuration": 8.5}

        advice = IopoolAdvice.from_dict(data)

        assert advice.filtration_duration == 8.5

    def test_from_dict_without_filtration_duration(self) -> None:
        """Test creating IopoolAdvice without filtration duration."""
        data = {}

        advice = IopoolAdvice.from_dict(data)

        assert advice.filtration_duration is None

    def test_from_dict_none_filtration_duration(self) -> None:
        """Test creating IopoolAdvice with None filtration duration."""
        data = {"filtrationDuration": None}

        advice = IopoolAdvice.from_dict(data)

        assert advice.filtration_duration is None


class TestIopoolAPIResponsePool:
    """Test IopoolAPIResponsePool model."""

    def test_from_dict_complete_data(self) -> None:
        """Test creating IopoolAPIResponsePool from complete data."""
        data = MOCK_POOLS_API_RESPONSE[
            0
        ]  # Get first pool directly since it's now a list

        pool = IopoolAPIResponsePool.from_dict(data)

        assert pool.id == "test_pool_id_67890"
        assert pool.title == "Test Pool"
        assert pool.mode == "STANDARD"
        assert pool.has_action_required is False
        assert pool.latest_measure is not None
        assert pool.advice is not None

    def test_from_dict_without_latest_measure(self) -> None:
        """Test creating IopoolAPIResponsePool without latest measure."""
        data = {
            "id": "pool1",
            "title": "Pool 1",
            "mode": "WINTER",
            "hasAnActionRequired": True,
            "latestMeasure": None,
            "advice": None,
        }

        pool = IopoolAPIResponsePool.from_dict(data)

        assert pool.id == "pool1"
        assert pool.title == "Pool 1"
        assert pool.mode == "WINTER"
        assert pool.has_action_required is True
        assert pool.latest_measure is None
        assert pool.advice is not None  # advice is created even if None in data

    def test_from_dict_missing_advice(self) -> None:
        """Test creating IopoolAPIResponsePool with missing advice field."""
        data = {
            "id": "pool2",
            "title": "Pool 2",
            "mode": "INITIALIZATION",
            "hasAnActionRequired": False,
        }

        pool = IopoolAPIResponsePool.from_dict(data)

        assert pool.id == "pool2"
        assert pool.advice is not None  # Default IopoolAdvice created


class TestIopoolAPIResponse:
    """Test IopoolAPIResponse model."""

    def test_from_dict_with_pools(self) -> None:
        """Test creating IopoolAPIResponse from data with pools."""
        data = MOCK_POOLS_API_RESPONSE  # Pass the pools list directly

        response = IopoolAPIResponse.from_dict(data)

        assert len(response.pools) == 1
        assert response.pools[0].id == "test_pool_id_67890"
        assert response.pools[0].title == "Test Pool"

    def test_from_dict_empty_list(self) -> None:
        """Test creating IopoolAPIResponse from empty list."""
        data = []

        response = IopoolAPIResponse.from_dict(data)

        assert len(response.pools) == 0

    def test_from_dict_multiple_pools(self) -> None:
        """Test creating IopoolAPIResponse from multiple pools."""
        data = [
            {
                "id": "pool1",
                "title": "Pool 1",
                "mode": "STANDARD",
                "hasAnActionRequired": False,
            },
            {
                "id": "pool2",
                "title": "Pool 2",
                "mode": "WINTER",
                "hasAnActionRequired": True,
            },
        ]

        response = IopoolAPIResponse.from_dict(data)

        assert len(response.pools) == 2
        assert response.pools[0].id == "pool1"
        assert response.pools[1].id == "pool2"
