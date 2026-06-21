"""Select entities for HARadiator."""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import preset_count
from .const import DOMAIN
from .hub import RadiatorOscHub

PRESET_SET_ADDRESS = "/radiator/preset"
PRESET_CURRENT_ADDRESS = "/radiator/preset/current"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[RadiatorOscHub],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HARadiator select entities."""
    hub = entry.runtime_data

    async_add_entities(
        [
            RadiatorPresetSelect(
                entry=entry,
                hub=hub,
                count=preset_count(entry),
            )
        ]
    )


class RadiatorPresetSelect(SelectEntity):
    """Preset select entity for Radiator."""

    _attr_has_entity_name = True
    _attr_name = "Preset"
    _attr_icon = "mdi:playlist-play"
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        *,
        entry: ConfigEntry[RadiatorOscHub],
        hub: RadiatorOscHub,
        count: int,
    ) -> None:
        """Initialize the preset select."""
        self._entry = entry
        self._hub = hub
        self._count = max(1, count)
        self._attr_unique_id = f"{entry.entry_id}_preset_select"
        self._attr_options = [f"Preset {number}" for number in range(1, self._count + 1)]
        self._attr_current_option: str | None = None
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
        """Subscribe to Radiator preset feedback."""
        self._unsubscribe = self._hub.subscribe(
            PRESET_CURRENT_ADDRESS,
            self._handle_preset_update,
        )

        current_value = self._hub.get_state(PRESET_CURRENT_ADDRESS)
        if current_value is not None:
            self._set_current_from_value(current_value)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from Radiator preset feedback."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    async def async_select_option(self, option: str) -> None:
        """Select a Radiator preset."""
        try:
            preset_number = int(option.replace("Preset ", ""))
        except ValueError:
            return

        await self._hub.async_send(PRESET_SET_ADDRESS, float(preset_number))

        self._attr_current_option = option
        self.async_write_ha_state()

    def _handle_preset_update(self, address: str, value: Any) -> None:
        """Handle preset feedback from Radiator."""
        self._set_current_from_value(value)
        self.async_write_ha_state()

    def _set_current_from_value(self, value: Any) -> None:
        """Convert Radiator preset number to a select option."""
        try:
            preset_number = int(float(value))
        except (TypeError, ValueError):
            return

        if preset_number < 1 or preset_number > self._count:
            return

        self._attr_current_option = f"Preset {preset_number}"