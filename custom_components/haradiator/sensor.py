"""Sensor entities for HARadiator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import RadiatorOscHub


@dataclass(frozen=True, kw_only=True)
class RadiatorSensorDescription(SensorEntityDescription):
    """Description for a Radiator sensor."""

    address: str
    convert_percent: bool = False


SENSORS: tuple[RadiatorSensorDescription, ...] = (
    RadiatorSensorDescription(
        key="current_preset",
        name="Current Preset",
        icon="mdi:playlist-check",
        address="/radiator/preset/current",
    ),
    RadiatorSensorDescription(
        key="master_level",
        name="Master Level",
        icon="mdi:brightness-6",
        address="/radiator/master/level",
        native_unit_of_measurement=PERCENTAGE,
        convert_percent=True,
    ),
    RadiatorSensorDescription(
        key="master_size",
        name="Master Size",
        icon="mdi:arrow-expand-all",
        address="/radiator/master/size",
        native_unit_of_measurement=PERCENTAGE,
        convert_percent=True,
    ),
    RadiatorSensorDescription(
        key="ed_status",
        name="Ether Dream Status",
        icon="mdi:lan-connect",
        address="/radiator/ed/status",
    ),
    RadiatorSensorDescription(
        key="color_mode",
        name="Color Mode",
        icon="mdi:palette",
        address="/radiator/color/mode/name",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[RadiatorOscHub],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HARadiator sensor entities."""
    hub = entry.runtime_data

    async_add_entities(
        [
            RadiatorSensor(
                entry=entry,
                hub=hub,
                description=description,
            )
            for description in SENSORS
        ]
    )


class RadiatorSensor(SensorEntity):
    """Radiator feedback sensor."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    entity_description: RadiatorSensorDescription

    def __init__(
        self,
        *,
        entry: ConfigEntry[RadiatorOscHub],
        hub: RadiatorOscHub,
        description: RadiatorSensorDescription,
    ) -> None:
        """Initialize sensor."""
        self._entry = entry
        self._hub = hub
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_native_value: Any = None
        self._unsubscribe = None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Neon Captain",
            "model": "Radiator",
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to Radiator feedback."""
        self._unsubscribe = self._hub.subscribe(
            self.entity_description.address,
            self._handle_update,
        )

        current_value = self._hub.get_state(self.entity_description.address)
        if current_value is not None:
            self._set_value(current_value)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from Radiator feedback."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    def _handle_update(self, address: str, value: Any) -> None:
        """Handle OSC update."""
        self._set_value(value)
        self.async_write_ha_state()

    def _set_value(self, value: Any) -> None:
        """Set sensor value."""
        if self.entity_description.convert_percent:
            try:
                self._attr_native_value = round(float(value) * 100, 1)
                return
            except (TypeError, ValueError):
                self._attr_native_value = None
                return

        if self.entity_description.key == "current_preset":
            try:
                self._attr_native_value = int(float(value))
                return
            except (TypeError, ValueError):
                self._attr_native_value = value
                return

        self._attr_native_value = value