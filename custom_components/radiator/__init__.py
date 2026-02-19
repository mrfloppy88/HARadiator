from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_PORT,
    CTRL_PRESET_PAGE_ENCODER,
    BTN_PRESET_1,
    SLOT_COUNT,
    PRESET_MIN,
    PRESET_MAX,
    DEFAULT_INTERVAL_SECONDS,
)
from .radiator_tcp import RadiatorClient
from .coordinator import RadiatorCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["select", "button", "number", "switch"]


def _preset_to_page_slot(preset: int) -> tuple[int, int]:
    """Convert global preset (1..1000) to (page, slot 1..10)."""
    page = ((preset - 1) // 10) + 1
    slot = ((preset - 1) % 10) + 1
    return page, slot


async def _recall_preset_robust(client: RadiatorClient, preset: int) -> None:
    """Recall a global preset number using 'rewind to page 1 then forward'."""
    if preset < PRESET_MIN or preset > PRESET_MAX:
        raise ValueError(f"preset must be between {PRESET_MIN} and {PRESET_MAX}")

    target_page, slot = _preset_to_page_slot(preset)

    # Radiator latches at page 1 when stepping below it:
    # rewind hard, then step forward to desired page.
    await client.step_encoder(CTRL_PRESET_PAGE_ENCODER, -200)
    await client.step_encoder(CTRL_PRESET_PAGE_ENCODER, target_page - 1)

    btn_no = BTN_PRESET_1 + (slot - 1)
    await client.press_button(btn_no)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    client = RadiatorClient(host=host, port=port)
    coordinator = RadiatorCoordinator(hass, client)

    # Per-entry runtime state
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        # Slot preset values (1..1000). Default = 1..20
        "slots": {i: i for i in range(1, SLOT_COUNT + 1)},
        "interval": DEFAULT_INTERVAL_SECONDS,
        "autoplay_task": None,
        "autoplay_stop": asyncio.Event(),
    }

    await client.start()
    coordinator.async_set_updated_data_from_client()

    async def _handle_recall_preset(call: ServiceCall) -> None:
        preset = int(call.data["preset"])
        await _recall_preset_robust(client, preset)

    hass.services.async_register(DOMAIN, "recall_preset", _handle_recall_preset)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _autoplay_loop(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Background loop that cycles through the 20 slots."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: RadiatorClient = data["client"]
    stop_event: asyncio.Event = data["autoplay_stop"]

    idx = 1
    _LOGGER.info("Radiator autoplay started")

    try:
        while not stop_event.is_set():
            interval = int(data.get("interval", DEFAULT_INTERVAL_SECONDS))
            slots: dict[int, int] = data["slots"]

            preset = int(slots.get(idx, 1))
            await _recall_preset_robust(client, preset)

            idx += 1
            if idx > SLOT_COUNT:
                idx = 1

            # Wait interval or stop early
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
    finally:
        _LOGGER.info("Radiator autoplay stopped")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id)

    # Stop autoplay if running
    stop_event: asyncio.Event = data["autoplay_stop"]
    stop_event.set()

    task = data.get("autoplay_task")
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await data["client"].stop()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
