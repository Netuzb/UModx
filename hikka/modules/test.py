import inspect
import logging
import os
import random
import time
from io import BytesIO
from typing import Union
from telethon.tl.functions.channels import EditAdminRequest, InviteToChannelRequest
from telethon.tl.types import ChatAdminRights, Message
from .. import loader, main, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

if "DYNO" not in os.environ:
    DEBUG_MODS_DIR = os.path.join(utils.get_base_dir(), "debug_modules")

    if not os.path.isdir(DEBUG_MODS_DIR):
        os.mkdir(DEBUG_MODS_DIR, mode=0o755)

    for mod in os.scandir(DEBUG_MODS_DIR):
        os.remove(mod.path)


@loader.tds
class TestMod(loader.Module):
    """Perform operations based on userbot self-testing"""

    _memory = {}

    strings = {
        "name": "Central",
        "set_loglevel": "🚫 <b>Please specify verbosity as an integer or string</b>",
        "no_logs": "ℹ️ <b>You don't have any logs at verbosity {}.</b>",
        "logs_filename": "hikka-logs.txt",
        "logs_caption": (
            "<emoji document_id='5188377234380954537'>🌘</emoji> <b>Hikka logs with"
            " verbosity </b><code>{}</code>\n\n<emoji"
            " document_id='5454390891466726015'>👋</emoji> <b>Hikka version:"
            " {}.{}.{}</b>{}\n<emoji document_id='6321050180095313397'>⏱</emoji>"
            " <b>Uptime: {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{}"
            " InlineLogs</b>"
        ),
        "suspend_invalid_time": (
            "<emoji document_id='5416024721705673488'>💀</emoji> <b>Invalid time to"
            " suspend</b>"
        ),
        "suspended": (
            "<emoji document_id='5452023368054216810'>🥶</emoji> <b>Bot suspended"
            " for</b> <code>{}</code> <b>seconds</b>"
        ),
        "results_ping": (
            "<emoji document_id='6321050180095313397'>⏱</emoji> <b>Telegram ping:</b>"
            " <code>{}</code> <b>ms</b>\n<emoji"
            " document_id='5377371691078916778'>😎</emoji> <b>Uptime: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id='5472146462362048818'>💡</emoji> <i>Telegram ping mostly"
            " depends on Telegram servers latency and other external factors and has"
            " nothing to do with the parameters of server on which userbot is"
            " installed</i>"
        ),
        "confidential": (
            "⚠️ <b>Log level </b><code>{}</code><b> may reveal your confidential info,"
            " be careful</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Log level </b><code>{0}</code><b> may reveal your confidential info,"
            " be careful</b>\n<b>Type </b><code>.logs {0} force_insecure</code><b> to"
            " ignore this warning</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Choose log level</b>",
        "bad_module": "🚫 <b>Module not found</b>",
        "debugging_enabled": (
            "🧑‍💻 <b>Debugging mode enabled for module </b><code>{0}</code>\n<i>Go to"
            " directory named `debug_modules`, edit file named `{0}.py` and see changes"
            " in real time</i>"
        ),
        "debugging_disabled": "✅ <b>Debugging disabled</b>",
        "heroku_debug": "🚫 <b>Debugging is not available on Heroku</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "force_send_all",
                False,
                "⚠️ Do not touch, if you don't know what it does!\nBy default, Hikka"
                " will try to determine, which client caused logs. E.g. there is a"
                " module TestModule installed on Client1 and TestModule2 on Client2. By"
                " default, Client2 will get logs from TestModule2, and Client1 will get"
                " logs from TestModule. If this option is enabled, Hikka will send all"
                " logs to Client1 and Client2, even if it is not the one that caused"
                " the log.",
                validator=loader.validators.Boolean(),
                on_change=self._pass_config_to_logger,
            ),
            loader.ConfigValue(
                "tglog_level",
                "INFO",
                "⚠️ Do not touch, if you don't know what it does!\n"
                "Minimal loglevel for records to be sent in Telegram.",
                validator=loader.validators.Choice(
                    ["INFO", "WARNING", "ERROR", "CRITICAL"]
                ),
                on_change=self._pass_config_to_logger,
            ),
        )

    def _pass_config_to_logger(self):
        logging.getLogger().handlers[0].force_send_all = self.config["force_send_all"]
        logging.getLogger().handlers[0].tg_level = self.config["tglog_level"]

    @loader.loop(interval=1)
    async def watchdog(self):
        if not os.path.isdir(DEBUG_MODS_DIR):
            return

        try:
            for module in os.scandir(DEBUG_MODS_DIR):
                last_modified = os.stat(module.path).st_mtime
                cls_ = module.path.split("/")[-1].split(".py")[0]

                if cls_ not in self._memory:
                    self._memory[cls_] = last_modified
                    continue

                if self._memory[cls_] == last_modified:
                    continue

                self._memory[cls_] = last_modified
                logger.debug(f"Reloading debug module {cls_}")
                with open(module.path, "r") as f:
                    try:
                        await next(
                            module
                            for module in self.allmodules.modules
                            if module.__class__.__name__ == "LoaderMod"
                        ).load_module(
                            f.read(),
                            None,
                            save_fs=False,
                        )
                    except Exception:
                        logger.exception("Failed to reload module in watchdog")
        except Exception:
            logger.exception("Failed debugging watchdog")
            return

    @loader.command(ru_doc="<уровень> - Показать логи")
    async def logs(
        self,
        message: Union[Message, InlineCall],
        force: bool = False,
        lvl: Union[int, None] = None,
    ):
        """<level> - Dump logs"""
        if not isinstance(lvl, int):
            args = utils.get_args_raw(message)
            try:
                try:
                    lvl = int(args.split()[0])
                except ValueError:
                    lvl = getattr(logging, args.split()[0].upper(), None)
            except IndexError:
                lvl = None

        if not isinstance(lvl, int):
            try:
                if not self.inline.init_complete or not await self.inline.form(
                    text=self.strings("choose_loglevel"),
                    reply_markup=[
                        [
                            {
                                "text": "🚨 Critical",
                                "callback": self.logs,
                                "args": (False, 50),
                            },
                            {
                                "text": "🚫 Error",
                                "callback": self.logs,
                                "args": (False, 40),
                            },
                        ],
                        [
                            {
                                "text": "⚠️ Warning",
                                "callback": self.logs,
                                "args": (False, 30),
                            },
                            {
                                "text": "ℹ️ Info",
                                "callback": self.logs,
                                "args": (False, 20),
                            },
                        ],
                        [
                            {
                                "text": "🧑‍💻 Debug",
                                "callback": self.logs,
                                "args": (False, 10),
                            },
                            {
                                "text": "👁 All",
                                "callback": self.logs,
                                "args": (False, 0),
                            },
                        ],
                        [{"text": "🚫 Cancel", "action": "close"}],
                    ],
                    message=message,
                ):
                    raise
            except Exception:
                await utils.answer(message, self.strings("set_loglevel"))

            return

        logs = "\n\n".join(
            [
                "\n".join(
                    handler.dumps(lvl, client_id=self._client.tg_id)
                    if "client_id" in inspect.signature(handler.dumps).parameters
                    else handler.dumps(lvl)
                )
                for handler in logging.getLogger().handlers
            ]
        )

        named_lvl = (
            lvl
            if lvl not in logging._levelToName
            else logging._levelToName[lvl]  # skipcq: PYL-W0212
        )

        if (
            lvl < logging.WARNING
            and not force
            and (
                not isinstance(message, Message)
                or "force_insecure" not in message.raw_text.lower()
            )
        ):
            try:
                if not self.inline.init_complete:
                    raise

                cfg = {
                    "text": self.strings("confidential").format(named_lvl),
                    "reply_markup": [
                        {
                            "text": "📤 Send anyway",
                            "callback": self.logs,
                            "args": [True, lvl],
                        },
                        {"text": "🚫 Cancel", "action": "close"},
                    ],
                }
                if isinstance(message, Message):
                    if not await self.inline.form(**cfg, message=message):
                        raise
                else:
                    await message.edit(**cfg)
            except Exception:
                await utils.answer(
                    message,
                    self.strings("confidential_text").format(named_lvl),
                )

            return

        if len(logs) <= 2:
            if isinstance(message, Message):
                await utils.answer(message, self.strings("no_logs").format(named_lvl))
            else:
                await message.edit(self.strings("no_logs").format(named_lvl))
                await message.unload()

            return

        if btoken := self._db.get("hikka.inline", "bot_token", False):
            logs = logs.replace(
                btoken,
                f'{btoken.split(":")[0]}:***************************',
            )

        if hikka_token := self._db.get("HikkaDL", "token", False):
            logs = logs.replace(
                hikka_token,
                f'{hikka_token.split("_")[0]}_********************************',
            )

        if hikka_token := self._db.get("Kirito", "token", False):
            logs = logs.replace(
                hikka_token,
                f'{hikka_token.split("_")[0]}_********************************',
            )

        if os.environ.get("DATABASE_URL"):
            logs = logs.replace(
                os.environ.get("DATABASE_URL"),
                "postgre://**************************",
            )

        if os.environ.get("REDIS_URL"):
            logs = logs.replace(
                os.environ.get("REDIS_URL"),
                "postgre://**************************",
            )

        if os.environ.get("hikka_session"):
            logs = logs.replace(
                os.environ.get("hikka_session"),
                "StringSession(**************************)",
            )

        logs = BytesIO(logs.encode("utf-16"))
        logs.name = self.strings("logs_filename")

        ghash = utils.get_git_hash()

        other = (
            *main.__version__,
            " <i><a"
            f' href="https://github.com/hikariatama/Hikka/commit/{ghash}">({ghash[:8]})</a></i>'
            if ghash
            else "",
            utils.formatted_uptime(),
            utils.get_named_platform(),
            "✅" if self._db.get(main.__name__, "no_nickname", False) else "🚫",
            "✅" if self._db.get(main.__name__, "grep", False) else "🚫",
            "✅" if self._db.get(main.__name__, "inlinelogs", False) else "🚫",
        )

        if getattr(message, "out", True):
            await message.delete()

        if isinstance(message, Message):
            await utils.answer(
                message,
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )
        else:
            await self._client.send_file(
                message.form["chat"],
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )

    @loader.command(ru_doc="Проверить скорость отклика юзербота")
    async def ping(self, message: Message):
        """Test your userbot ping"""
        start = time.perf_counter_ns()
        message = await utils.answer(message, "<code>🐻 Nofin...</code>")

        await utils.answer(
            message,
            self.strings("results_ping").format(
                round((time.perf_counter_ns() - start) / 10**6, 3),
                utils.formatted_uptime(),
            )
            + (
                ("\n\n" + self.strings("ping_hint"))
                if random.choice([0, 0, 1]) == 1
                else ""
            ),
        )

    async def client_ready(self):
        chat, is_new = await utils.asset_channel(
            self._client,
            "🔥 umodx-logs",
            "🔥 UModx ichki qatlami quyida joylashadi",
            silent=True,
            avatar="https://te.legra.ph/file/eca95f4035898ee660212.jpg",
        )

        self._logchat = int(f"-100{chat.id}")

        if "DYNO" not in os.environ:
            self.watchdog.start()

        if not is_new and any(
            participant.id == self.inline.bot_id
            for participant in (await self._client.get_participants(chat, limit=3))
        ):
            logging.getLogger().handlers[0].install_tg_log(self)
            logger.debug(f"Bot logging installed for {self._logchat}")
            return

        logger.debug("New logging chat created, init setup...")

        try:
            await self._client(InviteToChannelRequest(chat, [self.inline.bot_username]))
        except Exception:
            logger.warning("Unable to invite logger to chat")

        try:
            await self._client(
                EditAdminRequest(
                    channel=chat,
                    user_id=self.inline.bot_username,
                    admin_rights=ChatAdminRights(ban_users=True),
                    rank="Logger",
                )
            )
        except Exception:
            pass

        logging.getLogger().handlers[0].install_tg_log(self)
        logger.debug(f"Bot logging installed for {self._logchat}")
