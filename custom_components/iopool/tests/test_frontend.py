"""Tests for iopool frontend card registration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.iopool.frontend import (
    CARD_FILENAME,
    _CARD_VERSION,
    URL_BASE,
    IopoolCardRegistration,
    _ha_version_tuple,
)


class TestHaVersionTuple:
    """Test _ha_version_tuple helper."""

    def test_valid_version(self):
        """Test parsing a valid HA version string."""
        assert _ha_version_tuple("2026.2.0") == (2026, 2, 0)

    def test_valid_version_with_extra_parts(self):
        """Test that only the first three parts are used."""
        assert _ha_version_tuple("2025.6.1.dev20250601") == (2025, 6, 1)

    def test_invalid_version_returns_zeros(self):
        """Test that an invalid version returns (0, 0, 0)."""
        assert _ha_version_tuple("not-a-version") == (0, 0, 0)

    def test_empty_string_returns_zeros(self):
        """Test that an empty string returns (0, 0, 0)."""
        assert _ha_version_tuple("") == (0, 0, 0)

    def test_none_returns_zeros(self):
        """Test that None returns (0, 0, 0)."""
        assert _ha_version_tuple(None) == (0, 0, 0)


class TestCardVersionConstant:
    """Test _CARD_VERSION constant."""

    def test_card_version_is_non_empty_string(self):
        """Test that _CARD_VERSION is a non-empty string."""
        assert isinstance(_CARD_VERSION, str)
        assert len(_CARD_VERSION) > 0


class TestGetResourceVersion:
    """Test IopoolCardRegistration._get_resource_version static method."""

    def test_extracts_version_from_url(self):
        """Test version extraction from URL with query param."""
        url = f"{URL_BASE}/{CARD_FILENAME}?v=1.2.3"
        assert IopoolCardRegistration._get_resource_version(url) == "1.2.3"

    def test_returns_empty_string_when_no_version(self):
        """Test that empty string is returned when no version param exists."""
        url = f"{URL_BASE}/{CARD_FILENAME}"
        assert IopoolCardRegistration._get_resource_version(url) == ""

    def test_returns_empty_string_for_none(self):
        """Test that empty string is returned for None input."""
        assert IopoolCardRegistration._get_resource_version(None) == ""


class TestIopoolCardRegistrationProperties:
    """Test IopoolCardRegistration property accessors for different HA versions."""

    def _make_hass_with_lovelace(self, lovelace_data):
        hass = MagicMock()
        hass.data = {"lovelace": lovelace_data}
        return hass

    def test_lovelace_resource_mode_new_api(self):
        """Test resource_mode property for HA >= 2026.2.0."""
        lovelace = MagicMock()
        lovelace.resource_mode = "storage"
        hass = self._make_hass_with_lovelace(lovelace)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            reg = IopoolCardRegistration(hass)
            assert reg.lovelace_resource_mode == "storage"

    def test_lovelace_resource_mode_2025_api(self):
        """Test mode property for HA >= 2025.2.0 and < 2026.2.0."""
        lovelace = MagicMock()
        lovelace.mode = "storage"
        hass = self._make_hass_with_lovelace(lovelace)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2025, 6, 0)):
            reg = IopoolCardRegistration(hass)
            assert reg.lovelace_resource_mode == "storage"

    def test_lovelace_resource_mode_legacy_api(self):
        """Test mode property for HA < 2025.2.0 (dict-based lovelace data)."""
        lovelace = {"mode": "storage", "resources": MagicMock()}
        hass = MagicMock()
        hass.data = {"lovelace": lovelace}

        with patch("custom_components.iopool.frontend._HA_VERSION", (2024, 12, 0)):
            reg = IopoolCardRegistration(hass)
            assert reg.lovelace_resource_mode == "storage"

    def test_lovelace_resources_new_api(self):
        """Test resources property for HA >= 2025.2.0."""
        mock_resources = MagicMock()
        lovelace = MagicMock()
        lovelace.resources = mock_resources
        hass = self._make_hass_with_lovelace(lovelace)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2025, 6, 0)):
            reg = IopoolCardRegistration(hass)
            assert reg.lovelace_resources is mock_resources

    def test_lovelace_resources_legacy_api(self):
        """Test resources property for HA < 2025.2.0."""
        mock_resources = MagicMock()
        lovelace = {"mode": "storage", "resources": mock_resources}
        hass = MagicMock()
        hass.data = {"lovelace": lovelace}

        with patch("custom_components.iopool.frontend._HA_VERSION", (2024, 12, 0)):
            reg = IopoolCardRegistration(hass)
            assert reg.lovelace_resources is mock_resources


class TestIopoolCardRegistration:
    """Test IopoolCardRegistration async methods."""

    def _make_hass(self, mode="storage", resources_loaded=True):
        """Create a mock hass with lovelace storage mode."""
        mock_resources = MagicMock()
        mock_resources.loaded = resources_loaded
        mock_resources.async_get_info = AsyncMock()
        mock_resources.async_items = MagicMock(return_value=[])
        mock_resources.async_create_item = AsyncMock()
        mock_resources.async_update_item = AsyncMock()
        mock_resources.async_delete_item = AsyncMock()

        lovelace = MagicMock()
        lovelace.resource_mode = mode
        lovelace.resources = mock_resources

        hass = MagicMock()
        hass.data = {"lovelace": lovelace}
        hass.http = MagicMock()
        hass.http.async_register_static_paths = AsyncMock()
        return hass, mock_resources

    @pytest.mark.asyncio
    async def test_async_register_path_success(self):
        """Test static path registration succeeds."""
        hass, _ = self._make_hass()
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            await reg._async_register_path()

        hass.http.async_register_static_paths.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_register_path_already_registered(self):
        """Test that RuntimeError on static path registration is silently ignored."""
        hass, _ = self._make_hass()
        hass.http.async_register_static_paths = AsyncMock(side_effect=RuntimeError("already registered"))
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            # Should not raise
            await reg._async_register_path()

    @pytest.mark.asyncio
    async def test_async_register_card_creates_new_resource(self):
        """Test card registration creates a new resource when none exists."""
        hass, mock_resources = self._make_hass()
        mock_resources.async_items.return_value = []
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            with patch("custom_components.iopool.frontend._CARD_VERSION", "1.2.3"):
                await reg._async_register_card()

        mock_resources.async_get_info.assert_called_once()
        mock_resources.async_create_item.assert_called_once_with(
            {"res_type": "module", "url": f"{URL_BASE}/{CARD_FILENAME}?v=1.2.3"}
        )
        mock_resources.async_update_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_register_card_updates_outdated_resource(self):
        """Test card registration updates an existing resource with a different version."""
        hass, mock_resources = self._make_hass()
        existing_url = f"{URL_BASE}/{CARD_FILENAME}?v=1.0.0"
        mock_resources.async_items.return_value = [{"id": "res-id-1", "url": existing_url}]
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            with patch("custom_components.iopool.frontend._CARD_VERSION", "1.2.3"):
                await reg._async_register_card()

        mock_resources.async_get_info.assert_called_once()
        mock_resources.async_update_item.assert_called_once_with(
            "res-id-1",
            {"res_type": "module", "url": f"{URL_BASE}/{CARD_FILENAME}?v=1.2.3"},
        )
        mock_resources.async_create_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_register_card_skips_if_version_unchanged(self):
        """Test card registration is skipped when version is already current."""
        hass, mock_resources = self._make_hass()
        existing_url = f"{URL_BASE}/{CARD_FILENAME}?v=1.2.3"
        mock_resources.async_items.return_value = [{"id": "res-id-1", "url": existing_url}]
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            with patch("custom_components.iopool.frontend._CARD_VERSION", "1.2.3"):
                await reg._async_register_card()

        mock_resources.async_get_info.assert_called_once()
        mock_resources.async_update_item.assert_not_called()
        mock_resources.async_create_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_register_skips_card_in_yaml_mode(self):
        """Test that card resource is NOT registered when lovelace is in yaml mode."""
        hass, mock_resources = self._make_hass(mode="yaml")
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            with patch.object(reg, "_async_register_path", new=AsyncMock()) as mock_path:
                with patch.object(reg, "_async_register_card", new=AsyncMock()) as mock_card:
                    await reg.async_register()
                    mock_path.assert_called_once()
                    mock_card.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_register_full_flow_storage_mode(self):
        """Test full registration flow in storage mode with resources loaded."""
        hass, mock_resources = self._make_hass(mode="storage", resources_loaded=True)
        mock_resources.async_items.return_value = []
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            with patch("custom_components.iopool.frontend._CARD_VERSION", "1.2.3"):
                await reg.async_register()

        hass.http.async_register_static_paths.assert_called_once()
        mock_resources.async_get_info.assert_called_once()
        mock_resources.async_create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_unregister_storage_mode_removes_resources(self):
        """Test that async_unregister removes all matching resources in storage mode."""
        hass, mock_resources = self._make_hass(mode="storage")
        existing_url = f"{URL_BASE}/{CARD_FILENAME}?v=1.2.3"
        mock_resources.async_items.return_value = [{"id": "res-id-1", "url": existing_url}]
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            await reg.async_unregister()

        mock_resources.async_get_info.assert_called_once()
        mock_resources.async_delete_item.assert_called_once_with("res-id-1")

    @pytest.mark.asyncio
    async def test_async_unregister_yaml_mode_does_nothing(self):
        """Test that async_unregister does nothing in yaml mode."""
        hass, mock_resources = self._make_hass(mode="yaml")
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            await reg.async_unregister()

        mock_resources.async_get_info.assert_not_called()
        mock_resources.async_delete_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_unregister_no_matching_resources(self):
        """Test that async_unregister does nothing when no matching resources exist."""
        hass, mock_resources = self._make_hass(mode="storage")
        mock_resources.async_items.return_value = [{"id": "other-id", "url": "/other/card.js"}]
        reg = IopoolCardRegistration(hass)

        with patch("custom_components.iopool.frontend._HA_VERSION", (2026, 2, 0)):
            await reg.async_unregister()

        mock_resources.async_get_info.assert_called_once()
        mock_resources.async_delete_item.assert_not_called()
