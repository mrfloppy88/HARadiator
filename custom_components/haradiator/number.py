"""Number platform for HARadiator."""
from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import should_expose_entity
from .const import DOMAIN, NUMBER_DESCRIPTIONS, RadiatorOscDescription
from .entity import RadiatorEntity
from .hub import RadiatorOscHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Radiator number entities."""
    hub: RadiatorOscHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RadiatorNumber(hub, entry, description)
        for description in NUMBER_DESCRIPTIONS
        if should_expose_entity(entry, description.entity_registry_enabled_default)
    )


class RadiatorNumber(RadiatorEntity, NumberEntity):
    """Numeric OSC parameter."""

    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        hub: RadiatorOscHub,
        entry: ConfigEntry,
        description: RadiatorOscDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(hub, entry, description)
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        if description.value_type == "int":
            self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Return the current numeric state."""
        value: Any = self.raw_value
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the numeric value."""
        if self.entity_description.value_type == "int":
            await self.hub.async_send(self.entity_description.address, int(value))
            return
        await self.hub.async_send(self.entity_description.address, float(value))
