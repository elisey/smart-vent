"""Smart Ventilation Controller for Home Assistant."""
import logging

import voluptuous as vol

from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.discovery import async_load_platform
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_MAX_BOOSTS_PER_DAY,
    DEFAULT_SPEEDS,
)
from .coordinator import SmartVentCoordinator

_LOGGER = logging.getLogger(__name__)

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required("fan_entity"): cv.entity_id,
                vol.Required("humidity_sensor"): cv.entity_id,
                vol.Required("input_0"): cv.entity_id,
                vol.Required("input_1"): cv.entity_id,
                vol.Optional("speeds", default=DEFAULT_SPEEDS): vol.Schema(
                    {
                        vol.Required("low"): vol.All(
                            vol.Coerce(int), vol.Range(min=0, max=100)
                        ),
                        vol.Required("mid"): vol.All(
                            vol.Coerce(int), vol.Range(min=0, max=100)
                        ),
                        vol.Required("boost"): vol.All(
                            vol.Coerce(int), vol.Range(min=0, max=100)
                        ),
                    }
                ),
                vol.Optional(
                    "check_interval", default=DEFAULT_CHECK_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=3600)),
                vol.Optional(
                    "max_boosts_per_day", default=DEFAULT_MAX_BOOSTS_PER_DAY
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Smart Ventilation Controller component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    # Create the coordinator
    coordinator = SmartVentCoordinator(
        hass=hass,
        fan_entity=conf["fan_entity"],
        humidity_sensor=conf["humidity_sensor"],
        input_0=conf["input_0"],
        input_1=conf["input_1"],
        speeds=conf["speeds"],
        check_interval=conf["check_interval"],
        max_boosts_per_day=conf["max_boosts_per_day"],
    )

    # Store coordinator in hass.data
    hass.data[DOMAIN] = coordinator

    # Perform first refresh of coordinator data and start polling
    await coordinator.async_refresh()

    # Set up state change listeners for input entities
    @callback
    def async_state_changed_listener(event):
        """Handle state changes of monitored entities."""
        entity_id = event.data.get("entity_id")
        _LOGGER.debug("State change detected for %s, triggering immediate refresh", entity_id)
        # Use async_refresh() instead of async_request_refresh() to bypass debounce
        hass.async_create_task(coordinator.async_refresh())

    # Listen for changes to input sensors
    async_track_state_change_event(
        hass,
        [conf["input_0"], conf["input_1"], conf["humidity_sensor"]],
        async_state_changed_listener,
    )

    # Set up periodic polling for checking conditions (auto-boost timers, etc.)
    @callback
    def async_periodic_update(now):
        """Periodic update callback."""
        _LOGGER.debug("Periodic update triggered (every %d seconds)", conf["check_interval"])
        hass.async_create_task(coordinator.async_refresh())

    async_track_time_interval(
        hass,
        async_periodic_update,
        timedelta(seconds=conf["check_interval"]),
    )

    # Load the fan platform
    hass.async_create_task(
        async_load_platform(
            hass,
            "fan",
            DOMAIN,
            {"coordinator": coordinator},
            config,
        )
    )

    # Register services
    async def handle_set_mode(call):
        """Handle the set_mode service call."""
        mode = call.data.get("mode")

        # Validate mode
        if mode not in ["low", "mid", "boost"]:
            _LOGGER.error("Invalid mode '%s'. Must be one of: low, mid, boost", mode)
            return

        _LOGGER.info("Service call: set_mode to '%s'", mode)
        await coordinator.set_mode(mode)

    hass.services.async_register(DOMAIN, "set_mode", handle_set_mode)

    _LOGGER.info("Smart Ventilation Controller component loaded")
    _LOGGER.debug(
        "Configuration: fan=%s, humidity=%s, inputs=%s/%s",
        conf["fan_entity"],
        conf["humidity_sensor"],
        conf["input_0"],
        conf["input_1"],
    )

    return True
