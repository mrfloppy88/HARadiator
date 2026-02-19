from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RadiatorCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    add_entities([RadiatorStatusSelect(data["coordinator"])])


class RadiatorStatusSelect(SelectEntity):
    _attr_name = "Radiator Connection"
    _attr_options = ["connected", "disconnected"]

    def __init__(self, coordinator: RadiatorCoordinator) -> None:
        self._coordinator = coordinator

    @property
    def available(self) -> bool:
        return True

    @property
    def current_option(self) -> str:
        if self._coordinator.data and self._coordinator.data.connected:
            return "connected"
        return "disconnected"

    async def async_select_option(self, option: str) -> None:
        # read-only entity; do nothing
        return
