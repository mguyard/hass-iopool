"""Module to define the configuration flow for the iopool integration in Home Assistant."""

from __future__ import annotations

from enum import Enum
import logging
from typing import Any

from aiohttp import ClientError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_TEMPERATURE_UNIT,
    CONFIG_MINOR_VERSION,
    CONFIG_VERSION,
    DEFAULT_TEMPERATURE_UNIT,
    DOMAIN,
    POOLS_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class ApiKeyValidationResult(str, Enum):
    """Result of API key validation."""

    SUCCESS = "success"
    INVALID_AUTH = "invalid_auth"
    CANNOT_CONNECT = "cannot_connect"


async def validate_api_key(hass: HomeAssistant, api_key: str) -> ApiKeyValidationResult:
    """Validate the API key by making a request to the API.

    Returns:
        ApiKeyValidationResult: The result of the validation:
            - SUCCESS: The API key is valid
            - INVALID_AUTH: The API key is invalid
            - CANNOT_CONNECT: Unable to connect to the server

    """
    session = async_get_clientsession(hass)
    headers = {"x-api-key": api_key}

    try:
        async with session.get(POOLS_ENDPOINT, headers=headers) as resp:
            if resp.status == 200:
                return ApiKeyValidationResult.SUCCESS
            if resp.status in (401, 403):  # Unauthorized or Forbidden
                _LOGGER.error("API key validation failed with status: %s", resp.status)
                return ApiKeyValidationResult.INVALID_AUTH
            # Other HTTP errors
            _LOGGER.error("Server error with status: %s", resp.status)
            return ApiKeyValidationResult.CANNOT_CONNECT
    except ClientError as error:
        _LOGGER.error("Error connecting to iopool API: %s", error)
        return ApiKeyValidationResult.CANNOT_CONNECT
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected error during API key validation")
        return ApiKeyValidationResult.CANNOT_CONNECT


class IopoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iopool."""

    VERSION = CONFIG_VERSION
    MINOR_VERSION = CONFIG_MINOR_VERSION

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]

            # Validate the API key
            validation_result = await validate_api_key(self.hass, api_key)

            if validation_result == ApiKeyValidationResult.SUCCESS:
                return self.async_create_entry(
                    title="iopool",
                    data=user_input,
                    options={
                        CONF_TEMPERATURE_UNIT: DEFAULT_TEMPERATURE_UNIT,
                    },
                )

            # Set appropriate error
            errors["base"] = validation_result.value

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        _LOGGER.debug("Reconfiguring iopool integration")
        errors: dict[str, str] = {}

        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]

            # Check if API key is unchanged
            if api_key == config_entry.data[CONF_API_KEY]:
                return self.async_abort(reason="no_changes")

            # Validate the new API key
            validation_result = await validate_api_key(self.hass, api_key)

            if validation_result == ApiKeyValidationResult.SUCCESS:
                # Update the existing entry
                return self.async_update_reload_and_abort(
                    config_entry,
                    unique_id=config_entry.unique_id,
                    data={**config_entry.data, CONF_API_KEY: api_key},
                    reason="reconfigure_successful",
                )

            # Set appropriate error
            errors["base"] = validation_result.value

        # Build form with existing API key as default
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY, default=config_entry.data.get(CONF_API_KEY, "")
                ): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )
