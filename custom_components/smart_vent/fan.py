"""Fan platform for Smart Ventilation Controller."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartVentCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up the Smart Vent fan platform."""
    if discovery_info is None:
        return

    coordinator = discovery_info["coordinator"]

    async_add_entities([SmartVentFan(coordinator)], True)
    _LOGGER.info("Smart Vent fan entity created")


class SmartVentFan(CoordinatorEntity, FanEntity):
    """Representation of the Smart Ventilation Controller as a fan entity."""

    def __init__(self, coordinator: SmartVentCoordinator) -> None:
        """Initialize the fan entity."""
        super().__init__(coordinator)
        self._attr_name = "Smart Ventilation"
        self._attr_unique_id = "smart_vent_fan"
        self._attr_should_poll = False
        self._attr_speed_count = 100
        self._attr_supported_features = FanEntityFeature.SET_SPEED

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on (always on for this controller)."""
        return True

    @property
    def percentage(self) -> int:
        """Return the current speed percentage."""
        return self.coordinator.target_speed

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {
            "mode": self.coordinator.current_mode,
            "humidity": self.coordinator.data.get("humidity") if self.coordinator.data else None,
            "auto_boost_active": self.coordinator.auto_boost_active,
            "auto_boost_count_today": self.coordinator.auto_boost_count_today,
        }
        _LOGGER.debug("Fan extra_state_attributes: %s", attrs)
        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
