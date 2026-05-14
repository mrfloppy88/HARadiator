"""Sensor platform for HARadiator."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import should_expose_entity
from .const import DOMAIN, SENSOR_DESCRIPTIONS, RadiatorOscDescription
from .entity import RadiatorEntity
from .hub import RadiatorOscHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Radiator sensor entities."""
    hub: RadiatorOscHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RadiatorSensor(hub, entry, description)
        for description in SENSOR_DESCRIPTIONS
        if should_expose_entity(entry, description.entity_registry_enabled_default)
    )


class RadiatorSensor(RadiatorEntity, SensorEntity):
    """Read-only OSC state sensor."""

    @property
    def native_value(self) -> str | int | float | None:
        """Return the current sensor value."""
        value: Any = self.raw_value
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (str, int, float)):
            return value
        return str(value)
