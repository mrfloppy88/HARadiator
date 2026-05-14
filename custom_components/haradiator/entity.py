"""Shared entity helpers for HARadiator."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, RadiatorOscDescription
from .hub import RadiatorOscHub


class RadiatorEntity(Entity):
    """Base class for Radiator OSC entities."""

    _attr_has_entity_name = True
    should_poll = False

    def __init__(
        self,
        hub: RadiatorOscHub,
        entry: ConfigEntry,
        description: RadiatorOscDescription,
    ) -> None:
        """Initialize the entity."""
        self.hub = hub
        self.entity_description = description
        self._attr_name = description.name
        self._attr_entity_registry_enabled_default = (
            description.entity_registry_enabled_default
        )
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Neon Captain",
            model="Radiator",
            sw_version="OSC beta",
        )
        self._attr_extra_state_attributes = {
            "osc_address": description.address,
            "osc_direction": description.direction,
            "osc_section": description.section,
        }
        if description.notes:
            self._attr_extra_state_attributes["osc_notes"] = description.notes
        self._unsubscribe: Callable[[], None] | None = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to OSC state updates."""
        self._unsubscribe = self.hub.subscribe(
            self.entity_description.address, self._async_on_osc_state
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from OSC state updates."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    @callback
    def _async_on_osc_state(self, address: str, value: Any) -> None:
        """Handle a received OSC value."""
        self.async_write_ha_state()

    @property
    def raw_value(self) -> Any:
        """Return the raw cached OSC value."""
        return self.hub.get_state(self.entity_description.address)
