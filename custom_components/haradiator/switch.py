"""Switch entities for HARadiator."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import RadiatorOscHub

BLACKOUT_ADDRESS = "/radiator/master/blackout"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[RadiatorOscHub],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HARadiator switch entities."""
    hub = entry.runtime_data

    async_add_entities(
        [
            RadiatorBlackoutSwitch(
                entry=entry,
                hub=hub,
            )
        ]
    )


class RadiatorBlackoutSwitch(SwitchEntity):
    """Global Radiator blackout switch."""

    _attr_has_entity_name = True
    _attr_name = "Blackout"
    _attr_icon = "mdi:power"
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        *,
        entry: ConfigEntry[RadiatorOscHub],
        hub: RadiatorOscHub,
    ) -> None:
        """Initialize blackout switch."""
        self._entry = entry
        self._hub = hub
        self._attr_unique_id = f"{entry.entry_id}_blackout"
        self._attr_is_on: bool | None = None
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
        """Subscribe to Radiator blackout feedback."""
        self._unsubscribe = self._hub.subscribe(
            BLACKOUT_ADDRESS,
            self._handle_blackout_update,
        )

        current_value = self._hub.get_state(BLACKOUT_ADDRESS)
        if current_value is not None:
            self._set_state_from_value(current_value)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from Radiator blackout feedback."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn blackout on."""
        await self._hub.async_send(BLACKOUT_ADDRESS, 1.0)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn blackout off."""
        await self._hub.async_send(BLACKOUT_ADDRESS, 0.0)
        self._attr_is_on = False
        self.async_write_ha_state()

    def _handle_blackout_update(self, address: str, value: Any) -> None:
        """Handle blackout feedback from Radiator."""
        self._set_state_from_value(value)
        self.async_write_ha_state()

    def _set_state_from_value(self, value: Any) -> None:
        """Convert Radiator float value to switch state."""
        try:
            self._attr_is_on = float(value) >= 0.5
        except (TypeError, ValueError):
            self._attr_is_on = None