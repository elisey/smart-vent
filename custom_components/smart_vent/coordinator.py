"""DataUpdateCoordinator for Smart Ventilation Controller."""
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SmartVentCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Smart Vent data and controlling the fan."""

    def __init__(
        self,
        hass: HomeAssistant,
        fan_entity: str,
        humidity_sensor: str,
        input_0: str,
        input_1: str,
        speeds: dict[str, int],
        check_interval: int,
        max_boosts_per_day: int,
        auto_boost_duration: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=check_interval),
        )

        # Store configuration
        self.fan_entity = fan_entity
        self.humidity_sensor = humidity_sensor
        self.input_0 = input_0
        self.input_1 = input_1
        self.speeds = speeds
        self.check_interval = check_interval
        self.max_boosts_per_day = max_boosts_per_day
        self.auto_boost_duration = auto_boost_duration

        # Initialize state tracking
        self.current_mode = "low"
        self.target_speed = speeds["low"]

        # Auto-boost tracking
        self.auto_boost_active = False
        self.auto_boost_end_time = None
        self.auto_boost_count_today = 0
        self.last_reset_date = None

        # Manual boost tracking
        self.manual_boost_active = False
        self.mode_before_boost = None
        self.last_switch_mode = None

        _LOGGER.info(
            "SmartVentCoordinator initialized with fan=%s, humidity=%s, inputs=%s/%s",
            fan_entity,
            humidity_sensor,
            input_0,
            input_1,
        )

    def _get_switch_state(self) -> tuple[str | None, str | None]:
        """Get the current state of the two switch inputs.

        Returns:
            Tuple of (input_0_state, input_1_state) as strings ('on' or 'off')
            Returns None for unavailable inputs
        """
        state_0 = self.hass.states.get(self.input_0)
        state_1 = self.hass.states.get(self.input_1)

        # Debug: log the full state objects
        if state_0 is None:
            _LOGGER.debug("Input 0 entity '%s' not found in state registry", self.input_0)
        else:
            _LOGGER.debug("Input 0 state object: %s (state=%s)", state_0, state_0.state)

        if state_1 is None:
            _LOGGER.debug("Input 1 entity '%s' not found in state registry", self.input_1)
        else:
            _LOGGER.debug("Input 1 state object: %s (state=%s)", state_1, state_1.state)

        input_0_state = state_0.state if state_0 else None
        input_1_state = state_1.state if state_1 else None

        _LOGGER.debug(
            "Switch states: input_0=%s, input_1=%s", input_0_state, input_1_state
        )

        return input_0_state, input_1_state

    def _determine_switch_mode(self) -> str:
        """Determine the mode based on switch position.

        Switch logic:
        - off/off (0/0) → low
        - on/off  (1/0) → mid
        - off/on  (0/1) → boost
        - on/on   (1/1) → invalid (returns low as safe fallback)

        Returns:
            Mode string: 'low', 'mid', or 'boost'
        """
        state_0, state_1 = self._get_switch_state()

        # Handle unavailable inputs
        if state_0 is None or state_1 is None:
            _LOGGER.warning(
                "Switch inputs unavailable (input_0=%s, input_1=%s), defaulting to low",
                state_0,
                state_1,
            )
            return "low"

        # Determine mode based on binary combination
        if state_0 == "off" and state_1 == "off":
            mode = "low"
        elif state_0 == "on" and state_1 == "off":
            mode = "mid"
        elif state_0 == "off" and state_1 == "on":
            mode = "boost"
        elif state_0 == "on" and state_1 == "on":
            # Invalid state - both inputs on
            _LOGGER.error(
                "Invalid switch state detected: input_0=on, input_1=on. "
                "This should not happen with a 3-position switch. Defaulting to low mode."
            )
            mode = "low"
        else:
            # Unexpected state values (not 'on' or 'off')
            # This is normal during HA startup when entities haven't initialized yet
            _LOGGER.warning(
                "Unexpected switch state values: input_0=%s, input_1=%s. Defaulting to low mode.",
                state_0,
                state_1,
            )
            mode = "low"

        _LOGGER.debug("Determined switch mode: %s", mode)
        return mode

    def _get_humidity(self) -> float | None:
        """Get the current humidity value from the sensor.

        Returns:
            Humidity as float (0-100), or None if unavailable/invalid
        """
        state = self.hass.states.get(self.humidity_sensor)

        # Check if sensor exists
        if state is None:
            _LOGGER.warning("Humidity sensor %s not found", self.humidity_sensor)
            return None

        # Check if sensor is unavailable
        if state.state in ("unavailable", "unknown", "none", "None"):
            _LOGGER.warning(
                "Humidity sensor %s is unavailable (state: %s)",
                self.humidity_sensor,
                state.state,
            )
            return None

        # Try to convert to float
        try:
            humidity = float(state.state)
            _LOGGER.debug("Current humidity: %.1f%%", humidity)
            return humidity
        except (ValueError, TypeError) as err:
            _LOGGER.error(
                "Invalid humidity value from %s: %s (error: %s)",
                self.humidity_sensor,
                state.state,
                err,
            )
            return None

    def _reset_daily_counter_if_needed(self) -> None:
        """Reset the auto-boost counter if a new day has started."""
        current_date = datetime.now().date()

        if self.last_reset_date is None or current_date != self.last_reset_date:
            self.auto_boost_count_today = 0
            self.last_reset_date = current_date
            _LOGGER.info("Daily auto-boost counter reset")

    def _should_trigger_auto_boost(self) -> bool:
        """Check if conditions are met to trigger automatic boost.

        Returns:
            True if auto-boost should be activated, False otherwise
        """
        # Already active
        if self.auto_boost_active:
            return False

        # Check humidity
        humidity = self._get_humidity()
        if humidity is None:
            _LOGGER.debug("Auto-boost check: humidity unavailable")
            return False

        if humidity <= 80:
            _LOGGER.debug("Auto-boost check: humidity %.1f%% <= 80%%", humidity)
            return False

        # Check daily limit
        if self.auto_boost_count_today >= self.max_boosts_per_day:
            _LOGGER.warning(
                "Auto-boost check: daily limit reached (%d/%d)",
                self.auto_boost_count_today,
                self.max_boosts_per_day,
            )
            return False

        _LOGGER.debug("Auto-boost check: all conditions met (humidity: %.1f%%)", humidity)
        return True

    async def _activate_auto_boost(self) -> None:
        """Activate automatic boost mode."""
        self.auto_boost_active = True
        self.manual_boost_active = False
        self.auto_boost_end_time = datetime.now() + timedelta(minutes=self.auto_boost_duration)
        self.auto_boost_count_today += 1

        # Set fan to boost speed
        await self._set_fan_speed(self.speeds["boost"])
        self.target_speed = self.speeds["boost"]
        self.current_mode = "boost"

        end_time_str = self.auto_boost_end_time.strftime("%H:%M")
        _LOGGER.info(
            "Auto-boost activated (%d/%d today), duration: %d min, will end at %s",
            self.auto_boost_count_today,
            self.max_boosts_per_day,
            self.auto_boost_duration,
            end_time_str,
        )

    async def force_boost(self) -> None:
        """Force boost mode activation via service call.

        Does not check daily limit and does not increment counter.
        Returns to previous mode after timeout.
        """
        # Save current mode to return to after timeout
        self.mode_before_boost = self.current_mode

        # Cancel any existing boost
        self._cancel_auto_boost()

        # Activate manual boost
        self.auto_boost_active = True
        self.manual_boost_active = True
        self.auto_boost_end_time = datetime.now() + timedelta(minutes=self.auto_boost_duration)

        # Set fan to boost speed
        await self._set_fan_speed(self.speeds["boost"])
        self.target_speed = self.speeds["boost"]
        self.current_mode = "boost"

        end_time_str = self.auto_boost_end_time.strftime("%H:%M")
        _LOGGER.info(
            "Force boost activated via service (duration: %d min, will return to '%s', will end at %s)",
            self.auto_boost_duration,
            self.mode_before_boost,
            end_time_str,
        )

    def _check_auto_boost_timeout(self) -> str | None:
        """Check if auto-boost has timed out.

        Returns:
            Mode to return to if timeout occurred, None otherwise
        """
        if not self.auto_boost_active:
            return None

        if datetime.now() >= self.auto_boost_end_time:
            # Determine which mode to return to
            if self.manual_boost_active:
                # Manual boost - return to saved mode
                return_mode = self.mode_before_boost or "mid"
                _LOGGER.info("Manual boost timeout reached, returning to '%s'", return_mode)
            else:
                # Automatic boost - return to mid
                return_mode = "mid"
                _LOGGER.info("Auto-boost timeout reached, returning to 'mid'")

            # Clear boost flags
            self.auto_boost_active = False
            self.manual_boost_active = False
            self.auto_boost_end_time = None
            self.mode_before_boost = None

            return return_mode

        return None

    def _cancel_auto_boost(self) -> None:
        """Cancel active auto-boost or manual boost."""
        if self.auto_boost_active:
            boost_type = "manual" if self.manual_boost_active else "auto"
            self.auto_boost_active = False
            self.manual_boost_active = False
            self.auto_boost_end_time = None
            self.mode_before_boost = None
            _LOGGER.info("%s boost cancelled", boost_type.capitalize())

    async def _set_fan_speed(self, percentage: int) -> None:
        """Set the fan speed to a specific percentage.

        Supports both fan entities (using fan.set_percentage) and light entities
        (using light.turn_on with brightness_pct) for Shelly Dimmers.

        Args:
            percentage: Fan speed percentage (0-100)
        """
        # Check if fan entity exists
        fan_state = self.hass.states.get(self.fan_entity)
        if fan_state is None:
            _LOGGER.error("Fan entity %s not found, cannot set speed", self.fan_entity)
            return

        # Check if fan is available
        if fan_state.state in ("unavailable", "unknown"):
            _LOGGER.warning(
                "Fan entity %s is unavailable (state: %s), skipping speed change",
                self.fan_entity,
                fan_state.state,
            )
            return

        # Determine entity type and call appropriate service
        is_light_entity = self.fan_entity.startswith("light.")

        if is_light_entity:
            # For light entities (Shelly Dimmers), use light.turn_on with brightness_pct
            service_domain = "light"
            service_name = "turn_on"
            service_data = {
                "entity_id": self.fan_entity,
                "brightness_pct": percentage,
            }
        else:
            # For fan entities, use fan.set_percentage
            service_domain = "fan"
            service_name = "set_percentage"
            service_data = {
                "entity_id": self.fan_entity,
                "percentage": percentage,
            }

        # Call the appropriate service
        try:
            await self.hass.services.async_call(
                service_domain,
                service_name,
                service_data,
                blocking=True,
            )
            entity_type = "Light" if is_light_entity else "Fan"
            _LOGGER.info("%s speed set to %d%%", entity_type, percentage)
        except Exception as err:
            _LOGGER.error(
                "Failed to set speed for %s to %d%%: %s",
                self.fan_entity,
                percentage,
                err,
            )

    async def set_mode(self, mode: str) -> None:
        """Set the ventilation mode and adjust fan speed accordingly.

        Args:
            mode: The mode to set ('low', 'mid', or 'boost')
        """
        # Cancel any active auto-boost (manual mode change takes priority)
        self._cancel_auto_boost()

        # Validate mode
        if mode not in ("low", "mid", "boost"):
            _LOGGER.error("Invalid mode '%s', must be one of: low, mid, boost", mode)
            return

        # Check if mode actually changed
        if mode == self.current_mode:
            _LOGGER.debug("Mode already set to '%s', no change needed", mode)
            return

        # Update current mode
        old_mode = self.current_mode
        self.current_mode = mode

        # Get speed for the new mode
        speed = self.speeds[mode]
        self.target_speed = speed

        # Set the fan speed
        await self._set_fan_speed(speed)

        _LOGGER.info("Mode changed from '%s' to '%s' (speed: %d%%)", old_mode, mode, speed)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the system.

        This is called automatically by the DataUpdateCoordinator
        at the interval specified in update_interval.
        """
        try:
            # Reset daily counter if needed (new day)
            self._reset_daily_counter_if_needed()

            # Read inputs
            switch_mode = self._determine_switch_mode()
            humidity = self._get_humidity()

            # Check if auto-boost has timed out (returns mode to restore, or None)
            timeout_return_mode = self._check_auto_boost_timeout()

            # Detect switch position changes - cancel manual boost if switch moved
            if self.manual_boost_active and self.last_switch_mode and switch_mode != self.last_switch_mode:
                _LOGGER.info("Switch position changed from '%s' to '%s', cancelling manual boost",
                           self.last_switch_mode, switch_mode)
                self._cancel_auto_boost()

            # Update last known switch position
            self.last_switch_mode = switch_mode

            # Check if manual boost is active - if so, maintain it regardless of switch
            if self.manual_boost_active:
                # Manual boost stays active - only timeout or explicit switch CHANGE cancels it
                _LOGGER.debug("Manual boost active, maintaining boost speed")
                # Don't follow switch position while manual boost is active

            # Handle timeout - if boost just timed out, return to saved mode
            elif timeout_return_mode:
                # Boost timed out, return to the saved mode
                if self.current_mode != timeout_return_mode:
                    await self.set_mode(timeout_return_mode)

            # Otherwise, follow switch position
            elif switch_mode == "low":
                # Priority 1: Low mode cancels auto-boost (not manual boost)
                if self.auto_boost_active and not self.manual_boost_active:
                    self._cancel_auto_boost()
                if self.current_mode != "low":
                    await self.set_mode("low")

            elif switch_mode == "boost":
                # Priority 2: Manual boost on switch cancels any boost
                self._cancel_auto_boost()
                if self.current_mode != "boost":
                    await self.set_mode("boost")

            elif switch_mode == "mid":
                # Priority 3: Mid mode - handle auto-boost logic
                if self.auto_boost_active:
                    # Auto-boost is still active, keep boost speed
                    _LOGGER.debug("Auto-boost active, maintaining boost speed")
                elif self._should_trigger_auto_boost():
                    # Conditions met for new auto-boost
                    await self._activate_auto_boost()
                elif self.current_mode != "mid":
                    # Normal mid operation
                    await self.set_mode("mid")

            data = {
                "current_mode": self.current_mode,
                "target_speed": self.target_speed,
                "auto_boost_active": self.auto_boost_active,
                "humidity": humidity,
            }

            _LOGGER.debug("Update data: %s", data)
            return data

        except Exception as err:
            _LOGGER.error("Error updating Smart Vent data: %s", err)
            raise UpdateFailed(f"Error communicating with Smart Vent: {err}") from err
