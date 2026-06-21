"""Number entities for HARadiator."""
from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import RadiatorOscHub

MASTER_LEVEL_ADDRESS = "/radiator/master/level"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HARadiator number entities."""
    hub: RadiatorOscHub = entry.runtime_data

    async_add_entities(
        [
            RadiatorMasterLevelNumber(
                entry=entry,
                hub=hub,
            )
        ]
    )


class RadiatorMasterLevelNumber(NumberEntity):
    """Master level control."""

    _attr_has_entity_name = True
    _attr_name = "Master Level"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        *,
        entry: ConfigEntry,
        hub: RadiatorOscHub,
    ) -> None:
        """Initialize entity."""
        self._entry = entry
        self._hub = hub

        self._attr_unique_id = f"{entry.entry_id}_master_level"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Neon Captain",
            model="Radiator",
        )

        self._attr_native_value = 100.0
        self._unsubscribe = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to feedback."""
        self._unsubscribe = self._hub.subscribe(
            MASTER_LEVEL_ADDRESS,
            self._handle_update,
        )

        current = self._hub.get_state(MASTER_LEVEL_ADDRESS)
        if current is not None:
            self._set_from_osc(current)

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup."""
        if self._unsubscribe:
            self._unsubscribe()

    async def async_set_native_value(self, value: float) -> None:
        """Set value from Home Assistant."""

        value = max(0.0, min(100.0, float(value)))

        osc_value = value / 100.0

        await self._hub.async_send(
            MASTER_LEVEL_ADDRESS,
            osc_value,
        )

        self._attr_native_value = value
        self.async_write_ha_state()

    def _handle_update(self, address: str, value: Any) -> None:
        """Handle feedback from Radiator."""
        self._set_from_osc(value)
        self.async_write_ha_state()

    def _set_from_osc(self, value: Any) -> None:
        """Convert OSC 0.0-1.0 to HA 0-100."""
        try:
            self._attr_native_value = round(float(value) * 100.0, 1)
        except (TypeError, ValueError):
            pass