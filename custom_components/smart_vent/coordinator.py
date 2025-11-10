"""DataUpdateCoordinator for Smart Ventilation Controller."""
from datetime import timedelta
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

        # Initialize state tracking
        self.current_mode = "low"
        self.target_speed = speeds["low"]

        # Auto-boost tracking (will be used in later stages)
        self.auto_boost_active = False
        self.auto_boost_end_time = None
        self.auto_boost_count_today = 0
        self.last_reset_date = None

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
            _LOGGER.error(
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

    async def _set_fan_speed(self, percentage: int) -> None:
        """Set the fan speed to a specific percentage.

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

        # Call the fan.set_percentage service
        try:
            await self.hass.services.async_call(
                "fan",
                "set_percentage",
                {
                    "entity_id": self.fan_entity,
                    "percentage": percentage,
                },
                blocking=True,
            )
            _LOGGER.info("Fan speed set to %d%%", percentage)
        except Exception as err:
            _LOGGER.error(
                "Failed to set fan speed for %s to %d%%: %s",
                self.fan_entity,
                percentage,
                err,
            )

    async def set_mode(self, mode: str) -> None:
        """Set the ventilation mode and adjust fan speed accordingly.

        Args:
            mode: The mode to set ('low', 'mid', or 'boost')
        """
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
            # Read the current switch mode
            switch_mode = self._determine_switch_mode()

            # Read current humidity
            humidity = self._get_humidity()

            # If switch mode changed, update the mode and fan speed
            if switch_mode != self.current_mode:
                await self.set_mode(switch_mode)

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
