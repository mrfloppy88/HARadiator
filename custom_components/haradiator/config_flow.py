"""Config flow for HARadiator."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .const import (
    CONF_EXPOSE_ADVANCED,
    CONF_LISTEN_HOST,
    CONF_LISTEN_PORT,
    CONF_SEND_PORT,
    DEFAULT_EXPOSE_ADVANCED,
    DEFAULT_LISTEN_HOST,
    DEFAULT_LISTEN_PORT,
    DEFAULT_SEND_PORT,
    DOMAIN,
)


def _entry_value(
    config_entry: config_entries.ConfigEntry,
    key: str,
    default: Any,
) -> Any:
    """Return an option value, falling back to original config entry data."""
    return config_entry.options.get(key, config_entry.data.get(key, default))


def _config_schema(
    *,
    host: str | None = None,
    send_port: int = DEFAULT_SEND_PORT,
    listen_host: str = DEFAULT_LISTEN_HOST,
    listen_port: int = DEFAULT_LISTEN_PORT,
    expose_advanced: bool = DEFAULT_EXPOSE_ADVANCED,
) -> vol.Schema:
    """Return the HARadiator config/options schema."""
    schema: dict[Any, Any] = {
        vol.Required(CONF_HOST, default=host or ""): str,
        vol.Required(CONF_SEND_PORT, default=send_port): vol.Coerce(int),
        vol.Required(CONF_LISTEN_HOST, default=listen_host): str,
        vol.Required(CONF_LISTEN_PORT, default=listen_port): vol.Coerce(int),
        vol.Required(CONF_EXPOSE_ADVANCED, default=expose_advanced): bool,
    }

    return vol.Schema(schema)


class HARadiatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HARadiator."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HARadiatorOptionsFlow:
        """Create the options flow."""
        return HARadiatorOptionsFlow(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            send_port = int(user_input[CONF_SEND_PORT])
            listen_host = user_input[CONF_LISTEN_HOST].strip()
            listen_port = int(user_input[CONF_LISTEN_PORT])
            expose_advanced = bool(user_input[CONF_EXPOSE_ADVANCED])

            if not host:
                errors[CONF_HOST] = "required"
            elif send_port < 1 or send_port > 65535:
                errors[CONF_SEND_PORT] = "invalid_port"
            elif listen_port < 1 or listen_port > 65535:
                errors[CONF_LISTEN_PORT] = "invalid_port"
            elif not listen_host:
                errors[CONF_LISTEN_HOST] = "required"
            else:
                await self.async_set_unique_id(f"{host}:{send_port}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Radiator",
                    data={
                        CONF_HOST: host,
                        CONF_SEND_PORT: send_port,
                        CONF_LISTEN_HOST: listen_host,
                        CONF_LISTEN_PORT: listen_port,
                        CONF_EXPOSE_ADVANCED: expose_advanced,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_config_schema(),
            errors=errors,
        )


class HARadiatorOptionsFlow(config_entries.OptionsFlow):
    """Handle HARadiator options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage HARadiator options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            send_port = int(user_input[CONF_SEND_PORT])
            listen_host = user_input[CONF_LISTEN_HOST].strip()
            listen_port = int(user_input[CONF_LISTEN_PORT])
            expose_advanced = bool(user_input[CONF_EXPOSE_ADVANCED])

            if not host:
                errors[CONF_HOST] = "required"
            elif send_port < 1 or send_port > 65535:
                errors[CONF_SEND_PORT] = "invalid_port"
            elif listen_port < 1 or listen_port > 65535:
                errors[CONF_LISTEN_PORT] = "invalid_port"
            elif not listen_host:
                errors[CONF_LISTEN_HOST] = "required"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_HOST: host,
                        CONF_SEND_PORT: send_port,
                        CONF_LISTEN_HOST: listen_host,
                        CONF_LISTEN_PORT: listen_port,
                        CONF_EXPOSE_ADVANCED: expose_advanced,
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_config_schema(
                host=_entry_value(self.config_entry, CONF_HOST, ""),
                send_port=int(
                    _entry_value(
                        self.config_entry,
                        CONF_SEND_PORT,
                        DEFAULT_SEND_PORT,
                    )
                ),
                listen_host=str(
                    _entry_value(
                        self.config_entry,
                        CONF_LISTEN_HOST,
                        DEFAULT_LISTEN_HOST,
                    )
                ),
                listen_port=int(
                    _entry_value(
                        self.config_entry,
                        CONF_LISTEN_PORT,
                        DEFAULT_LISTEN_PORT,
                    )
                ),
                expose_advanced=bool(
                    _entry_value(
                        self.config_entry,
                        CONF_EXPOSE_ADVANCED,
                        DEFAULT_EXPOSE_ADVANCED,
                    )
                ),
            ),
            errors=errors,
        )