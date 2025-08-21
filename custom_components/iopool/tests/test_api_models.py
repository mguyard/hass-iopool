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


class TestIopoolLatestMeasureEdgeCases:
    """Test IopoolLatestMeasure edge cases and error handling."""

    def test_from_dict_all_mode_types(self) -> None:
        """Test all possible mode values."""
        modes = ["standard", "live", "maintenance", "manual", "backup", "gateway"]

        for mode in modes:
            data = {
                "temperature": 25.0,
                "ph": 7.2,
                "orp": 650.0,
                "mode": mode,
                "isValid": True,
                "ecoId": "eco123",
                "measuredAt": "2025-07-22T10:30:00Z",
            }

            measure = IopoolLatestMeasure.from_dict(data)
            assert measure.mode == mode

    def test_from_dict_with_microseconds(self) -> None:
        """Test creating IopoolLatestMeasure with microseconds in timestamp."""
        data = {
            "temperature": 24.5,
            "ph": 7.2,
            "orp": 650.0,
            "mode": "standard",
            "isValid": True,
            "ecoId": "eco123",
            "measuredAt": "2025-07-22T10:30:00.123456Z",
        }

        measure = IopoolLatestMeasure.from_dict(data)
        assert isinstance(measure.measured_at, datetime)
        assert measure.measured_at.microsecond == 123456

    def test_from_dict_with_different_timezone_formats(self) -> None:
        """Test different timezone formats."""
        # Test various timezone formats
        timezone_formats = [
            "2025-07-22T10:30:00Z",
            "2025-07-22T10:30:00+00:00",
            "2025-07-22T10:30:00-05:00",
            "2025-07-22T10:30:00+02:00",
        ]

        for timestamp in timezone_formats:
            data = {
                "temperature": 24.5,
                "ph": 7.2,
                "orp": 650.0,
                "mode": "standard",
                "isValid": True,
                "ecoId": "eco123",
                "measuredAt": timestamp,
            }

            measure = IopoolLatestMeasure.from_dict(data)
            assert isinstance(measure.measured_at, datetime)

    def test_from_dict_extreme_values(self) -> None:
        """Test with extreme but valid values."""
        data = {
            "temperature": -10.0,  # Very cold water
            "ph": 14.0,  # Maximum pH
            "orp": 1000.0,  # Very high ORP
            "mode": "maintenance",
            "isValid": False,
            "ecoId": "",  # Empty string
            "measuredAt": "2025-07-22T10:30:00Z",
        }

        measure = IopoolLatestMeasure.from_dict(data)
        assert measure.temperature == -10.0
        assert measure.ph == 14.0
        assert measure.orp == 1000.0
        assert measure.is_valid is False
        assert measure.eco_id == ""


class TestIopoolAPIResponsePoolEdgeCases:
    """Test IopoolAPIResponsePool edge cases."""

    def test_from_dict_all_pool_modes(self) -> None:
        """Test all possible pool mode values."""
        modes = ["STANDARD", "OPENING", "ACTIVE_WINTER", "WINTER", "INITIALIZATION"]

        for mode in modes:
            data = {
                "id": f"pool_{mode.lower()}",
                "title": f"Pool {mode}",
                "mode": mode,
                "hasAnActionRequired": False,
            }

            pool = IopoolAPIResponsePool.from_dict(data)
            assert pool.mode == mode
            assert pool.id == f"pool_{mode.lower()}"

    def test_from_dict_with_empty_strings(self) -> None:
        """Test with empty string values."""
        data = {
            "id": "",
            "title": "",
            "mode": "STANDARD",
            "hasAnActionRequired": True,
            "latestMeasure": None,
            "advice": {},
        }

        pool = IopoolAPIResponsePool.from_dict(data)
        assert pool.id == ""
        assert pool.title == ""
        assert pool.has_action_required is True
        assert pool.latest_measure is None
        assert pool.advice is not None

    def test_from_dict_with_complex_latest_measure(self) -> None:
        """Test with complex latest measure data."""
        data = {
            "id": "complex_pool",
            "title": "Complex Pool",
            "mode": "OPENING",
            "hasAnActionRequired": False,
            "latestMeasure": {
                "temperature": 26.7,
                "ph": 7.8,
                "orp": 720.5,
                "mode": "gateway",
                "isValid": True,
                "ecoId": "eco_complex_123",
                "measuredAt": "2025-07-22T15:45:30.987Z",
            },
            "advice": {
                "filtrationDuration": 10.25,
            },
        }

        pool = IopoolAPIResponsePool.from_dict(data)
        assert pool.latest_measure is not None
        assert pool.latest_measure.temperature == 26.7
        assert pool.latest_measure.mode == "gateway"
        assert pool.advice is not None
        assert pool.advice.filtration_duration == 10.25

    def test_from_dict_missing_optional_fields(self) -> None:
        """Test with only required fields present."""
        data = {
            "id": "minimal_pool",
            "title": "Minimal Pool",
            "mode": "WINTER",
            "hasAnActionRequired": True,
        }

        pool = IopoolAPIResponsePool.from_dict(data)
        assert pool.id == "minimal_pool"
        assert pool.title == "Minimal Pool"
        assert pool.mode == "WINTER"
        assert pool.has_action_required is True
        assert pool.latest_measure is None
        assert pool.advice is not None  # Default advice created

    def test_from_dict_advice_with_none_value(self) -> None:
        """Test when advice field is explicitly None."""
        data = {
            "id": "pool_none_advice",
            "title": "Pool with None Advice",
            "mode": "STANDARD",
            "hasAnActionRequired": False,
            "advice": None,
        }

        pool = IopoolAPIResponsePool.from_dict(data)
        assert pool.advice is not None  # Should create default IopoolAdvice


class TestIopoolAdviceEdgeCases:
    """Test IopoolAdvice edge cases."""

    def test_from_dict_with_zero_duration(self) -> None:
        """Test with zero filtration duration."""
        data = {"filtrationDuration": 0.0}

        advice = IopoolAdvice.from_dict(data)
        assert advice.filtration_duration == 0.0

    def test_from_dict_with_negative_duration(self) -> None:
        """Test with negative filtration duration."""
        data = {"filtrationDuration": -1.5}

        advice = IopoolAdvice.from_dict(data)
        assert advice.filtration_duration == -1.5

    def test_from_dict_with_very_large_duration(self) -> None:
        """Test with very large filtration duration."""
        data = {"filtrationDuration": 999.99}

        advice = IopoolAdvice.from_dict(data)
        assert advice.filtration_duration == 999.99

    def test_from_dict_with_extra_fields(self) -> None:
        """Test that extra fields are ignored."""
        data = {
            "filtrationDuration": 5.5,
            "extraField": "ignored",
            "anotherField": 123,
        }

        advice = IopoolAdvice.from_dict(data)
        assert advice.filtration_duration == 5.5
        # Extra fields should be ignored, not cause errors


class TestIopoolAPIResponseEdgeCases:
    """Test IopoolAPIResponse edge cases."""

    def test_from_dict_with_mixed_pool_data(self) -> None:
        """Test with mixed complete and incomplete pool data."""
        data = [
            {
                "id": "complete_pool",
                "title": "Complete Pool",
                "mode": "STANDARD",
                "hasAnActionRequired": False,
                "latestMeasure": {
                    "temperature": 25.0,
                    "ph": 7.2,
                    "orp": 650.0,
                    "mode": "standard",
                    "isValid": True,
                    "ecoId": "eco123",
                    "measuredAt": "2025-07-22T10:30:00Z",
                },
                "advice": {"filtrationDuration": 8.0},
            },
            {
                "id": "minimal_pool",
                "title": "Minimal Pool",
                "mode": "WINTER",
                "hasAnActionRequired": True,
            },
        ]

        response = IopoolAPIResponse.from_dict(data)
        assert len(response.pools) == 2

        # Check complete pool
        complete_pool = response.pools[0]
        assert complete_pool.latest_measure is not None
        assert complete_pool.advice.filtration_duration == 8.0

        # Check minimal pool
        minimal_pool = response.pools[1]
        assert minimal_pool.latest_measure is None
        assert minimal_pool.advice.filtration_duration is None

    def test_from_dict_single_pool_as_list(self) -> None:
        """Test with single pool in list."""
        data = [
            {
                "id": "single_pool",
                "title": "Single Pool",
                "mode": "OPENING",
                "hasAnActionRequired": False,
            }
        ]

        response = IopoolAPIResponse.from_dict(data)
        assert len(response.pools) == 1
        assert response.pools[0].id == "single_pool"

    def test_from_dict_large_pool_list(self) -> None:
        """Test with many pools."""
        data = [
            {
                "id": f"pool_{i}",
                "title": f"Pool {i}",
                "mode": "STANDARD",
                "hasAnActionRequired": i % 2 == 0,  # Alternating True/False
            }
            for i in range(10)
        ]

        response = IopoolAPIResponse.from_dict(data)
        assert len(response.pools) == 10

        for i, pool in enumerate(response.pools):
            assert pool.id == f"pool_{i}"
            assert pool.title == f"Pool {i}"
            assert pool.has_action_required == (i % 2 == 0)


class TestDataclassDefaults:
    """Test dataclass default values and initialization."""

    def test_iopool_advice_defaults(self) -> None:
        """Test IopoolAdvice default initialization."""
        advice = IopoolAdvice()
        assert advice.filtration_duration is None

    def test_iopool_advice_with_value(self) -> None:
        """Test IopoolAdvice with explicit value."""
        advice = IopoolAdvice(filtration_duration=7.5)
        assert advice.filtration_duration == 7.5

    def test_iopool_api_response_defaults(self) -> None:
        """Test IopoolAPIResponse default initialization."""
        response = IopoolAPIResponse()
        assert response.pools == []
        assert len(response.pools) == 0

    def test_iopool_api_response_with_pools(self) -> None:
        """Test IopoolAPIResponse with explicit pools."""
        pool_data = {
            "id": "test_pool",
            "title": "Test Pool",
            "mode": "STANDARD",
            "has_action_required": False,
        }
        pool = IopoolAPIResponsePool(**pool_data)

        response = IopoolAPIResponse(pools=[pool])
        assert len(response.pools) == 1
        assert response.pools[0].id == "test_pool"
