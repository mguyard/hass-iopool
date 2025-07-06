"""Filtration logic for integration."""

from datetime import datetime, time, timedelta
import logging
import re

from homeassistant.core import State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    CONF_OPTIONS_FILTRATION,
    CONF_OPTIONS_FILTRATION_DURATION,
    CONF_OPTIONS_FILTRATION_DURATION_PERCENT,
    CONF_OPTIONS_FILTRATION_MAX_DURATION,
    CONF_OPTIONS_FILTRATION_MIN_DURATION,
    CONF_OPTIONS_FILTRATION_SLOT1,
    CONF_OPTIONS_FILTRATION_SLOT2,
    CONF_OPTIONS_FILTRATION_START,
    CONF_OPTIONS_FILTRATION_STATUS,
    CONF_OPTIONS_FILTRATION_SUMMER,
    CONF_OPTIONS_FILTRATION_SWITCH_ENTITY,
    CONF_OPTIONS_FILTRATION_WINTER,
    CONF_POOL_ID,
    DOMAIN,
    EVENT_TYPE_SLOT1_END,
    EVENT_TYPE_SLOT1_START,
    EVENT_TYPE_SLOT2_END,
    EVENT_TYPE_SLOT2_START,
    EVENT_TYPE_WINTER_END,
    EVENT_TYPE_WINTER_START,
    SENSOR_BOOST_SELECTOR,
    SENSOR_ELAPSED_FILTRATION,
    SENSOR_FILTRATION,
    SENSOR_FILTRATION_RECOMMENDATION,
    SENSOR_POOL_MODE,
)
from .models import IopoolConfigData, IopoolConfigEntry

_LOGGER = logging.getLogger(__name__)


class Filtration:
    """Class to handle filtration functionality."""

    def __init__(self, entry: IopoolConfigEntry) -> None:
        """Initialize the Filtration handler.

        This constructor sets up the filtration handler with the necessary references
        to the Home Assistant instance and iopool configuration.

        Args:
            entry: The iopool config entry containing runtime data and configuration.

        Returns:
            None

        """

        self._entry = entry
        self._config: IopoolConfigData = entry.runtime_data.config
        self._coordinator = entry.runtime_data.coordinator
        # _LOGGER.debug("Filtration configuration: %s", self._config)
        self._config_options: dict = self._config.options.__dict__
        # _LOGGER.debug("Filtration options: %s", self._config_options)
        self.configuration_filtration_enabled_summer = (
            self.config_filtration_summer_enabled()
        )
        self.configuration_filtration_enabled_winter = (
            self.config_filtration_winter_enabled()
        )
        self.configuration_filtration_enabled = self.config_filtration_enabled()

    def config_filtration_summer_enabled(self) -> bool:
        """Determine if summer filtration is enabled in the configuration.

        This method checks the configuration options to see if summer filtration mode
        is enabled. It navigates through nested configuration dictionaries to find
        the summer filtration status.

        Returns:
            bool: True if summer filtration is enabled in the configuration, False otherwise.

        """

        filtration = self._config_options.get(CONF_OPTIONS_FILTRATION, None)
        summer_filtration = filtration.get(CONF_OPTIONS_FILTRATION_SUMMER, None)
        summer_filtration_status = summer_filtration.get(
            CONF_OPTIONS_FILTRATION_STATUS, False
        )
        _LOGGER.debug(
            "Is summer filtration enabled in configuration? %s",
            summer_filtration_status,
        )

        return bool(summer_filtration_status)

    def config_filtration_winter_enabled(self) -> bool:
        """Determine if winter filtration is enabled in the configuration.

        This method checks the configuration options to see if winter filtration mode
        is enabled. It navigates through nested configuration dictionaries to find
        the winter filtration status.

        Returns:
            bool: True if winter filtration is enabled in the configuration, False otherwise.

        """

        filtration = self._config_options.get(CONF_OPTIONS_FILTRATION, None)
        winter_filtration = filtration.get(CONF_OPTIONS_FILTRATION_WINTER, None)
        winter_filtration_status = winter_filtration.get(
            CONF_OPTIONS_FILTRATION_STATUS, False
        )
        _LOGGER.debug(
            "Is winter filtration enabled in configuration? %s",
            winter_filtration_status,
        )

        return bool(winter_filtration_status)

    def config_filtration_enabled(self) -> bool:
        """Check if filtration is enabled in either summer or winter mode.

        Returns:
            bool: True if filtration is enabled in either summer or winter configuration, False otherwise.

        """

        return (
            self.configuration_filtration_enabled_summer
            or self.configuration_filtration_enabled_winter
        )

    def _get_switch_state(self, switch_entity: str) -> str | None:
        """Get the current state of the switch entity.

        Returns:
            The state as a string ("on", "off", etc.) or None if unavailable

        """

        state = self._entry.runtime_data.coordinator.hass.states.get(switch_entity)
        return state.state if state else None

    async def async_start_filtration(self) -> None:
        """Start the filtration system if it's enabled in the configuration.

        This method checks if filtration is enabled in the configuration and if a switch entity
        is properly configured. If conditions are met and the pump is not already running,
        it will turn on the filtration pump.

        Returns:
            None

        Raises:
            No explicit exceptions are raised, but logs warnings if:
            - Filtration is not enabled in configuration
            - No filtration switch entity is configured

        """

        # First check if filtration is enabled in configuration
        if not self.configuration_filtration_enabled:
            _LOGGER.warning(
                "Filtration is not enabled in configuration, skipping start"
            )
            return

        switch_entity = self.get_switch_entity()
        if not switch_entity:
            _LOGGER.warning(
                "No filtration switch entity configured, cannot start filtration"
            )
            return

        # Check if the pump is already on
        current_state = self._get_switch_state(switch_entity)

        if current_state != "on":
            _LOGGER.debug("Starting filtration pump using entity %s", switch_entity)
            await self._entry.runtime_data.coordinator.hass.services.async_call(
                "switch", "turn_on", {"entity_id": switch_entity}, blocking=True
            )
        else:
            _LOGGER.debug("Filtration pump is already on, skipping start command")

    async def async_stop_filtration(self) -> None:
        """Stop the filtration system if it is enabled and configured.

        This method will:
        1. Check if filtration is enabled in configuration
        2. Verify that a switch entity is configured for controlling the filtration pump
        3. Check the current state of the switch
        4. Turn off the switch if it's not already off

        Returns:
            None

        Raises:
            No exceptions are explicitly raised, but logs warnings for:
            - Filtration not enabled in configuration
            - No filtration switch entity configured

        """

        # First check if filtration is enabled in configuration
        if not self.configuration_filtration_enabled:
            _LOGGER.warning("Filtration is not enabled in configuration, skipping stop")
            return

        switch_entity = self.get_switch_entity()
        if not switch_entity:
            _LOGGER.warning(
                "No filtration switch entity configured, cannot stop filtration"
            )
            return

        # Check if the pump is already off
        current_state = self._get_switch_state(switch_entity)

        if current_state != "off":
            _LOGGER.debug("Stopping filtration pump using entity %s", switch_entity)
            await self._entry.runtime_data.coordinator.hass.services.async_call(
                "switch", "turn_off", {"entity_id": switch_entity}, blocking=True
            )
        else:
            _LOGGER.debug("Filtration pump is already off, skipping stop command")

    def get_switch_entity(self) -> str | None:
        """Retrieve the configured switch entity for filtration control.

        Returns:
            str | None: The entity ID of the switch entity configured for filtration control,
                        or None if filtration is not enabled in the configuration.

        """

        if not self.configuration_filtration_enabled:
            return None

        return self._config.options.filtration.get(
            CONF_OPTIONS_FILTRATION_SWITCH_ENTITY
        )

    def search_entity(self, platform: str, name_pattern: str) -> str | None:
        """Search for an entity by platform and name pattern.

        Args:
            platform: The entity platform (sensor, binary_sensor, etc.)
            name_pattern: Regex pattern to match the entity name after the platform prefix

        Returns:
            The full entity_id if found, None otherwise

        """

        entry_id = self._entry.entry_id
        hass = self._entry.runtime_data.coordinator.hass

        # Get entity registry using proper method
        entity_registry = er.async_get(hass)

        # Compile the regex pattern
        pattern = re.compile(name_pattern)

        # Get all entities for the config entry
        entities = async_entries_for_config_entry(entity_registry, entry_id)

        # Filter by platform and pattern
        for entity in entities:
            if entity.domain == platform and pattern.search(
                entity.entity_id.split(".", 1)[1]
            ):
                return entity.entity_id

        _LOGGER.debug(
            "No matching %s entity found for pattern %s", platform, name_pattern
        )
        return None

    def get_summer_filtration_slot_start(self, slot: int) -> datetime | None:
        """Return today's date at the summer filtration slot start time.

        Args:
            slot (int): The slot number (1 or 2) to retrieve the start time for.

        Returns:
            datetime | None: Today's date at the slot start time, or None if not configured or invalid.

        """

        filtration = self._config_options.get(CONF_OPTIONS_FILTRATION, {})
        summer_filtration = (
            filtration.get(CONF_OPTIONS_FILTRATION_SUMMER, {}) if filtration else {}
        )
        slot_key = f"slot{slot}"
        slot_start = summer_filtration.get(slot_key, {}).get(
            CONF_OPTIONS_FILTRATION_START
        )

        if not slot_start:
            _LOGGER.warning("No start time configured for summer slot %d", slot)
            return None

        try:
            slot_time = datetime.strptime(slot_start, "%H:%M:%S").time()
            today = datetime.now().date()
            return datetime.combine(today, slot_time)
        except ValueError as e:
            _LOGGER.error("Invalid time format for summer slot %d: %s", slot, e)
            return None

    def get_summer_filtration_duration(self) -> int | None:
        """Get the recommended summer filtration duration with constraints applied.

        This method retrieves the filtration duration recommendation from the appropriate sensor,
        then applies any configured minimum and maximum duration constraints.

        Returns:
            int | None: The adjusted filtration duration in minutes that respects the min/max constraints,
                        or None if the recommendation could not be retrieved or is invalid.

        Raises:
            ValueError: If the recommendation state is not a valid number
            TypeError: If the recommendation state cannot be converted to an integer

        """

        # Get the recommendation entity state using dynamic search
        recommendation_entity = self.search_entity(
            "sensor", f"iopool_.*_{SENSOR_FILTRATION_RECOMMENDATION}$"
        )
        if not recommendation_entity:
            _LOGGER.warning("No filtration recommendation entity found")
            return None

        recommendation_state = self._entry.runtime_data.coordinator.hass.states.get(
            recommendation_entity
        )
        if not recommendation_state:
            _LOGGER.warning("Filtration recommendation entity not found")
            return None

        try:
            # Convert the state to a number
            recommended_duration = int(float(recommendation_state.state))
        except (ValueError, TypeError):
            _LOGGER.warning("Filtration recommendation is not a valid number")
            return None

        # Get min and max durations from summer configuration
        filtration = self._config_options.get(CONF_OPTIONS_FILTRATION, {})
        summer_filtration = (
            filtration.get(CONF_OPTIONS_FILTRATION_SUMMER, {}) if filtration else {}
        )

        min_duration = summer_filtration.get(CONF_OPTIONS_FILTRATION_MIN_DURATION)
        max_duration = summer_filtration.get(CONF_OPTIONS_FILTRATION_MAX_DURATION)

        original_duration = recommended_duration

        # Apply constraints with min/max functions
        if min_duration is not None:
            recommended_duration = max(recommended_duration, min_duration)

        if max_duration is not None:
            recommended_duration = min(recommended_duration, max_duration)

        if recommended_duration != original_duration:
            _LOGGER.debug(
                "Adjusted summer filtration duration from iopool/%s to calculated/%s minutes (Min: %s, Max: %s)",
                original_duration,
                recommended_duration,
                min_duration,
                max_duration,
            )

        return recommended_duration

    def get_filtration_pool_mode(self) -> str | None:
        """Retrieve the current pool mode entity.

        The pool mode is identified by finding the appropriate sensor entity
        that matches the pattern 'iopool_.*_mode$' and extracting its state.

        Returns:
            str | None: The pool mode as a string if found, or None if:
                - No matching pool mode entity is found
                - The entity state could not be retrieved
                - The state value could not be converted to a valid string

        """

        pool_mode_entity = self.search_entity(
            "select", f"iopool_.*_{SENSOR_POOL_MODE}$"
        )
        if not pool_mode_entity:
            _LOGGER.warning("No filtration pool mode entity found")
            return None

        pool_mode_state = self._entry.runtime_data.coordinator.hass.states.get(
            pool_mode_entity
        )
        if not pool_mode_state:
            _LOGGER.warning("Filtration pool mode entity not found")
            return None

        try:
            # Convert the state to a string
            pool_mode = str(pool_mode_state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Filtration pool mode is not a valid string")
            return None

        return pool_mode

    def get_winter_filtration_start_end(self) -> tuple[datetime.time, timedelta] | None:
        """Get winter filtration start time and duration.

        Retrieves the configured winter filtration start time and duration from the component's
        configuration. If winter filtration is not configured, returns None.

        Returns:
            tuple[datetime.time, timedelta] | None: A tuple containing the start time as datetime.time
                and duration as timedelta if winter filtration is configured, None otherwise.

        """

        winter_filtration = self._config.options.filtration.get(
            CONF_OPTIONS_FILTRATION_WINTER
        )
        if not winter_filtration:
            return None

        start_time = datetime.strptime(
            winter_filtration.get(CONF_OPTIONS_FILTRATION_START),
            "%H:%M:%S",
        ).time()
        duration = int(winter_filtration.get(CONF_OPTIONS_FILTRATION_DURATION))

        if not start_time or not duration:
            return None

        return start_time, timedelta(minutes=duration)

    async def get_filtration_attributes(
        self,
    ) -> tuple[str, State, dict[str, str | int | None]]:
        """Retrieve the entity_id, state, and attributes of the iopool filtration binary sensor.

        This method searches for the filtration binary sensor entity by pattern matching,
        fetches its current state from Home Assistant, and returns the entity ID,
        state object, and a dictionary of attributes.

        Returns:
            tuple[str, State, dict[str, str | int | None]]:
                - The entity_id of the filtration binary sensor
                - The State object representing the current state
                - A dictionary containing all attributes of the state
            Returns an empty dict if the binary sensor is not found or its state cannot be retrieved.

        """

        entity_id = self.search_entity(
            "binary_sensor", f"iopool_.*_{SENSOR_FILTRATION}$"
        )
        if not entity_id:
            _LOGGER.warning("Filtration binary sensor not found")
            return {}

        state = self._entry.runtime_data.coordinator.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning("Filtration binary sensor state not found")
            return {}

        return entity_id, state, dict(state.attributes)

    async def update_filtration_attributes(
        self,
        next_stop_time: str | None = None,
        active_slot: int | str | None = None,
        slot1_end_time: str | None = None,
        slot2_end_time: str | None = None,
    ) -> None:
        """Update the attributes of the filtration binary sensor.

        Args:
            next_stop_time: ISO formatted datetime string for the next stop time
            active_slot: Current active slot (1, 2, "winter", or None)
            slot1_end_time: ISO formatted datetime string for slot 1 end time
            slot2_end_time: ISO formatted datetime string for slot 2 end time

        Returns:
            None

        """

        entity_id, state, attributes = await self.get_filtration_attributes()

        # Update attributes if values provided
        if slot1_end_time is not None:
            attributes["slot1_end_time"] = slot1_end_time
        if slot2_end_time is not None:
            attributes["slot2_end_time"] = slot2_end_time
        if next_stop_time is not None:
            attributes["next_stop_time"] = next_stop_time
        if active_slot is not None:
            attributes["active_slot"] = active_slot

        # If next_stop_time is None, remove it from attributes
        if next_stop_time is None and "next_stop_time" in attributes:
            attributes.pop("next_stop_time")
        if active_slot is None and "active_slot" in attributes:
            attributes.pop("active_slot")

        # Update the state
        self._entry.runtime_data.coordinator.hass.states.async_set(
            entity_id, state.state, attributes
        )
        _LOGGER.debug("Updated filtration attributes: %s", attributes)

    async def check_filtration_status(self, now: datetime) -> None:
        """Periodically checks and manages the filtration system status.

        This method performs the following actions:
        - Logs the current check time.
        - Checks if the filtration switch is on; exits early if not.
        - Checks if the boost mode is active; if so, updates attributes and exits early.
        - Retrieves the next scheduled stop time for filtration.
        - If the stop time is reached or passed:
            - For slot 2, checks if the elapsed filtration duration is sufficient; if not, adjusts the stop time.
            - Otherwise, stops the filtration process.
            - Fires an appropriate event (slot1, slot2, or winter end) with relevant data.
            - Clears the next stop time and active slot attributes.
        - Handles and logs parsing and runtime errors.

        Args:
            now (datetime): The current datetime, typically provided by the scheduler.

        Returns:
            None

        """

        _LOGGER.debug("Periodic check running at %s", now)

        hass = self._entry.runtime_data.coordinator.hass

        try:
            # Check if filtration switch is on
            # If not active, leave the method early
            switch_entity_id = self.get_switch_entity()
            switch_state = (
                hass.states.get(switch_entity_id) if switch_entity_id else None
            )
            _LOGGER.debug(
                "Checking filtration status - Entity ID: %s, State: %s",
                switch_entity_id,
                switch_state,
            )

            if not switch_state or switch_state.state != "on":
                _LOGGER.debug(
                    "Filtration not running (switch state: %s), skipping scheduled stop check",
                    switch_state.state,
                )
                return

            # Check if boost is active
            # If boost is active, leave the method early
            boost_selector_entity = self.search_entity(
                "select", f"iopool_.*{SENSOR_BOOST_SELECTOR}$"
            )
            boost_state = (
                hass.states.get(boost_selector_entity)
                if boost_selector_entity
                else None
            )
            _LOGGER.debug(
                "Checking boost state for Entity: %s, State: %s",
                boost_selector_entity,
                boost_state,
            )

            _, _, filtration_attributes = await self.get_filtration_attributes()

            # if boost_state and boost_state.state not in (None, "none", "None"):
            #     _LOGGER.debug(
            #         "Boost is active (%s), skipping scheduled filtration stop",
            #         boost_state.state,
            #     )
            #     if filtration_attributes.get("active_slot") != "boost":
            #         await self.update_filtration_attributes(
            #             next_stop_time=None, active_slot="boost"
            #         )
            #     return

            # Retrieve the next scheduled stop time from binary sensor attributes
            next_stop_time = filtration_attributes.get("next_stop_time")
            _LOGGER.debug("Next stop time for filtration: %s", next_stop_time)
            if not next_stop_time:
                _LOGGER.debug("No next stop time set, skipping filtration stop check")
                return

            try:
                # Parse the next_stop_time which is in local timezone
                next_stop_dt = dt_util.parse_datetime(next_stop_time)
                if not next_stop_dt:
                    _LOGGER.warning(
                        "Could not parse next_stop_time: %s", next_stop_time
                    )
                    return

                # Convert now to local time for proper comparison
                now_local = dt_util.as_local(now)

                _LOGGER.debug(
                    "Parsed next stop time: %s, current time (local): %s",
                    next_stop_dt,
                    now_local,
                )

                # Retrieve the elapsed filtration duration sensor state
                elapsed_filtration_duration_entity = self.search_entity(
                    "sensor", f"iopool_.*_{SENSOR_ELAPSED_FILTRATION}$"
                )
                elapsed_filtration_duration_state: State = (
                    hass.states.get(elapsed_filtration_duration_entity)
                    if elapsed_filtration_duration_entity
                    else None
                )
                _LOGGER.debug(
                    "Elapsed filtration duration state: %s",
                    elapsed_filtration_duration_state,
                )

                if next_stop_dt and now_local >= next_stop_dt:
                    # Check if active_slot is 2 and if elapsed filtration is enough
                    if filtration_attributes.get("active_slot", None) == 2:
                        if elapsed_filtration_duration_state:
                            remaining_duration_min = round(
                                int(
                                    filtration_attributes.get(
                                        "filtration_duration_minutes", 0
                                    )
                                )
                                - (float(elapsed_filtration_duration_state.state) * 60)
                            )
                            _LOGGER.info(
                                "Remaining duration for slot #2 is %s minutes",
                                remaining_duration_min,
                            )
                            if remaining_duration_min > 0:
                                # Calculate new stop time based on remaining duration
                                new_stop_time = now_local + timedelta(
                                    minutes=remaining_duration_min
                                )
                                # Round to the nearest minute
                                new_stop_time = new_stop_time.replace(
                                    second=0, microsecond=0
                                )
                                # Convert to ISO format for consistency
                                new_stop_time_iso = new_stop_time.isoformat()
                                _LOGGER.info(
                                    "Ajusting next stop time based on remaining duration: %s minutes, new stop time: %s (was %s)",
                                    int(remaining_duration_min),
                                    new_stop_time_iso,
                                    next_stop_dt,
                                )

                                await self.update_filtration_attributes(
                                    slot2_end_time=new_stop_time_iso,
                                    next_stop_time=new_stop_time_iso,
                                    active_slot=2,
                                )
                                return

                    _LOGGER.info(
                        "Stopping filtration based on scheduled end time: %s",
                        next_stop_time,
                    )

                    if boost_state and boost_state.state not in (None, "none", "None"):
                        _LOGGER.info(
                            "Boost is active, skipping scheduled filtration stop"
                        )
                    else:
                        await self.async_stop_filtration()

                    # Prepare common event data
                    day_filtration_objective_minutes = (
                        self.get_summer_filtration_duration()
                    )
                    day_filtration_elapsed_minutes = (
                        float(elapsed_filtration_duration_state.state) * 60
                        if elapsed_filtration_duration_state
                        else 0
                    )
                    day_filtration_elapsed_percent = round(
                        (
                            day_filtration_elapsed_minutes
                            / day_filtration_objective_minutes
                        )
                        * 100
                    )
                    boost_end_time = (
                        dt_util.parse_datetime(
                            boost_state.attributes.get(
                                "boost_end_time", now.isoformat()
                            )
                        )
                        if boost_state
                        and boost_state.state not in (None, "none", "None")
                        else None
                    )
                    boost_remaining_duration = (
                        int((boost_end_time - now).total_seconds() / 60)
                        if boost_end_time and boost_end_time > now
                        else 0
                    )

                    # Prepare event data based on active slot
                    event_type = None
                    event = None
                    match filtration_attributes.get("active_slot"):
                        case 1:
                            event_type = EVENT_TYPE_SLOT1_END
                            event = {
                                "start_time": dt_util.parse_datetime(
                                    filtration_attributes.get("slot1_start_time", None)
                                ),
                                "end_time": now.isoformat(),
                                "duration_minutes": int(
                                    (
                                        now
                                        - dt_util.parse_datetime(
                                            filtration_attributes.get(
                                                "slot1_start_time", None
                                            )
                                        )
                                    ).total_seconds()
                                    / 60
                                ),
                                "boost_in_progress": boost_state.state,
                                "remaining_boost_duration_minutes": boost_remaining_duration,
                                "day_filtration_objective_minutes": day_filtration_objective_minutes,
                                "day_filtration_elapsed_minutes": day_filtration_elapsed_minutes,
                                "day_filtration_elapsed_percent": day_filtration_elapsed_percent,
                            }
                        case 2:
                            event_type = EVENT_TYPE_SLOT2_END
                            event = {
                                "start_time": dt_util.parse_datetime(
                                    filtration_attributes.get("slot2_start_time", None)
                                ),
                                "end_time": now.isoformat(),
                                "duration_minutes": int(
                                    (
                                        now
                                        - dt_util.parse_datetime(
                                            filtration_attributes.get(
                                                "slot2_start_time", None
                                            )
                                        )
                                    ).total_seconds()
                                    / 60
                                ),
                                "boost_in_progress": boost_state.state,
                                "remaining_boost_duration_minutes": boost_remaining_duration,
                                "day_filtration_objective_minutes": day_filtration_objective_minutes,
                                "day_filtration_elapsed_minutes": day_filtration_elapsed_minutes,
                                "day_filtration_elapsed_percent": day_filtration_elapsed_percent,
                            }
                        case "winter":
                            event_type = EVENT_TYPE_WINTER_END
                            event = {
                                "start_time": dt_util.parse_datetime(
                                    filtration_attributes.get("winter_start_time", None)
                                ),
                                "end_time": now.isoformat(),
                                "duration_minutes": int(
                                    (
                                        now
                                        - dt_util.parse_datetime(
                                            filtration_attributes.get(
                                                "winter_start_time", None
                                            )
                                        )
                                    ).total_seconds()
                                    / 60
                                ),
                                "boost_in_progress": boost_state.state,
                                "remaining_boost_duration_minutes": boost_remaining_duration,
                                "day_filtration_objective_minutes": day_filtration_objective_minutes,
                                "day_filtration_elapsed_minutes": day_filtration_elapsed_minutes,
                                "day_filtration_elapsed_percent": day_filtration_elapsed_percent,
                            }

                    # Fire the event if event_type and event are set
                    if event_type and event:
                        await self.publish_event(
                            event_type,
                            event,
                        )

                    # Clear next_stop_time and active_slot attributes
                    await self.update_filtration_attributes(
                        next_stop_time=None, active_slot=None
                    )
            except (ValueError, TypeError) as err:
                _LOGGER.error("Error parsing next_stop_time: %s", err)
        except Exception:
            # Catch any exception that might occur
            _LOGGER.exception("Error in periodic check")

    async def on_summer_filtration_slot1_trigger(self, now: datetime) -> None:
        """Handle the summer filtration slot 1 trigger event.

        This method is triggered daily at the configured start time for summer filtration slot 1.
        It calculates the filtration duration based on the configured percentage of the total
        required filtration time, starts the filtration process, and sets the scheduled end time
        in binary_sensor attributes.

        Args:
            now (datetime): The current datetime when the trigger is executed.

        Returns:
            None: This method doesn't return anything but may exit early if filtration duration can't be determined.

        Note:
            The filtration duration is calculated as a percentage of the total required filtration time
            based on the summer configuration settings.

        """

        _LOGGER.debug("Executing summer filtration slot 1 daily trigger at %s", now)

        # Calculate filtration duration for slot 1
        filtration_duration = self.get_summer_filtration_duration()
        if filtration_duration is None:
            _LOGGER.warning("Could not determine filtration duration for slot 1")
            return

        # Calculate slot 1 percentage
        slot1_percent = (
            self._entry.runtime_data.config.options.filtration.get(
                CONF_OPTIONS_FILTRATION_SUMMER, {}
            )
            .get(CONF_OPTIONS_FILTRATION_SLOT1, {})
            .get(CONF_OPTIONS_FILTRATION_DURATION_PERCENT, 0)
        )
        slot1_duration_minutes = round(filtration_duration * slot1_percent / 100)

        # Calculate end time
        end_time = (now + timedelta(minutes=slot1_duration_minutes)).replace(
            second=0, microsecond=0
        )

        _LOGGER.debug(
            "Slot 1 duration: %s min (%s%% of %s min), end time: %s",
            slot1_duration_minutes,
            slot1_percent,
            filtration_duration,
            end_time,
        )

        # Start filtration and update attributes
        await self.async_start_filtration()
        await self.update_filtration_attributes(
            next_stop_time=end_time.isoformat(),
            active_slot=1,
            slot1_end_time=end_time.isoformat(),
        )

        # Fire start filtration event for slot 1
        await self.publish_event(
            EVENT_TYPE_SLOT1_START,
            {
                "start_time": now.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_minutes": slot1_duration_minutes,
            },
        )

    async def on_summer_filtration_slot2_trigger(self, now: datetime) -> None:
        """Handle the daily trigger for summer filtration slot 2.

        This method is triggered at the scheduled time for the second filtration slot in summer mode.
        It calculates the filtration duration based on the configured percentage for slot 2,
        starts the filtration process, and sets the scheduled end time in binary_sensor attributes.

        Args:
            now (datetime): The current time when the trigger was activated.

        Returns:
            None: The method returns early if filtration duration cannot be determined.

        """

        _LOGGER.debug("Executing summer filtration slot 2 daily trigger at %s", now)

        # Calculate filtration duration for slot 2
        filtration_duration = self.get_summer_filtration_duration()
        if filtration_duration is None:
            _LOGGER.warning("Could not determine filtration duration for slot 2")
            return

        # Calculate slot 2 percentage
        slot2_percent = (
            self._entry.runtime_data.config.options.filtration.get(
                CONF_OPTIONS_FILTRATION_SUMMER, {}
            )
            .get(CONF_OPTIONS_FILTRATION_SLOT2, {})
            .get(CONF_OPTIONS_FILTRATION_DURATION_PERCENT, 0)
        )
        slot2_duration_minutes = round(filtration_duration * slot2_percent / 100)

        # Calculate end time
        end_time = (now + timedelta(minutes=slot2_duration_minutes)).replace(
            second=0, microsecond=0
        )

        _LOGGER.debug(
            "Slot 2 duration: %s min (%s%% of %s min), end time: %s",
            slot2_duration_minutes,
            slot2_percent,
            filtration_duration,
            end_time,
        )

        # Start filtration and update attributes
        await self.async_start_filtration()
        await self.update_filtration_attributes(
            next_stop_time=end_time.isoformat(),
            active_slot=2,
            slot2_end_time=end_time.isoformat(),
        )

        # Fire start filtration event for slot 2
        await self.publish_event(
            EVENT_TYPE_SLOT2_START,
            {
                "start_time": now.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_minutes": slot2_duration_minutes,
            },
        )

    async def on_winter_filtration_start_trigger(self, now: datetime) -> None:
        """Handle winter filtration start trigger events.

        This method is called when the winter filtration schedule triggers a start event.
        It calculates the end time based on configured duration, starts the filtration
        process, and updates entity attributes accordingly.

        Args:
            now (datetime): The current datetime when the trigger was activated.

        Returns:
            None: This method doesn't return any value.

        Raises:
            No explicit exceptions raised, but may log warnings if winter filtration
            configuration is missing.

        """

        _LOGGER.debug("Executing winter filtration start trigger at %s", now)

        # Get winter filtration duration
        winter_result = self.get_winter_filtration_start_end()
        if winter_result is None:
            _LOGGER.warning("No winter filtration configuration found")
            return

        _, winter_duration = winter_result

        # Calculate end time
        end_time = now + winter_duration

        _LOGGER.debug(
            "Winter filtration started, duration: %s, end time: %s",
            winter_duration,
            end_time,
        )

        # Start filtration and update attributes
        await self.async_start_filtration()
        await self.update_filtration_attributes(
            next_stop_time=end_time.isoformat(), active_slot="winter"
        )

        # Fire start filtration event for winter mode
        await self.publish_event(
            EVENT_TYPE_WINTER_START,
            {
                "start_time": now.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_minutes": int(winter_duration.total_seconds() / 60),
            },
        )

    def calculate_next_run_datetime(
        self, current: datetime, target_time: time
    ) -> datetime:
        """Calculate the next datetime to run a scheduled action.

        This method determines when a scheduled action should next occur based on the given
        target time. If the target time has already passed for the current day, it schedules
        the action for the same time on the following day.

        Args:
            current: The current datetime used as a reference.
            target_time: The target time of day when the action should run.

        Returns:
            The datetime of the next scheduled run, which will be either today or tomorrow
            at the specified target time.

        """

        # Convert target_time to datetime for today
        target_datetime = dt_util.start_of_local_day(current)
        target_datetime = target_datetime.replace(
            hour=target_time.hour, minute=target_time.minute, second=target_time.second
        )

        # If the time has already passed today, schedule for tomorrow
        if target_datetime <= current:
            target_datetime += timedelta(days=1)

        return target_datetime

    def calculate_end_time(self, start_time: time, duration: timedelta) -> time:
        """Calculate the end time by adding a duration to a start time.

        This method converts the start time to a datetime object using the current local date as reference,
        adds the specified duration, and extracts the resulting time component.
        Note that this method does not account for multi-day durations in the return value.

        Args:
            start_time (time): The starting time
            duration (timedelta): The duration to add to the starting time

        Returns:
            time: The end time after adding the duration

        """

        # Convert to datetime to be able to add the duration
        reference_date = dt_util.start_of_local_day()
        start_datetime = reference_date.replace(
            hour=start_time.hour, minute=start_time.minute, second=start_time.second
        )

        # Add the duration
        end_datetime = start_datetime + duration

        # Extract the end time (may be on the following day)
        return end_datetime.time()

    def setup_time_events(self) -> None:
        """Set up the time-based event listeners for filtration control.

        This method configures time triggers for automated filtration based on the current pool mode:
        - Creates a periodic check at the start of each minute for filtration stop verification
        - For 'Standard' mode: Configures triggers for summer filtration slots #1 and #2
        - For 'Active-Winter' mode: Configures triggers for winter filtration schedule

        The method first cleans up any existing time listeners to prevent duplicates,
        then creates new listeners based on the current configuration.
        If filtration is disabled in the configuration, no time events will be set up.

        Returns:
            None

        """

        hass = self._entry.runtime_data.coordinator.hass
        entry = self._entry

        # Clean old time listeners if they exist
        for remove_listener in entry.runtime_data.remove_time_listeners:
            remove_listener()

        # Reinitialize the list for new listeners
        entry.runtime_data.remove_time_listeners = []

        if not self.config_filtration_enabled():
            _LOGGER.debug(
                "Filtration not enabled in configuration, skipping time events setup"
            )
            return

        # Configure time-based events for filtration slots depending on the pool mode
        pool_mode = self.get_filtration_pool_mode()
        _LOGGER.info("Setting up time events for pool mode: %s", pool_mode)

        # Set up a periodic check that runs at the beginning of each minute (xx:xx:00)
        # to monitor filtration status. This is only configured when filtration is enabled
        # in the current pool mode (Standard or Active-Winter).
        if (
            pool_mode == "Standard" and self.configuration_filtration_enabled_summer
        ) or (
            pool_mode == "Active-Winter"
            and self.configuration_filtration_enabled_winter
        ):
            # Setup periodic check exactly at the beginning of each minute (0 seconds)
            _LOGGER.info(
                "Setting up periodic filtration check (every minute at xx:xx:00)"
            )
            remove_periodic_listener = async_track_time_change(
                hass, self.check_filtration_status, second=0
            )
            entry.runtime_data.remove_time_listeners.append(remove_periodic_listener)

        now = dt_util.now()

        match pool_mode:
            case "Standard":
                # If filtration is enabled for summer mode, configure the time events
                if self.configuration_filtration_enabled_summer:
                    _LOGGER.debug("Configuring events for Standard mode")

                    # Configure slot 1 start time
                    slot1_start_datetime: datetime | None = (
                        self.get_summer_filtration_slot_start(1)
                    )
                    if slot1_start_datetime:
                        slot1_start_time = slot1_start_datetime.time()

                        # Calculate the next run datetime for slot 1
                        next_slot1_run = self.calculate_next_run_datetime(
                            now, slot1_start_time
                        )
                        _LOGGER.info(
                            "Setting up trigger for slot #1 at %s, next run: %s",
                            slot1_start_time,
                            next_slot1_run,
                        )

                        remove_listener = async_track_time_change(
                            hass,
                            self.on_summer_filtration_slot1_trigger,
                            hour=slot1_start_time.hour,
                            minute=slot1_start_time.minute,
                            second=slot1_start_time.second,
                        )
                        entry.runtime_data.remove_time_listeners.append(remove_listener)

                    # Configure slot 2 start time if duration percent is greater than 0
                    filtration_slot2_percent = (
                        entry.runtime_data.config.options.filtration.get(
                            CONF_OPTIONS_FILTRATION_SUMMER, {}
                        )
                        .get(CONF_OPTIONS_FILTRATION_SLOT2, {})
                        .get(CONF_OPTIONS_FILTRATION_DURATION_PERCENT, 0)
                    )
                    if filtration_slot2_percent > 0:
                        slot2_start_datetime: datetime | None = (
                            self.get_summer_filtration_slot_start(2)
                        )

                        if slot2_start_datetime:
                            slot2_start_time = slot2_start_datetime.time()

                            # Calculate the next run datetime for slot 2
                            next_slot2_run = self.calculate_next_run_datetime(
                                now, slot2_start_time
                            )
                            _LOGGER.info(
                                "Setting up trigger for slot #2 at %s, next run: %s",
                                slot2_start_time,
                                next_slot2_run,
                            )

                            remove_listener = async_track_time_change(
                                hass,
                                self.on_summer_filtration_slot2_trigger,
                                hour=slot2_start_time.hour,
                                minute=slot2_start_time.minute,
                                second=slot2_start_time.second,
                            )
                            entry.runtime_data.remove_time_listeners.append(
                                remove_listener
                            )

            case "Active-Winter":
                # If filtration is enabled for winter mode, configure the time events
                if self.configuration_filtration_enabled_winter:
                    _LOGGER.debug("Configuring events for Active Winter mode")

                    # Get the start time and duration for winter mode
                    if (
                        winter_result := self.get_winter_filtration_start_end()
                    ) is not None:
                        winter_start_time: time
                        winter_duration: timedelta
                        winter_start_time, winter_duration = winter_result

                        # Calculate the next executions for logging
                        next_start_run = self.calculate_next_run_datetime(
                            now, winter_start_time
                        )

                        _LOGGER.debug(
                            "Setting up winter filtration: start at %s (next: %s)",
                            winter_start_time,
                            next_start_run,
                        )

                        # Configure the start trigger
                        remove_listener = async_track_time_change(
                            hass,
                            self.on_winter_filtration_start_trigger,
                            hour=winter_start_time.hour,
                            minute=winter_start_time.minute,
                            second=winter_start_time.second,
                        )
                        entry.runtime_data.remove_time_listeners.append(remove_listener)

                    else:
                        _LOGGER.debug("No winter filtration configuration found")
            case _:
                _LOGGER.debug("No time events configured for pool mode %s", pool_mode)

    async def publish_event(self, event_type: str, event_data: dict) -> None:
        """Publish an event to the Home Assistant event bus.

        This method fires an event of type 'IOPOOL_EVENT' with data containing
        the event type, pool ID, pool title, and any additional event data provided.

        Args:
            event_type (str): The type of event to publish
            event_data (dict): Additional data to include in the event

        Returns:
            None: This method doesn't return anything

        """

        event = {
            "type": event_type,
            "pool_id": self._entry.data[CONF_POOL_ID],
            "pool_title": self._coordinator.get_pool_data(
                self._entry.data[CONF_POOL_ID]
            ).title,
            "data": event_data,
        }
        _LOGGER.debug("Firing event type: %s with data: %s", event_type, event)
        self._entry.runtime_data.coordinator.hass.bus.async_fire(
            f"{DOMAIN.upper()}_EVENT", event
        )
