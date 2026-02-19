from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_HOST, CONF_PORT, DEFAULT_PORT


class RadiatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is None:
            schema = vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                }
            )
            return self.async_show_form(step_id="user", data_schema=schema)

        await self.async_set_unique_id(user_input[CONF_HOST])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Radiator ({user_input[CONF_HOST]})", data=user_input
        )
