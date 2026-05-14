"""HARadiator OSC integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    ALL_KNOWN_ADDRESSES,
    ATTR_ADDRESS,
    ATTR_VALUE,
    CONF_EXPOSE_ADVANCED,
    CONF_LISTEN_HOST,
    CONF_LISTEN_PORT,
    CONF_PRESET_COUNT,
    CONF_SEND_PORT,
    DEFAULT_EXPOSE_ADVANCED,
    DEFAULT_LISTEN_HOST,
    DEFAULT_LISTEN_PORT,
    DEFAULT_PRESET_COUNT,
    DEFAULT_SEND_PORT,
    DOMAIN,
    PLATFORMS,
    SERVICE_SEND_MESSAGE,
)
from .hub import RadiatorOscHub

_LOGGER = logging.getLogger(__name__)

PLATFORM_MAP: dict[str, Platform] = {
    "button": Platform.BUTTON,
    "number": Platform.NUMBER,
    "sensor": Platform.SENSOR,
    "switch": Platform.SWITCH,
}

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ADDRESS): cv.string,
        vol.Required(ATTR_VALUE): vol.Any(cv.string, float, int, bool),
    }
)


RadiatorConfigEntry = ConfigEntry[RadiatorOscHub]


async def async_setup_entry(hass: HomeAssistant, entry: RadiatorConfigEntry) -> bool:
    """Set up HARadiator from a config entry."""
    host = entry.data[CONF_HOST]
    send_port = int(entry.data.get(CONF_SEND_PORT, DEFAULT_SEND_PORT))
    listen_host = entry.data.get(CONF_LISTEN_HOST, DEFAULT_LISTEN_HOST)
    listen_port = int(entry.data.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT))

    hub = RadiatorOscHub(
        host=host,
        send_port=send_port,
        listen_host=listen_host,
        listen_port=listen_port,
        known_addresses=ALL_KNOWN_ADDRESSES,
        loop=hass.loop,
    )
    await hub.async_start()

    entry.runtime_data = hub
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    async def _handle_send_message(call: ServiceCall) -> None:
        await hub.async_send(call.data[ATTR_ADDRESS], call.data[ATTR_VALUE])

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_MESSAGE,
            _handle_send_message,
            schema=SERVICE_SCHEMA,
        )

    await hass.config_entries.async_forward_entry_setups(
        entry, [PLATFORM_MAP[platform] for platform in PLATFORMS]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RadiatorConfigEntry) -> bool:
    """Unload a HARadiator config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [PLATFORM_MAP[platform] for platform in PLATFORMS]
    )
    if unload_ok:
        hub = entry.runtime_data
        await hub.async_stop()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


def should_expose_entity(entry: ConfigEntry, enabled_default: bool) -> bool:
    """Return whether an entity should be enabled by default."""
    return bool(
        enabled_default
        or entry.data.get(CONF_EXPOSE_ADVANCED, DEFAULT_EXPOSE_ADVANCED)
    )


def preset_count(entry: ConfigEntry) -> int:
    """Return configured preset button count."""
    return int(entry.data.get(CONF_PRESET_COUNT, DEFAULT_PRESET_COUNT))
