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


async def _step_encoder_chunked(
    client: RadiatorClient,
    encoder_no: int,
    steps: int,
    *,
    chunk_size: int = 10,
    delay_s: float = 0.03,
) -> None:
    """
    Step an encoder in small chunks with a short delay.
    This is more reliable than sending one huge step value.
    """
    if steps == 0:
        return

    direction = 1 if steps > 0 else -1
    remaining = abs(steps)

    while remaining > 0:
        chunk = min(chunk_size, remaining) * direction
        await client.step_encoder(encoder_no, chunk)
        remaining -= abs(chunk)
        await asyncio.sleep(delay_s)


async def _recall_preset_robust(client: RadiatorClient, preset: int) -> None:
    """Recall a global preset number using 'rewind to page 1 then forward' with chunking."""
    if preset < PRESET_MIN or preset > PRESET_MAX:
        raise ValueError(f"preset must be between {PRESET_MIN} and {PRESET_MAX}")

    target_page, slot = _preset_to_page_slot(preset)

    _LOGGER.debug("Recall preset=%s => page=%s slot=%s", preset, target_page, slot)

    # Rewind hard so we latch at page 1 (confirmed by you).
    # Do it in chunks so Radiator has time to process.
    await _step_encoder_chunked(client, CTRL_PRESET_PAGE_ENCODER, -200, chunk_size=10, delay_s=0.03)

    # Small settle time before moving forward
    await asyncio.sleep(0.05)

    # Step forward to the desired page (page 1 => 0 steps forward)
    await _step_encoder_chunked(
        client,
        CTRL_PRESET_PAGE_ENCODER,
        target_page - 1,
        chunk_size=10,
        delay_s=0.03,
    )

    # Give Radiator a moment to apply the page change before button press
    await asyncio.sleep(0.05)

    # Press preset button (20..29 = preset 1..10)
    btn_no = BTN_PRESET_1 + (slot - 1)
    await client.press_button(btn_no)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    client = RadiatorClient(host=host, port=port)
    coordinator = RadiatorCoordinator(hass, client)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
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

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
    finally:
        _LOGGER.info("Radiator autoplay stopped")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id)

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
