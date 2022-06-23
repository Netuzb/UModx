"""Main logging part"""

import asyncio
import inspect
import logging
import io
from typing import Optional
from logging.handlers import RotatingFileHandler

from . import utils
from ._types import Module

_main_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="%",
)
_tg_formatter = logging.Formatter(
    fmt="[%(levelname)s] %(name)s: %(message)s\n",
    datefmt=None,
    style="%",
)

rotating_handler = RotatingFileHandler(
    filename="hikka.log",
    mode="a",
    maxBytes=10 * 1024 * 1024,
    backupCount=1,
    encoding="utf-8",
    delay=0,
)

rotating_handler.setFormatter(_main_formatter)


class TelegramLogsHandler(logging.Handler):
    """
    Keeps 2 buffers.
    One for dispatched messages.
    One for unused messages.
    When the length of the 2 together is 100
    truncate to make them 100 together,
    first trimming handled then unused.
    """

    def __init__(self, targets: list, capacity: int):
        super().__init__(0)
        self.targets = targets
        self.capacity = capacity
        self.buffer = []
        self.handledbuffer = []
        self.lvl = logging.NOTSET  # Default loglevel
        self._queue = []
        self.tg_buff = []
        self._mods = {}
        self.force_send_all = False

    def install_tg_log(self, mod: Module):
        if getattr(self, "_task", False):
            self._task.cancel()

        self._mods[mod._tg_id] = mod

        self._task = asyncio.ensure_future(self.queue_poller())

    async def queue_poller(self):
        while True:
            await self.sender()
            await asyncio.sleep(3)

    def setLevel(self, level: int):
        self.lvl = level

    def dump(self):
        """Return a list of logging entries"""
        return self.handledbuffer + self.buffer

    def dumps(self, lvl: Optional[int] = 0, client_id: Optional[int] = None) -> list:
        """Return all entries of minimum level as list of strings"""
        return [
            self.targets[0].format(record)
            for record in (self.buffer + self.handledbuffer)
            if record.levelno >= lvl
            and (not record.hikka_caller or client_id == record.hikka_caller)
        ]

    async def sender(self):
        self._queue = {
            client_id: utils.chunks(
                utils.escape_html(
                    "".join(
                        [
                            item[0]
                            for item in self.tg_buff
                            if not item[1]
                            or item[1] == client_id
                            or self.force_send_all
                        ]
                    )
                ),
                4096,
            )
            for client_id in self._mods
        }

        self.tg_buff = []

        for client_id in self._mods:
            if client_id not in self._queue:
                continue

            if len(self._queue[client_id]) > 5:
                file = io.BytesIO("".join(self._queue[client_id]).encode("utf-8"))
                file.name = "hikka-logs.txt"
                file.seek(0)
                await self._mods[client_id].inline.bot.send_document(
                    self._mods[client_id]._logchat,
                    file,
                    parse_mode="HTML",
                    caption="<b>🧳 Journals are too big to be sent as separate messages</b>",
                )

                self._queue[client_id] = []
                continue

            while self._queue[client_id]:
                chunk = self._queue[client_id].pop(0)

                if not chunk:
                    continue

                asyncio.ensure_future(
                    self._mods[client_id].inline.bot.send_message(
                        self._mods[client_id]._logchat,
                        f"<code>{chunk}</code>",
                        parse_mode="HTML",
                        disable_notification=True,
                    )
                )

    def emit(self, record: logging.LogRecord):
        try:
            caller = next(
                (
                    frame_info.frame.f_locals["_hikka_client_id_logging_tag"]
                    for frame_info in inspect.stack()
                    if isinstance(
                        getattr(getattr(frame_info, "frame", None), "f_locals", {}).get(
                            "_hikka_client_id_logging_tag"
                        ),
                        int,
                    )
                ),
                False,
            )

            assert isinstance(caller, int)
        except Exception:
            caller = None

        record.hikka_caller = caller

        if record.levelno >= 20:
            self.tg_buff += [
                (
                    ("🚫 " if record.exc_info else "") + _tg_formatter.format(record),
                    caller,
                )
            ]

        if len(self.buffer) + len(self.handledbuffer) >= self.capacity:
            if self.handledbuffer:
                del self.handledbuffer[0]
            else:
                del self.buffer[0]

        self.buffer.append(record)

        if record.levelno >= self.lvl >= 0:
            self.acquire()
            try:
                for precord in self.buffer:
                    for target in self.targets:
                        if record.levelno >= target.level:
                            target.handle(precord)

                self.handledbuffer = (
                    self.handledbuffer[-(self.capacity - len(self.buffer)) :]
                    + self.buffer
                )
                self.buffer = []
            finally:
                self.release()


def init():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(_main_formatter)
    logging.getLogger().handlers = []
    logging.getLogger().addHandler(
        TelegramLogsHandler((handler, rotating_handler), 7000)
    )
    logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.captureWarnings(True)
