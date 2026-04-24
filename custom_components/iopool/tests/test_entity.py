"""Tests for iopool entity base module, including slugify_pool_name."""

from __future__ import annotations

import pytest

from custom_components.iopool.entity import slugify_pool_name


class TestSlugifyPoolName:
    """Tests for the slugify_pool_name helper function."""

    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            # Standard case — no change in behavior
            ("My Pool", "my_pool"),
            # Numbers are preserved
            ("Pool 123", "pool_123"),
            # Accented char + double space collapses to single underscore
            ("aquarium à  pikatchu", "aquarium_a_pikatchu"),
            # Multiple accented chars
            ("Piscine été", "piscine_ete"),
            # Leading and trailing spaces are stripped
            ("  Leading Spaces  ", "leading_spaces"),
            # Hyphen is replaced by underscore
            ("Pool-Name", "pool_name"),
            # Tilde-combined chars (Ñ → N)
            ("Ma Piscine Ñoño", "ma_piscine_nono"),
        ],
    )
    def test_slugify_pool_name(self, input_name: str, expected: str) -> None:
        """Test slugify_pool_name produces correct output for various inputs."""
        assert slugify_pool_name(input_name) == expected

    def test_already_clean_name(self) -> None:
        """Test that an already-clean lowercase name passes through unchanged."""
        assert slugify_pool_name("mypool") == "mypool"

    def test_all_special_chars_stripped(self) -> None:
        """Test that a name consisting only of special chars returns empty string."""
        # All characters are non-alphanumeric; strip("_") yields ""
        assert slugify_pool_name("---") == ""

    def test_numeric_only(self) -> None:
        """Test that a purely numeric name is preserved."""
        assert slugify_pool_name("42") == "42"
