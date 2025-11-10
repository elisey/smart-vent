"""Smart Ventilation Controller for Home Assistant."""
import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant
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

    # Perform first refresh of coordinator data
    await coordinator.async_refresh()

    _LOGGER.info("Smart Ventilation Controller component loaded")
    _LOGGER.debug(
        "Configuration: fan=%s, humidity=%s, inputs=%s/%s",
        conf["fan_entity"],
        conf["humidity_sensor"],
        conf["input_0"],
        conf["input_1"],
    )

    return True
