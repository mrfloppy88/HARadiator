from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .radiator_tcp import RadiatorClient

_LOGGER = logging.getLogger(__name__)


@dataclass
class RadiatorData:
    connected: bool
    last_ping: str | None


class RadiatorCoordinator(DataUpdateCoordinator[RadiatorData]):
    def __init__(self, hass: HomeAssistant, client: RadiatorClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="radiator",
            update_interval=None,
        )
        self.client = client
        self.client.set_on_update(self.async_set_updated_data_from_client)

    def async_set_updated_data_from_client(self) -> None:
        lp = self.client.state.last_ping
        self.async_set_updated_data(
            RadiatorData(
                connected=self.client.state.connected,
                last_ping=lp.isoformat() if lp else None,
            )
        )
