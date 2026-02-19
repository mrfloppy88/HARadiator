from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, BTN_PRESET_1
from .coordinator import RadiatorCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: RadiatorCoordinator = data["coordinator"]
    client = data["client"]

    add_entities([RadiatorPresetButton(coordinator, client, i) for i in range(1, 11)])


class RadiatorPresetButton(ButtonEntity):
    def __init__(self, coordinator: RadiatorCoordinator, client, slot: int) -> None:
        self._coordinator = coordinator
        self._client = client
        self._slot = slot
        self._attr_name = f"Radiator Preset {slot}"

    @property
    def available(self) -> bool:
        return bool(self._coordinator.data and self._coordinator.data.connected)

    async def async_press(self) -> None:
        btn_no = BTN_PRESET_1 + (self._slot - 1)
        await self._client.press_button(btn_no)
