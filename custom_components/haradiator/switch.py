"""Switch platform for HARadiator."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import should_expose_entity
from .const import DOMAIN, SWITCH_DESCRIPTIONS, RadiatorOscDescription
from .entity import RadiatorEntity
from .hub import RadiatorOscHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Radiator switch entities."""
    hub: RadiatorOscHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RadiatorSwitch(hub, entry, description)
        for description in SWITCH_DESCRIPTIONS
        if should_expose_entity(entry, description.entity_registry_enabled_default)
    )


class RadiatorSwitch(RadiatorEntity, SwitchEntity):
    """Boolean OSC parameter."""

    def __init__(
        self,
        hub: RadiatorOscHub,
        entry: ConfigEntry,
        description: RadiatorOscDescription,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(hub, entry, description)
        if description.address == "/radiator/master/blackout":
            self._attr_icon = "mdi:laser-pointer"

    @property
    def is_on(self) -> bool | None:
        """Return the current switch state."""
        value: Any = self.raw_value
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "on", "yes"}
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the OSC flag on."""
        await self.hub.async_send(self.entity_description.address, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the OSC flag off."""
        await self.hub.async_send(self.entity_description.address, 0)
