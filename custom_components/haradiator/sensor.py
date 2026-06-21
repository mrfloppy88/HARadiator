"""Sensor entities for HARadiator."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    NUMBER_DESCRIPTIONS,
    SENSOR_DESCRIPTIONS,
    SWITCH_DESCRIPTIONS,
    RadiatorOscDescription,
)
from .hub import RadiatorOscHub


ENABLED_BY_DEFAULT_ADDRESSES: set[str] = {
    "/radiator/preset/current",
    "/radiator/master/blackout",
    "/radiator/master/level",
    "/radiator/master/size",
    "/radiator/color/mode/name",
    "/radiator/ed/status",
    "/radiator/shapeA/shape/name",
    "/radiator/shapeB/shape/name",
    "/radiator/lfo1/on",
    "/radiator/lfo2/on",
    "/radiator/lfo3/on",
}


def _read_descriptions() -> tuple[RadiatorOscDescription, ...]:
    """Return all OSC descriptions that can provide read-side feedback."""
    descriptions: list[RadiatorOscDescription] = []
    seen_addresses: set[str] = set()

    for description in (
        *SENSOR_DESCRIPTIONS,
        *NUMBER_DESCRIPTIONS,
        *SWITCH_DESCRIPTIONS,
    ):
        if "TX" not in description.direction:
            continue

        if description.address in seen_addresses:
            continue

        seen_addresses.add(description.address)
        descriptions.append(description)

    return tuple(descriptions)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[RadiatorOscHub],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HARadiator read-side sensor entities."""
    hub = entry.runtime_data

    async_add_entities(
        [
            RadiatorOscReadSensor(
                entry=entry,
                hub=hub,
                description=description,
            )
            for description in _read_descriptions()
        ]
    )


class RadiatorOscReadSensor(SensorEntity):
    """Read-only OSC feedback sensor for Radiator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        *,
        entry: ConfigEntry[RadiatorOscHub],
        hub: RadiatorOscHub,
        description: RadiatorOscDescription,
    ) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._hub = hub
        self._description = description

        self.entity_description = SensorEntityDescription(
            key=description.key,
            name=description.name,
            icon=_icon_for_description(description),
        )

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_entity_registry_enabled_default = (
            description.address in ENABLED_BY_DEFAULT_ADDRESSES
        )
        self._attr_native_value: Any = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Neon Captain",
            model="Radiator",
            sw_version="OSC beta",
        )

        extra_attributes: dict[str, Any] = {
            "osc_address": description.address,
            "osc_direction": description.direction,
            "osc_value_type": description.value_type,
        }

        if description.section:
            extra_attributes["osc_section"] = description.section

        if description.notes:
            extra_attributes["osc_notes"] = description.notes

        if description.native_min_value is not None:
            extra_attributes["osc_min"] = description.native_min_value

        if description.native_max_value is not None:
            extra_attributes["osc_max"] = description.native_max_value

        if description.native_step is not None:
            extra_attributes["osc_step"] = description.native_step

        self._attr_extra_state_attributes = extra_attributes
        self._unsubscribe = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to OSC feedback."""
        self._unsubscribe = self._hub.subscribe(
            self._description.address,
            self._handle_osc_update,
        )

        current_value = self._hub.get_state(self._description.address)
        if current_value is not None:
            self._set_value(current_value)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from OSC feedback."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    def _handle_osc_update(self, address: str, value: Any) -> None:
        """Handle an OSC update from Radiator."""
        self._set_value(value)
        self.async_write_ha_state()

    def _set_value(self, value: Any) -> None:
        """Convert OSC values to Home Assistant sensor-safe values."""
        if value is None:
            self._attr_native_value = None
            return

        if isinstance(value, list | tuple):
            self._attr_native_value = ", ".join(str(item) for item in value)
            return

        if self._description.value_type == "string":
            self._attr_native_value = str(value)
            return

        if self._description.value_type == "bool":
            try:
                self._attr_native_value = "on" if float(value) >= 0.5 else "off"
            except (TypeError, ValueError):
                self._attr_native_value = str(value)
            return

        if self._description.value_type == "int":
            try:
                self._attr_native_value = int(float(value))
            except (TypeError, ValueError):
                self._attr_native_value = str(value)
            return

        if self._description.value_type == "float":
            try:
                self._attr_native_value = round(float(value), 6)
            except (TypeError, ValueError):
                self._attr_native_value = str(value)
            return

        self._attr_native_value = value


def _icon_for_description(description: RadiatorOscDescription) -> str:
    """Return a useful icon for an OSC feedback sensor."""
    address = description.address.lower()
    key = description.key.lower()

    if "preset" in address:
        return "mdi:playlist-check"

    if "blackout" in address:
        return "mdi:power"

    if "ed/status" in address:
        return "mdi:lan-connect"

    if "color" in address or "hue" in address or "rgb" in address:
        return "mdi:palette"

    if "lfo" in address:
        return "mdi:sine-wave"

    if "shapea" in address or "shapeb" in address or "shape" in address:
        return "mdi:shape-outline"

    if "trans" in address:
        return "mdi:axis-arrow"

    if "clone" in address:
        return "mdi:content-duplicate"

    if "master" in address:
        return "mdi:tune"

    if key.endswith("_name") or address.endswith("/name"):
        return "mdi:label-outline"

    if description.value_type == "bool":
        return "mdi:toggle-switch"

    return "mdi:counter"