"""Config flow for HARadiator."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
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
)


class RadiatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a HARadiator config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_SEND_PORT]}"
            )
            self._abort_if_unique_id_configured()

            title = user_input.get(CONF_NAME) or "Radiator"
            data = dict(user_input)
            data.pop(CONF_NAME, None)
            return self.async_create_entry(title=title, data=data)

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default="Radiator"): str,
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_SEND_PORT, default=DEFAULT_SEND_PORT): int,
                vol.Optional(CONF_LISTEN_HOST, default=DEFAULT_LISTEN_HOST): str,
                vol.Optional(CONF_LISTEN_PORT, default=DEFAULT_LISTEN_PORT): int,
                vol.Optional(CONF_PRESET_COUNT, default=DEFAULT_PRESET_COUNT): int,
                vol.Optional(
                    CONF_EXPOSE_ADVANCED, default=DEFAULT_EXPOSE_ADVANCED
                ): bool,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
