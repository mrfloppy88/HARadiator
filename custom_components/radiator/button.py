from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SLOT_COUNT
from .coordinator import RadiatorCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: RadiatorCoordinator = data["coordinator"]
    client = data["client"]

    add_entities(
        [RadiatorPlaySlotButton(hass, entry.entry_id, coordinator, client, i) for i in range(1, SLOT_COUNT + 1)]
    )


class RadiatorPlaySlotButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, entry_id: str, coordinator: RadiatorCoordinator, client, slot_index: int) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._coordinator = coordinator
        self._client = client
        self._slot_index = slot_index

        self._attr_name = f"Radiator Play Slot {slot_index:02d}"
        self._attr_unique_id = f"{entry_id}_play_slot_{slot_index:02d}"

    @property
    def available(self) -> bool:
        return bool(self._coordinator.data and self._coordinator.data.connected)

    async def async_press(self) -> None:
        data = self._hass.data[DOMAIN][self._entry_id]
        preset = int(data["slots"].get(self._slot_index, 1))

        await self._hass.services.async_call(
            DOMAIN,
            "recall_preset",
            {"preset": preset},
            blocking=True,
        )
