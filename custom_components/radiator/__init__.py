from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_PORT,
    CTRL_PRESET_PAGE_ENCODER,
    BTN_PRESET_1,
)
from .radiator_tcp import RadiatorClient
from .coordinator import RadiatorCoordinator

PLATFORMS = ["select", "button"]


def _preset_to_page_slot(preset: int) -> tuple[int, int]:
    page = ((preset - 1) // 10) + 1
    slot = ((preset - 1) % 10) + 1
    return page, slot


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    client = RadiatorClient(host=host, port=port)
    coordinator = RadiatorCoordinator(hass, client)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "current_page": 1,
    }

    await client.start()
    coordinator.async_set_updated_data_from_client()

    async def _handle_recall_preset(call: ServiceCall) -> None:
        preset = int(call.data["preset"])
        if preset < 1 or preset > 1000:
            raise ValueError("preset must be between 1 and 1000")

        target_page, slot = _preset_to_page_slot(preset)

        data = hass.data[DOMAIN][entry.entry_id]
        current_page = int(data.get("current_page", 1))

        delta = target_page - current_page
        if delta != 0:
            await client.step_encoder(CTRL_PRESET_PAGE_ENCODER, delta)
            data["current_page"] = target_page

        btn_no = BTN_PRESET_1 + (slot - 1)
        await client.press_button(btn_no)

    hass.services.async_register(DOMAIN, "recall_preset", _handle_recall_preset)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id)
    await data["client"].stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
