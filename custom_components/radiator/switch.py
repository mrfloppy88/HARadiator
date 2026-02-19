from __future__ import annotations

import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from . import _autoplay_loop


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    add_entities([RadiatorAutoplaySwitch(hass, entry)])


class RadiatorAutoplaySwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_name = "Radiator Autoplay"
        self._attr_unique_id = f"{entry.entry_id}_autoplay"

    @property
    def is_on(self) -> bool:
        data = self._hass.data[DOMAIN][self._entry.entry_id]
        task = data.get("autoplay_task")
        return bool(task and not task.done())

    async def async_turn_on(self, **kwargs) -> None:
        data = self._hass.data[DOMAIN][self._entry.entry_id]

        # If already running, do nothing
        task = data.get("autoplay_task")
        if task and not task.done():
            self.async_write_ha_state()
            return

        # Reset stop event and start loop
        stop_event: asyncio.Event = data["autoplay_stop"]
        stop_event.clear()

        data["autoplay_task"] = self._hass.async_create_task(_autoplay_loop(self._hass, self._entry))
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        data = self._hass.data[DOMAIN][self._entry.entry_id]
        stop_event: asyncio.Event = data["autoplay_stop"]
        stop_event.set()

        task = data.get("autoplay_task")
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        data["autoplay_task"] = None
        self.async_write_ha_state()
