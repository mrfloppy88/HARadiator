from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SLOT_COUNT,
    PRESET_MIN,
    PRESET_MAX,
    DEFAULT_INTERVAL_SECONDS,
    INTERVAL_MIN_SECONDS,
    INTERVAL_MAX_SECONDS,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    add = []

    # 20 preset slot numbers
    for i in range(1, SLOT_COUNT + 1):
        add.append(RadiatorSlotPresetNumber(hass, entry.entry_id, i))

    # interval number
    add.append(RadiatorIntervalNumber(hass, entry.entry_id))

    add_entities(add)


class RadiatorSlotPresetNumber(NumberEntity):
    _attr_native_min_value = PRESET_MIN
    _attr_native_max_value = PRESET_MAX
    _attr_native_step = 1
    _attr_mode = "box"

    def __init__(self, hass: HomeAssistant, entry_id: str, slot_index: int) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._slot_index = slot_index

        self._attr_name = f"Radiator Slot {slot_index:02d} Preset"
        self._attr_unique_id = f"{entry_id}_slot_{slot_index:02d}_preset"

    @property
    def native_value(self) -> float | None:
        data = self._hass.data[DOMAIN][self._entry_id]
        return float(int(data["slots"].get(self._slot_index, self._slot_index)))

    async def async_set_native_value(self, value: float) -> None:
        data = self._hass.data[DOMAIN][self._entry_id]
        data["slots"][self._slot_index] = int(value)
        self.async_write_ha_state()


class RadiatorIntervalNumber(NumberEntity):
    _attr_native_min_value = INTERVAL_MIN_SECONDS
    _attr_native_max_value = INTERVAL_MAX_SECONDS
    _attr_native_step = 1
    _attr_mode = "box"

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._entry_id = entry_id

        self._attr_name = "Radiator Autoplay Interval"
        self._attr_unique_id = f"{entry_id}_autoplay_interval"

    @property
    def native_value(self) -> float | None:
        data = self._hass.data[DOMAIN][self._entry_id]
        return float(int(data.get("interval", DEFAULT_INTERVAL_SECONDS)))

    async def async_set_native_value(self, value: float) -> None:
        data = self._hass.data[DOMAIN][self._entry_id]
        data["interval"] = int(value)
        self.async_write_ha_state()
