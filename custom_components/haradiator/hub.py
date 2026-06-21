"""OSC transport for the HARadiator Home Assistant integration."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
from typing import Any

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

_LOGGER = logging.getLogger(__name__)

StateCallback = Callable[[str, Any], None]


class RadiatorOscHub:
    """Small OSC bridge used by HARadiator entities."""

    def __init__(
        self,
        *,
        host: str,
        send_port: int,
        listen_host: str,
        listen_port: int,
        known_addresses: set[str],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Initialize the OSC hub."""
        self.host = host
        self.send_port = send_port
        self.listen_host = listen_host
        self.listen_port = listen_port
        self._loop = loop
        self._known_addresses = known_addresses
        self._client = SimpleUDPClient(host, send_port)
        self._dispatcher = Dispatcher()
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: asyncio.DatagramProtocol | None = None
        self._states: dict[str, Any] = {}
        self._callbacks: dict[str, set[StateCallback]] = {}

        # Map every known OSC endpoint explicitly.
        for address in known_addresses:
            self._dispatcher.map(address, self._handle_osc_message)

        # Also map a wildcard fallback so new Radiator OSC addresses still update.
        self._dispatcher.set_default_handler(self._handle_osc_message)

    @property
    def states(self) -> dict[str, Any]:
        """Return the current known state cache."""
        return self._states

    async def async_start(self) -> None:
        """Start the OSC receive endpoint."""
        if self._transport is not None:
            return

        server = AsyncIOOSCUDPServer(
            (self.listen_host, self.listen_port),
            self._dispatcher,
            self._loop,
        )
        self._transport, self._protocol = await server.create_serve_endpoint()
        _LOGGER.info(
            "Started Radiator OSC listener on %s:%s; sending to %s:%s",
            self.listen_host,
            self.listen_port,
            self.host,
            self.send_port,
        )

    async def async_stop(self) -> None:
        """Stop the OSC receive endpoint."""
        if self._transport is not None:
            self._transport.close()
            self._transport = None
            self._protocol = None
            _LOGGER.info("Stopped Radiator OSC listener")

    async def async_send(self, address: str, value: Any) -> None:
        """Send one OSC value to Radiator and update optimistic local state."""
        parsed = _parse_service_value(value)
        await self._loop.run_in_executor(
            None,
            self._client.send_message,
            address,
            parsed,
        )
        self._set_state(address, parsed)

    def subscribe(self, address: str, callback: StateCallback) -> Callable[[], None]:
        """Subscribe to one OSC address and return an unsubscribe callback."""
        self._callbacks.setdefault(address, set()).add(callback)

        def _unsubscribe() -> None:
            callbacks = self._callbacks.get(address)
            if callbacks is None:
                return
            callbacks.discard(callback)
            if not callbacks:
                self._callbacks.pop(address, None)

        return _unsubscribe

    def get_state(self, address: str) -> Any:
        """Return the latest known value for an OSC address."""
        return self._states.get(address)

    def _handle_osc_message(self, address: str, *args: Any) -> None:
        """Handle a received OSC message from python-osc."""
        if not args:
            value: Any = None
        elif len(args) == 1:
            value = args[0]
        else:
            value = list(args)

        self._loop.call_soon_threadsafe(self._set_state, address, value)

    def _set_state(self, address: str, value: Any) -> None:
        """Update cached state and notify subscribed entities."""
        self._states[address] = value
        for callback in tuple(self._callbacks.get(address, ())):
            try:
                callback(address, value)
            except Exception:
                _LOGGER.exception(
                    "Error notifying Radiator OSC callback for %s",
                    address,
                )


def _parse_service_value(value: Any) -> Any:
    """Convert UI service values to OSC-friendly primitive values.

    Radiator reports most numeric values as FLOAT, including on/off style
    values like blackout, so numeric service values are sent as floats.
    """
    if isinstance(value, bool):
        return 1.0 if value else 0.0

    if isinstance(value, int | float):
        return float(value)

    if isinstance(value, str):
        stripped = value.strip()
        lowered = stripped.lower()

        if lowered in {"true", "on", "yes"}:
            return 1.0

        if lowered in {"false", "off", "no"}:
            return 0.0

        try:
            return float(stripped)
        except ValueError:
            return value

    return value