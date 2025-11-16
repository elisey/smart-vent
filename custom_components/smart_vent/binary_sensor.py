"""Binary sensor platform for Smart Ventilation Controller."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up the Smart Vent binary sensor platform."""
    if discovery_info is None:
        return

    coordinator = discovery_info["coordinator"]
    async_add_entities([SmartVentAutoBoostSensor(coordinator)], True)


class SmartVentAutoBoostSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that indicates if auto-boost is active."""

    def __init__(self, coordinator) -> None:
        """Initialize the auto-boost sensor."""
        super().__init__(coordinator)
        self._attr_name = "Smart Vent Auto Boost"
        self._attr_unique_id = "smart_vent_auto_boost"

    @property
    def is_on(self) -> bool:
        """Return true if auto-boost is active."""
        return self.coordinator.auto_boost_active

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self.is_on:
            return "mdi:fan-plus"
        return "mdi:fan"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        attributes = {
            "boosts_used_today": self.coordinator.auto_boost_count_today,
            "max_boosts_per_day": self.coordinator.max_boosts_per_day,
        }

        # Add time remaining if boost is active
        if self.coordinator.auto_boost_active and self.coordinator.auto_boost_end_time:
            now = datetime.now()
            time_remaining = self.coordinator.auto_boost_end_time - now
            if time_remaining.total_seconds() > 0:
                attributes["time_remaining_seconds"] = int(time_remaining.total_seconds())
                attributes["time_remaining_minutes"] = round(time_remaining.total_seconds() / 60, 1)
                attributes["boost_end_time"] = self.coordinator.auto_boost_end_time.isoformat()

        return attributes
