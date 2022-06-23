import inspect
import logging
import os
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
        "name": "Tester",
        "set_loglevel": "🚫 <b>Please specify verbosity as an integer or string</b>",
        "no_logs": "ℹ️ <b>You don't have any logs at verbosity {}.</b>",
        "logs_filename": "premium-userbot-jurnal-turi.html",
        "logs_caption": "◽ <b>«Premium-Userbot»</b> jurnali quyidagicha.",
        "suspend_invalid_time": "🚫 <b>Invalid time to suspend</b>",
        "suspended": "🥶 <b>Bot suspended for</b> <code>{}</code> <b>seconds</b>",
        "results_ping": "◽ <b>«Javob vaqti»:</b> <code>{}</code> <b>ms</b>\n◽ <b>«Ish vaqti»: {}</b>",
        "confidential": "◽ <b>Jurnal darajasi </b><code>{}</code><b> maxfiy ma'lumotlaringizni oshkor qilishi mumkin, ehtiyot bo'ling</b>",
        "confidential_text": (
            "⚠️ <b>Log level </b><code>{0}</code><b> may reveal your confidential info, "
            "be careful</b>\n<b>Type </b><code>.logs {0} force_insecure</code><b> "
            "to ignore this warning</b>"
        ),
        "choose_loglevel": "◽ <b>Jurnal <u>darajasini</u> tanlang:</b>\n◽ Modul xatosi «2. modul» manzilida.",
        "database_unlocked": "🚫 DB eval unlocked",
        "database_locked": "✅ DB eval locked",
        "bad_module": "🚫 <b>Module not found</b>",
        "debugging_enabled": "🧑‍💻 <b>Debugging mode enabled for module </b><code>{0}</code>\n<i>Go to directory named `debug_modules`, edit file named `{0}.py` and see changes in real time</i>",
        "debugging_disabled": "✅ <b>Debugging disabled</b>",
        "heroku_debug": "🚫 <b>Debugging is not available on Heroku</b>",
    }

    strings_ru = {
        "set_loglevel": "🚫 <b>Укажи уровень логов числом или строкой</b>",
        "no_logs": "ℹ️ <b>У тебя нет логов уровня {}.</b>",
        "logs_caption": "◽ <b>«Premium-Userbot»</b> журнал выглядит следующим образом.",
        "database_unlocked": "🚫 База скомпрометирована",
        "database_locked": "✅ База защищена",
        "bad_module": "🚫 <b>Модуль не найден</b>",
        "debugging_enabled": "🧑‍💻 <b>Режим разработчика включен для модуля </b><code>{0}</code>\n<i>Отправляйся в директорию `debug_modules`, изменяй файл `{0}.py`, и смотри изменения в режиме реального времени</i>",
        "debugging_disabled": "✅ <b>Режим разработчика выключен</b>",
        "suspend_invalid_time": "🚫 <b>Неверное время заморозки</b>",
        "suspended": "🥶 <b>Бот заморожен на</b> <code>{}</code> <b>секунд</b>",
        "results_ping": "⏱ <b>Скорость отклика:</b> <code>{}</code> <b>ms</b>\n👩‍💼 <b>Прошло с последней перезагрузки: {}</b>",
        "confidential": "◽ <b>Уровень логов </b><code>{}</code><b> может содержать личную информацию, будь осторожен</b>",
        "confidential_text": "◽ <b>Уровень логов </b><code>{0}</code><b> может содержать личную информацию, будь осторожен</b>\n<b>Напиши </b><code>.logs {0} force_insecure</code><b>, чтобы отправить логи игнорируя предупреждение</b>",
        "choose_loglevel": "◽ Выберите <b>журнал <u>уровня</u>:</b> \n◽ Ошибка модуля в «2. modul».",
        "_cmd_doc_dump": "Показать информацию о сообщении",
        "_cmd_doc_logs": "<уровень> - Отправляет лог-файл. Уровни ниже WARNING могут содержать личную инфомрацию.",
        "_cmd_doc_suspend": "<время> - Заморозить бота на некоторое время",
        "_cmd_doc_ping": "Проверяет скорость отклика юзербота",
        "_cls_doc": "Операции, связанные с самотестированием",
        "heroku_debug": "🚫 <b>Режим разработчика не доступен на Heroku</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "force_send_all",
                False,
                (
                    "Forcefully send logs to all clients, aka do not split logs "
                    "to <mine> and <not-mine>. Restart required after setting"
                ),
                validator=loader.validators.Boolean(),
            )
        )

        logging.getLogger().handlers[0].force_send_all = self.config["force_send_all"]

    @loader.loop(interval=1)
    async def watchdog(self):
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

    async def logscmd(
        self,
        message: Union[Message, InlineCall],
        force: bool = False,
        lvl: Union[int, None] = None,
    ):
        """<level> - Dumps logs. Loglevels below WARNING may contain personal info."""
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
                                "text": "«1. tanqidiy»",
                                "callback": self.logscmd,
                                "args": (False, 50),
                            },
                            {
                                "text": "«2. modul»",
                                "callback": self.logscmd,
                                "args": (False, 40),
                            },
                        ],
                        [
                            {
                                "text": "«3. ogohlik»",
                                "callback": self.logscmd,
                                "args": (False, 30),
                            },
                            {
                                "text": "«4. jurnal»",
                                "callback": self.logscmd,
                                "args": (False, 20),
                            },
                        ],
                        [
                            {
                                "text": "«5. to'liq»",
                                "callback": self.logscmd,
                                "args": (False, 10),
                            },
                            {
                                "text": "«6. barcha»",
                                "callback": self.logscmd,
                                "args": (False, 0),
                            },
                        ],
                        [{"text": "— bekor qilish —", "action": "close"}],
                    ],
                    message=message,
                ):
                    raise
            except Exception:
                await utils.answer(message, self.strings("set_loglevel"))

            return

        logs = "\n\n".join(
            [
                (
                    "\n".join(
                        handler.dumps(lvl, client_id=self._client._tg_id)
                        if "client_id" in inspect.signature(handler.dumps).parameters
                        else handler.dumps(lvl)
                    )
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
                            "text": "◽ Har vaqt koʻrish",
                            "callback": self.logscmd,
                            "args": [True, lvl],
                        },
                        {"text": "◽ Bekor qilish", "action": "close"},
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
            f' <i><a href="https://github.com/hikariatama/Hikka/commit/{ghash}">({ghash[:8]})</a></i>'
            if ghash
            else "",
            utils.formatted_uptime(),
            utils.get_named_platform(),
            self.strings(
                f"database_{'un' if self._db.get(main.__name__, 'enable_db_eval', False) else ''}locked"
            ),
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

    async def pingcmd(self, message: Message):
        """Userbot pingini sinab ko'ring"""
        start = time.perf_counter_ns()
        message = await utils.answer(message, "<code>◽ premium...</code>")
        await utils.answer(
            message,
            self.strings("results_ping").format(
                round((time.perf_counter_ns() - start) / 10**6, 3),
                utils.formatted_uptime(),
            ),
        )

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

        chat, is_new = await utils.asset_channel(
            self._client,
            "premium-userbot-logs",
            "🌉 Your Premium logs will appear in this chat",
            silent=True,
            avatar="https://te.legra.ph/file/5308c45970b6e27805e09.jpg",
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
                    rank="Premium-Userbot-Logger",
                )
            )
        except Exception:
            pass

        logging.getLogger().handlers[0].install_tg_log(self)
        logger.debug(f"Bot logging installed for {self._logchat}")
