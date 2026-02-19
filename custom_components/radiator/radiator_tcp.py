import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Callable

_LOGGER = logging.getLogger(__name__)


@dataclass
class RadiatorState:
    connected: bool = False
    last_ping: Optional[datetime] = None


class RadiatorClient:
    """Async TCP client for Radiator panel protocol (port 4815)."""

    def __init__(self, host: str, port: int = 4815) -> None:
        self._host = host
        self._port = port
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self.state = RadiatorState()
        self._task: Optional[asyncio.Task] = None
        self._on_update: Optional[Callable[[], None]] = None
        self._lock = asyncio.Lock()

    def set_on_update(self, cb: Callable[[], None]) -> None:
        self._on_update = cb

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._close()

    async def _close(self) -> None:
        async with self._lock:
            if self._writer:
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except Exception:
                    pass
            self._reader = None
            self._writer = None
        self.state.connected = False
        self._notify()

    def _notify(self) -> None:
        if self._on_update:
            self._on_update()

    async def _connect(self) -> None:
        _LOGGER.debug("Connecting to Radiator %s:%s", self._host, self._port)
        reader, writer = await asyncio.open_connection(self._host, self._port)
        async with self._lock:
            self._reader = reader
            self._writer = writer
        self.state.connected = True
        self._notify()
        _LOGGER.info("Connected to Radiator %s:%s", self._host, self._port)

    async def _run(self) -> None:
        backoff = 1
        while True:
            try:
                await self._connect()
                backoff = 1
                await self._read_loop()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _LOGGER.warning("Radiator connection error: %s", e)
                await self._close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    async def _read_loop(self) -> None:
        assert self._reader is not None
        while True:
            raw = await self._reader.readline()
            if not raw:
                raise ConnectionError("Socket closed")
            line = raw.decode("ascii", errors="ignore").strip()
            if line == "p":  # ping
                self.state.last_ping = datetime.now(timezone.utc)
                self._notify()

    async def send_line(self, line: str) -> None:
        async with self._lock:
            if not self._writer:
                raise ConnectionError("Not connected")
            self._writer.write(line.encode("ascii"))
            await self._writer.drain()

    async def press_button(self, button_no: int, press_ms: int = 60) -> None:
        await self.send_line(f"s {button_no} true\n")
        await asyncio.sleep(press_ms / 1000)
        await self.send_line(f"s {button_no} false\n")

    async def step_encoder(self, encoder_no: int, steps: int) -> None:
        await self.send_line(f"e {encoder_no} {steps}\n")
