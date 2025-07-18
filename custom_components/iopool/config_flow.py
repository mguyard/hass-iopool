"""Module to define the configuration flow for the iopool integration in Home Assistant."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from enum import Enum
import logging
from typing import Any

from aiohttp import ClientError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import device_registry as dr, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api_models import IopoolAPIResponse
from .const import (
    CONF_API_KEY,
    CONF_OPTIONS_FILTRATION,
    CONF_OPTIONS_FILTRATION_DURATION,
    CONF_OPTIONS_FILTRATION_DURATION_PERCENT,
    CONF_OPTIONS_FILTRATION_MAX_DURATION,
    CONF_OPTIONS_FILTRATION_MIN_DURATION,
    CONF_OPTIONS_FILTRATION_NAME,
    CONF_OPTIONS_FILTRATION_SLOT1,
    CONF_OPTIONS_FILTRATION_SLOT2,
    CONF_OPTIONS_FILTRATION_START,
    CONF_OPTIONS_FILTRATION_STATUS,
    CONF_OPTIONS_FILTRATION_SUMMER,
    CONF_OPTIONS_FILTRATION_SWITCH_ENTITY,
    CONF_OPTIONS_FILTRATION_WINTER,
    CONF_POOL_ID,
    CONFIG_MINOR_VERSION,
    CONFIG_VERSION,
    DOMAIN,
    POOLS_ENDPOINT,
)
from .models import IopoolConfigEntry, IopoolOptionsData

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


@dataclass
class GetIopoolDataResult:
    """Class to represent the result of fetching Iopool data.

    Attributes:
        result_code (ApiKeyValidationResult): The result code indicating the success or failure of the API key validation.
        result_data (IopoolAPIResponse | None): The data returned from the Iopool API, or None if the request failed.

    """

    result_code: ApiKeyValidationResult = ApiKeyValidationResult.CANNOT_CONNECT
    result_data: IopoolAPIResponse | None = None


async def get_iopool_data(hass: HomeAssistant, api_key: str) -> GetIopoolDataResult:
    """Validate the iopool API key.

    This function attempts to connect to the iopool API using the provided API key
    and retrieves the list of data if successful.

    Args:
        hass: The Home Assistant instance.
        api_key: The iopool API key to validate.

    Returns:
        A ValidationResult object containing:
            - 'result': An ApiKeyValidationResult enum value indicating the validation result:
                - SUCCESS: The API key is valid.
                - INVALID_AUTH: The API key is invalid (401/403 error).
                - CANNOT_CONNECT: Could not connect to the API or received a server error.
            - 'response': An IopoolAPIResponse object containing the API response data if successful,
              or None if the validation failed.

    Raises:
        No exceptions are raised as they are caught and returned as CANNOT_CONNECT results.

    """

    session = async_get_clientsession(hass)
    headers = {"x-api-key": api_key}
    result = GetIopoolDataResult()

    try:
        async with session.get(POOLS_ENDPOINT, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                result.result_code = ApiKeyValidationResult.SUCCESS
                result.result_data = IopoolAPIResponse.from_dict(data)
                return result
            if response.status in (401, 403):  # Unauthorized or Forbidden
                _LOGGER.error(
                    "API key validation failed with status: %s", response.status
                )
                result.result_code = ApiKeyValidationResult.INVALID_AUTH
                return result
            # Other HTTP errors
            _LOGGER.error("Server error with status: %s", response.status)
            result.result_code = ApiKeyValidationResult.CANNOT_CONNECT
            return result
    except ClientError as error:
        _LOGGER.error("Error connecting to iopool API: %s", error)
        result.result_code = ApiKeyValidationResult.CANNOT_CONNECT
        return result
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected error during API key validation")
        result.result_code = ApiKeyValidationResult.CANNOT_CONNECT
        return result


class IopoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iopool."""

    VERSION = CONFIG_VERSION
    MINOR_VERSION = CONFIG_MINOR_VERSION

    def __init__(self):
        """Initialize the config flow."""
        self._api_key = None
        self._iopool_data: IopoolAPIResponse | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: IopoolConfigEntry) -> IopoolOptionsFlow:
        """Create and return an instance of IopoolOptionsFlow for the given config entry."""
        return IopoolOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # api_key = user_input[CONF_API_KEY]
            self._api_key = user_input[CONF_API_KEY]

            # Validate the API key
            data: GetIopoolDataResult = await get_iopool_data(self.hass, self._api_key)
            self._iopool_data = data.result_data

            if data.result_code == ApiKeyValidationResult.SUCCESS:
                if data.result_data and data.result_data.pools:
                    # Proceed to choose a pool
                    return await self.async_step_choose_pool()

                # No pools found, abort the flow
                _LOGGER.warning("No pools found in iopool data")
                return self.async_abort(reason="no_pools_found")

            # Set appropriate error
            errors["base"] = data.result_code.value

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            last_step=False,
        )

    async def async_step_choose_pool(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to choose a pool."""
        errors: dict[str, str] = {}

        if not self._iopool_data or not self._iopool_data.pools:
            _LOGGER.error("No pools found in iopool data")
            return self.async_abort(reason="no_pools")

        if user_input is not None:
            pool_id = user_input.get("pool")
            if pool_id:
                # Create the config entry with the API key and selected pool ID
                return self.async_create_entry(
                    title=next(
                        (p.title for p in self._iopool_data.pools if p.id == pool_id),
                        "iopool",
                    ),
                    data={
                        CONF_API_KEY: self._api_key,
                        CONF_POOL_ID: pool_id,
                    },
                    options=asdict(IopoolOptionsData()),
                )

            errors["base"] = "no_pool_selected"

        # Get the device registry to check existing pools
        dev_reg = dr.async_get(self.hass)
        existing_pool_ids = set()
        # Get existing pool IDs from the device registry
        for device in dev_reg.devices.values():
            for identifier in device.identifiers:
                # Check if the identifier belongs to our integration
                if identifier[0] == DOMAIN:
                    existing_pool_ids.add(identifier[1])

        # Filter out existing pools from the available pools
        available_pools = [
            pool for pool in self._iopool_data.pools if pool.id not in existing_pool_ids
        ]

        if not available_pools:
            return self.async_abort(reason="no_new_pools")

        pool_options = [
            {"value": pool.id, "label": pool.title} for pool in available_pools
        ]

        schema = vol.Schema(
            {
                vol.Required("pool"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=pool_options,
                        mode=selector.SelectSelectorMode.LIST,
                        translation_key="pool",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="choose_pool",
            data_schema=schema,
            errors=errors,
            last_step=True,
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
            result, response = await get_iopool_data(self.hass, api_key)

            if result == ApiKeyValidationResult.SUCCESS:
                # Update the existing entry
                return self.async_update_reload_and_abort(
                    config_entry,
                    unique_id=config_entry.unique_id,
                    data={**config_entry.data, CONF_API_KEY: api_key},
                    reason="reconfigure_successful",
                )

            # Set appropriate error
            errors["base"] = result.value

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


class IopoolOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for iopool."""

    async def async_step_init(self, user_input: None = None) -> ConfigFlowResult:
        """Manage the options."""
        _LOGGER.debug("Initializing IopoolOptionsFlow")
        options = deepcopy(dict(self.config_entry.options))
        _LOGGER.debug("Current options: %s", options)
        errors: dict[str, str] = {}

        # Set slot1 and slot2 for summer filtration
        slot1 = options[CONF_OPTIONS_FILTRATION][CONF_OPTIONS_FILTRATION_SUMMER][
            CONF_OPTIONS_FILTRATION_SLOT1
        ]
        slot2 = options[CONF_OPTIONS_FILTRATION][CONF_OPTIONS_FILTRATION_SUMMER][
            CONF_OPTIONS_FILTRATION_SLOT2
        ]

        if user_input is not None:
            # Validate and process user input
            options_returned = IopoolOptionsData.from_config_flow_data(user_input)
            _LOGGER.debug("User input: %s", options_returned)

            # If min_duration or max_duration is 0, set to None
            # This is to allow the user to set them to None in the UI
            if options_returned.filtration.summer_filtration.min_duration == 0:
                options_returned.filtration.summer_filtration.min_duration = None
            if options_returned.filtration.summer_filtration.max_duration == 0:
                options_returned.filtration.summer_filtration.max_duration = None

            # Check if the options have changed
            if options == IopoolOptionsData.to_dict(options_returned):
                _LOGGER.debug("No configuration changes detected, skipping update.")
                return self.async_abort(reason="no_changes")

            # Summer filtration options validation
            if options_returned.filtration.summer_filtration.status:
                mandatory_fields = [
                    (
                        options_returned.filtration.switch_entity,
                        "switch_entity_missing",
                    ),
                    (
                        options_returned.filtration.summer_filtration.slot1.start,
                        "summer_slot1_start_missing",
                    ),
                    (
                        options_returned.filtration.summer_filtration.slot1.duration_percent,
                        "summer_slot1_duration_percent_missing",
                    ),
                    (
                        options_returned.filtration.summer_filtration.slot2.duration_percent,
                        "summer_slot2_duration_percent_missing",
                    ),
                ]

                # Check if any mandatory fields are missing
                for field_value, error_key in mandatory_fields:
                    if field_value is None:
                        errors["filtration"] = error_key
                        break  # Stop checking after first error

                # Check if min_duration is greater than max_duration
                if (
                    options_returned.filtration.summer_filtration.min_duration
                    is not None
                    and options_returned.filtration.summer_filtration.max_duration
                    is not None
                    and options_returned.filtration.summer_filtration.min_duration
                    > options_returned.filtration.summer_filtration.max_duration
                ):
                    errors["filtration"] = "min_duration_greater_than_max_duration"

                # Check if slot2 duration percent is greater than 0 and slot2 start time is None
                if (
                    options_returned.filtration.summer_filtration.slot2.duration_percent
                    > 0
                    and options_returned.filtration.summer_filtration.slot2.start
                    is None
                ):
                    errors["filtration"] = "slot2_start_missing"

                # Check if slot1 start time is greater than or equal to slot2 start time
                if (
                    options_returned.filtration.summer_filtration.slot1.start
                    is not None
                    and options_returned.filtration.summer_filtration.slot2.start
                    is not None
                    and options_returned.filtration.summer_filtration.slot1.start
                    >= options_returned.filtration.summer_filtration.slot2.start
                ):
                    errors["filtration"] = "slot1_start_greater_than_equal_slot2_start"

                # Check if slot1 duration percent is greater than or equal to slot2 duration percent
                if (
                    options_returned.filtration.summer_filtration.slot1.duration_percent
                    + options_returned.filtration.summer_filtration.slot2.duration_percent
                    > 100
                ):
                    errors["filtration"] = (
                        "slot1_and_slot2_duration_percent_greater_than_100"
                    )

            # Winter filtration options validation
            if options_returned.filtration.winter_filtration.status:
                mandatory_fields = [
                    (
                        options_returned.filtration.switch_entity,
                        "switch_entity_missing",
                    ),
                    (
                        options_returned.filtration.winter_filtration.start,
                        "winter_start_missing",
                    ),
                    (
                        options_returned.filtration.winter_filtration.duration,
                        "winter_duration_missing",
                    ),
                ]

                for field_value, error_key in mandatory_fields:
                    if field_value is None:
                        errors["filtration"] = error_key
                        break

            if not errors:
                # No errors, proceed to update the options
                return self.async_create_entry(
                    title="", data=IopoolOptionsData.to_dict(options_returned)
                )

        # Define the schema for "Filtration" options
        OPTIONS_FILTRATION = vol.Schema(
            {
                # Global Filtration options
                vol.Optional(
                    CONF_OPTIONS_FILTRATION_SWITCH_ENTITY,
                    default=options[CONF_OPTIONS_FILTRATION].get(
                        CONF_OPTIONS_FILTRATION_SWITCH_ENTITY
                    ),
                ): vol.Maybe(
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="switch",
                            multiple=False,
                        )
                    )
                ),
                # Summer Filtration options
                vol.Required(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_STATUS}",
                    default=options[CONF_OPTIONS_FILTRATION][
                        CONF_OPTIONS_FILTRATION_SUMMER
                    ][CONF_OPTIONS_FILTRATION_STATUS],
                ): selector.BooleanSelector(),
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_MIN_DURATION}",
                    default=options[CONF_OPTIONS_FILTRATION][
                        CONF_OPTIONS_FILTRATION_SUMMER
                    ][CONF_OPTIONS_FILTRATION_MIN_DURATION],
                ): vol.Maybe(
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=1439,
                            step=1,
                            mode="slider",
                        )
                    )
                ),
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_MAX_DURATION}",
                    default=options[CONF_OPTIONS_FILTRATION][
                        CONF_OPTIONS_FILTRATION_SUMMER
                    ][CONF_OPTIONS_FILTRATION_MAX_DURATION],
                ): vol.Maybe(
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=1439,
                            step=1,
                            mode="slider",
                        )
                    )
                ),
                # Summer Filtration - Slot 1 options
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_SLOT1}.{CONF_OPTIONS_FILTRATION_NAME}",
                    default=slot1[CONF_OPTIONS_FILTRATION_NAME],
                ): vol.Maybe(vol.All(str, vol.Length(min=1, max=100))),
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_SLOT1}.{CONF_OPTIONS_FILTRATION_START}",
                    default=slot1[CONF_OPTIONS_FILTRATION_START],
                ): vol.Maybe(selector.TimeSelector()),
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_SLOT1}.{CONF_OPTIONS_FILTRATION_DURATION_PERCENT}",
                    default=slot1[CONF_OPTIONS_FILTRATION_DURATION_PERCENT],
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=100,
                        step=1,
                        unit_of_measurement="%",
                        mode="slider",
                    )
                ),
                # Summer Filtration - Slot 2 options
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_SLOT2}.{CONF_OPTIONS_FILTRATION_NAME}",
                    default=slot2[CONF_OPTIONS_FILTRATION_NAME],
                ): vol.Maybe(vol.All(str, vol.Length(min=1, max=100))),
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_SLOT2}.{CONF_OPTIONS_FILTRATION_START}",
                    default=slot2[CONF_OPTIONS_FILTRATION_START],
                ): vol.Maybe(selector.TimeSelector()),
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_SUMMER}.{CONF_OPTIONS_FILTRATION_SLOT2}.{CONF_OPTIONS_FILTRATION_DURATION_PERCENT}",
                    default=slot2[CONF_OPTIONS_FILTRATION_DURATION_PERCENT],
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=100,
                        step=1,
                        unit_of_measurement="%",
                        mode="slider",
                    )
                ),
                # Winter Filtration options
                vol.Required(
                    f"{CONF_OPTIONS_FILTRATION_WINTER}.{CONF_OPTIONS_FILTRATION_STATUS}",
                    default=options[CONF_OPTIONS_FILTRATION][
                        CONF_OPTIONS_FILTRATION_WINTER
                    ][CONF_OPTIONS_FILTRATION_STATUS],
                ): selector.BooleanSelector(),
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_WINTER}.{CONF_OPTIONS_FILTRATION_START}",
                    default=options[CONF_OPTIONS_FILTRATION][
                        CONF_OPTIONS_FILTRATION_WINTER
                    ][CONF_OPTIONS_FILTRATION_START],
                ): vol.Maybe(selector.TimeSelector()),
                vol.Optional(
                    f"{CONF_OPTIONS_FILTRATION_WINTER}.{CONF_OPTIONS_FILTRATION_DURATION}",
                    default=options[CONF_OPTIONS_FILTRATION][
                        CONF_OPTIONS_FILTRATION_WINTER
                    ][CONF_OPTIONS_FILTRATION_DURATION],
                ): vol.Maybe(
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=1439,
                            step=1,
                            mode="slider",
                        )
                    )
                ),
            }
        )

        # Define the schema for the options form
        STEP_OPTIONS = vol.Schema(
            {
                vol.Required("filtration"): section(
                    OPTIONS_FILTRATION,
                    {"collapsed": True},
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_OPTIONS,
            errors=errors or {},
            last_step=True,
        )
