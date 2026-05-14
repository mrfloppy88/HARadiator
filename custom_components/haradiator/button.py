"""Button platform for HARadiator."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import preset_count
from .const import DOMAIN, RadiatorOscDescription
from .entity import RadiatorEntity
from .hub import RadiatorOscHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Radiator preset buttons."""
    hub: RadiatorOscHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RadiatorPresetButton(hub, entry, preset_number)
        for preset_number in range(1, preset_count(entry) + 1)
    )


class RadiatorPresetButton(RadiatorEntity, ButtonEntity):
    """Button to recall a Radiator preset."""

    def __init__(self, hub: RadiatorOscHub, entry: ConfigEntry, preset_number: int) -> None:
        """Initialize the preset button."""
        description = RadiatorOscDescription(
            key=f"preset_{preset_number}",
            name=f"Preset {preset_number}",
            address="/radiator/preset",
            value_type="int",
            direction="RX",
            section="PRESET",
            notes="Recall preset by number",
            entity_registry_enabled_default=True,
        )
        super().__init__(hub, entry, description)
        self._preset_number = preset_number

    async def async_press(self) -> None:
        """Recall the preset."""
        await self.hub.async_send(self.entity_description.address, self._preset_number)
