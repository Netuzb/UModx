"""Loads and registers modules"""

import asyncio
import contextlib
import functools
import importlib
import inspect
import logging
import os
import re
import ast
import sys
import time
import uuid
from collections import ChainMap
from importlib.machinery import ModuleSpec
from typing import Optional, Union
from urllib.parse import urlparse
import requests
import telethon
from telethon.tl.types import Message, Channel
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.contacts import SearchRequest
from .. import loader, main, utils
from ..compat import geek
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

VALID_PIP_PACKAGES = re.compile(
    r"^\s*# ?requires:(?: ?)((?:{url} )*(?:{url}))\s*$".format(
        url=r"[-[\]_.~:/?#@!$&'()*+,;%<=>a-zA-Z0-9]+"
    ),
    re.MULTILINE,
)

USER_INSTALL = "PIP_TARGET" not in os.environ and "VIRTUAL_ENV" not in os.environ


@loader.tds
class LoaderMod(loader.Module):
    """Loads modules"""

    strings = {
        "name": "Loader",
        "repo_config_doc": "Fully qualified URL to a module repo",
        "avail_header": "<b>◽ Official modules from repo</b>",
        "no_module": "<b>◽ Module not available in repo.</b>",
        "no_file": "<b>◽ File not found</b>",
        "provide_module": "<b>◽ Provide a module to load</b>",
        "bad_unicode": "<b>◽ Invalid Unicode formatting in module</b>",
        "load_failed": "<b>◽ Loading failed. See logs for details</b>",
        "loaded": "<b>◽ Module </b><b>{}</b>{}<b> loaded {}</b>{}{}{}{}{}",
        "no_class": "<b>What class needs to be unloaded?</b>",
        "unloaded": "<b>◽ Module {} unloaded.</b>",
        "not_unloaded": "<b>◽ Module not unloaded.</b>",
        "requirements_failed": "<b>◽ Requirements installation failed</b>",
        "requirements_installing": "<b>◽ Installing requirements:\n\n{}</b>",
        "requirements_restart": "<b>◽ Requirements installed, but a restart is required for </b><b>{}</b><b> to apply</b>",
        "all_modules_deleted": "<b>◽ All modules deleted</b>",
        "single_cmd": "\n◽ <b>{}{}</b> {}",
        "undoc_cmd": "◽ No docs",
        "ihandler": "\n◽ <b>{}</b> {}",
        "undoc_ihandler": "◽ No docs",
        "inline_init_failed": (
            "◽ <b>This module requires Hikka inline feature and "
            "initialization of InlineManager failed</b>\n"
            "<i>Please, remove one of your old bots from @BotFather and "
            "restart userbot to load this module</i>"
        ),
        "version_incompatible": "◽ <b>This module requires Hikka {}+\nPlease, update with </b><b>.update</b>",
        "ffmpeg_required": "◽ <b>This module requires FFMPEG, which is not installed</b>",
        "developer": "\n\n◽ <b>Developer: </b>{}",
        "module_fs": "◽ <b>Ushbu modulni fayl tizimiga saqlashni xohlaysizmi?</b>\n ◽ <i>(<b>Restart</b> berilganidan soʻng saqlanib qoladi)</i>",
        "save": "◽ Ha // Saqlash",
        "no_save": "◽ Yoʻq // Bekor",
        "save_for_all": "◽ Har doim // Barchasini saqlash",
        "never_save": "◽ Hech qachon // Saqlash kerakmas",
        "will_save_fs": "◽ Now all modules, loaded with .loadmod will be saved to filesystem",
        "add_repo_config_doc": "Additional repos to load from",
        "share_link_doc": "Share module link in result message of .dlmod",
        "modlink": "\n\n◽ <b>Link: </b><b>{}</b>",
        "blob_link": "◽ <b>Do not use `blob` links to download modules. Consider switching to `raw` instead</b>",
        "suggest_subscribe": "\n\n◽ <b>This module is made by {}. Do you want to join this channel to support developer?</b>",
        "subscribe": "◽ Subscribe",
        "no_subscribe": "◽ Don't subscribe",
        "subscribed": "◽ Subscribed",
        "not_subscribed": "◽ I will no longer suggest subscribing to this channel",
        "confirm_clearmodules": "◽ <b>Barcha modullarni <u>tozalashni</u> ishonch hosil qiling hamda tasdiqlang!</b>",
        "clearmodules": "◽ Ha // Tasdiqlash",
        "cancel": "◽ Yo'q // Bekor qilish",
    }

    strings_ru = {
        "repo_config_doc": "Ссылка для загрузки модулей",
        "add_repo_config_doc": "Дополнительные репозитории",
        "avail_header": "<b>◽ Официальные модули из репозитория</b>",
        "no_module": "<b>◽ Модуль недоступен в репозитории.</b>",
        "no_file": "<b>◽ Файл не найден</b>",
        "provide_module": "<b>◽ Укажи модуль для загрузки</b>",
        "bad_unicode": "<b>◽ Неверная кодировка модуля</b>",
        "load_failed": "<b>◽ Загрузка не увенчалась успехом. Смотри логи.</b>",
        "loaded": "<b>◽ Модуль </b><b>{}</b>{}<b> загружен {}</b>{}{}{}{}{}",
        "no_class": "<b>А что выгружать то?</b>",
        "unloaded": "<b>◽ Модуль {} выгружен.</b>",
        "not_unloaded": "<b>◽ Модуль не выгружен.</b>",
        "requirements_failed": "<b>◽ Ошибка установки зависимостей</b>",
        "requirements_installing": "<b>◽ Устанавливаю зависимости:\n\n{}</b>",
        "requirements_restart": "<b>◽ Зависимости установлены, но нужна перезагрузка для применения </b><b>{}</b>",
        "all_modules_deleted": "<b>◽ Модули удалены</b>",
        "single_cmd": "\n◽ <b>{}{}</b> {}",
        "undoc_cmd": "◽ Нет описания",
        "ihandler": "\n◽ <b>{}</b> {}",
        "undoc_ihandler": "◽ Нет описания",
        "version_incompatible": "◽ <b>Этому модулю требуется Hikka версии {}+\nОбновись с помощью </b><b>.update</b>",
        "ffmpeg_required": "◽ <b>Этому модулю требуется FFMPEG, который не установлен</b>",
        "developer": "\n\n◽ <b>Разработчик: </b>{}",
        "module_fs": "◽ <b>Ты хочешь сохранить модуль на жесткий диск, чтобы он не выгружался при перезагрузке?</b>",
        "save": "◽ Сохранить",
        "no_save": "◽ Не сохранять",
        "save_for_all": "◽ Всегда сохранять",
        "never_save": "◽ Никогда не сохранять",
        "will_save_fs": "◽ Теперь все модули, загруженные из файла, будут сохраняться на жесткий диск",
        "inline_init_failed": "◽ <b>Этому модулю нужен HikkaInline, а инициализация менеджера инлайна неудачна</b>\n<i>Попробуй удалить одного из старых ботов в @BotFather и перезагрузить юзербота</i>",
        "_cmd_doc_dlmod": "Скачивает и устаналвивает модуль из репозитория",
        "_cmd_doc_dlpreset": "Скачивает и устанавливает определенный набор модулей",
        "_cmd_doc_loadmod": "Скачивает и устанавливает модуль из файла",
        "_cmd_doc_unloadmod": "Выгружает (удаляет) модуль",
        "_cmd_doc_clearmodules": "Выгружает все установленные модули",
        "_cls_doc": "Загружает модули",
        "share_link_doc": "Указывать ссылку на модуль после загрузки через .dlmod",
        "modlink": "\n\n◽ <b>Ссылка: </b><b>{}</b>",
        "blob_link": "◽ <b>Не используй `blob` ссылки для загрузки модулей. Лучше загружать из `raw`</b>",
        "raw_link": "\n◽ <b>Ссылка: </b><b>{}</b>",
        "suggest_subscribe": "\n\n◽ <b>Этот модуль сделан {}. Подписаться на него, чтобы поддержать разработчика?</b>",
        "subscribe": "◽ Подписаться",
        "no_subscribe": "◽ Не подписываться",
        "subscribed": "◽ Подписался!",
        "unsubscribed": "◽ Я больше не буду предлагать подписаться на этот канал",
        "confirm_clearmodules": "◽ <b>Вы уверены, что хотите выгрузить все модули?</b>",
        "clearmodules": "◽ Выгрузить модули",
        "cancel": "◽ Отмена",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "MODULES_REPO",
                "https://raw.githubusercontent.com/Netuzb/FTG-Modules/main/",
                lambda: self.strings("repo_config_doc"),
                validator=loader.validators.Link(),
            ),
            loader.ConfigValue(
                "ADDITIONAL_REPOS",
                # Currenly the trusted developers are specified
                [
                    "https://raw.githubusercontent.com/Netuzb/FTG-Modules/main/",
                ],
                lambda: self.strings("add_repo_config_doc"),
                validator=loader.validators.Series(validator=loader.validators.Link()),
            ),
            loader.ConfigValue(
                "share_link",
                doc=lambda: self.strings("share_link_doc"),
                validator=loader.validators.Boolean(),
            ),
        )

    def _update_modules_in_db(self):
        self.set(
            "loaded_modules",
            {
                module.__class__.__name__: module.__origin__
                for module in self.allmodules.modules
                if module.__origin__.startswith("http")
            },
        )

    @loader.owner
    async def dlmodcmd(self, message: Message):
        """Rasmiy modul repo-dan modulni yuklab oladi va o'rnatadi"""
        if args := utils.get_args(message):
            args = args[0]

            await self.download_and_install(args, message)
            if self._fully_loaded:
                self._update_modules_in_db()
        else:
            await self.inline.list(
                message,
                [
                    self.strings("avail_header")
                    + f"\n◽️ {repo.strip('/')}\n\n"
                    + "\n".join(
                        [
                            " | ".join(chunk)
                            for chunk in utils.chunks(
                                [
                                    f"<b>{i}</b>"
                                    for i in sorted(
                                        [
                                            utils.escape_html(
                                                i.split("/")[-1].split(".")[0]
                                            )
                                            for i in mods.values()
                                        ]
                                    )
                                ],
                                5,
                            )
                        ]
                    )
                    for repo, mods in (await self.get_repo_list("full")).items()
                ],
            )

    async def _get_repo(self, repo: str, preset: str) -> str:
        repo = repo.strip("/")
        preset_id = f"{repo}/{preset}"

        if self._links_cache.get(preset_id, {}).get("exp", 0) >= time.time():
            return self._links_cache[preset_id]["data"]

        res = await utils.run_sync(
            requests.get,
            f"{repo}/{preset}.txt",
        )

        if not str(res.status_code).startswith("2"):
            logger.debug(f"Can't load {repo=}, {preset=}, {res.status_code=}")
            return []

        self._links_cache[preset_id] = {
            "exp": time.time() + 5 * 60,
            "data": [link for link in res.text.strip().splitlines() if link],
        }

        return self._links_cache[preset_id]["data"]

    async def get_repo_list(
        self,
        preset: Optional[str] = None,
        only_primary: Optional[bool] = False,
    ) -> dict:
        if preset is None or preset == "none":
            preset = "minimal"

        return {
            repo: {
                f"Mod/{repo_id}/{i}": f'{repo.strip("/")}/{link}.py'
                for i, link in enumerate(set(await self._get_repo(repo, preset)))
            }
            for repo_id, repo in enumerate(
                [self.config["MODULES_REPO"]]
                + ([] if only_primary else self.config["ADDITIONAL_REPOS"])
            )
            if repo.startswith("http")
        }

    async def get_links_list(self):
        def converter(repo_dict: dict) -> list:
            return list(dict(ChainMap(*list(repo_dict.values()))).values())

        links = await self.get_repo_list("full")
        # Make `MODULES_REPO` primary one
        main_repo = list(links[self.config["MODULES_REPO"]].values())
        del links[self.config["MODULES_REPO"]]
        return main_repo + converter(links)

    async def _find_link(self, module_name: str) -> Union[str, bool]:
        links = await self.get_links_list()
        return next(
            (
                link
                for link in links
                if link.lower().endswith(f"/{module_name.lower()}.py")
            ),
            False,
        )

    async def download_and_install(
        self,
        module_name: str,
        message: Optional[Message] = None,
    ):
        try:
            blob_link = False
            module_name = module_name.strip()
            if urlparse(module_name).netloc:
                url = module_name
                if re.match(
                    r"^(https:\/\/github\.com\/.*?\/.*?\/blob\/.*\.py)|"
                    r"(https:\/\/gitlab\.com\/.*?\/.*?\/-\/blob\/.*\.py)$",
                    url,
                ):
                    url = url.replace("/blob/", "/raw/")
                    blob_link = True
            else:
                url = await self._find_link(module_name)

                if not url:
                    if message is not None:
                        await utils.answer(message, self.strings("no_module"))

                    return False

            r = await utils.run_sync(requests.get, url)

            if r.status_code == 404:
                if message is not None:
                    await utils.answer(message, self.strings("no_module"))

                return False

            r.raise_for_status()

            return await self.load_module(
                r.content.decode("utf-8"),
                message,
                module_name,
                url,
                blob_link=blob_link,
            )
        except Exception:
            logger.exception(f"Failed to load {module_name}")

    async def _inline__load(
        self,
        call: InlineCall,
        doc: str,
        path_: Union[str, None],
        mode: str,
    ):
        save = False
        if mode == "all_yes":
            self._db.set(main.__name__, "permanent_modules_fs", True)
            self._db.set(main.__name__, "disable_modules_fs", False)
            await call.answer(self.strings("will_save_fs"))
            save = True
        elif mode == "all_no":
            self._db.set(main.__name__, "disable_modules_fs", True)
            self._db.set(main.__name__, "permanent_modules_fs", False)
        elif mode == "once":
            save = True

        await self.load_module(doc, call, origin=path_ or "<string>", save_fs=save)

    @loader.owner
    async def loadmodcmd(self, message: Message):
        """Modul faylini yuklaydi"""
        msg = message if message.file else (await message.get_reply_message())

        if msg is None or msg.media is None:
            if args := utils.get_args(message):
                try:
                    path_ = args[0]
                    with open(path_, "rb") as f:
                        doc = f.read()
                except FileNotFoundError:
                    await utils.answer(message, self.strings("no_file"))
                    return
            else:
                await utils.answer(message, self.strings("provide_module"))
                return
        else:
            path_ = None
            doc = await msg.download_media(bytes)

        logger.debug("Loading external module...")

        try:
            doc = doc.decode("utf-8")
        except UnicodeDecodeError:
            await utils.answer(message, self.strings("bad_unicode"))
            return

        if (
            not self._db.get(
                main.__name__,
                "disable_modules_fs",
                False,
            )
            and not self._db.get(main.__name__, "permanent_modules_fs", False)
            and "DYNO" not in os.environ
        ):
            if message.file:
                await message.edit("")
                message = await message.respond("◽")

            if await self.inline.form(
                self.strings("module_fs"),
                message=message,
                reply_markup=[
                    [
                        {
                            "text": self.strings("save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "once"),
                        },
                        {
                            "text": self.strings("no_save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "no"),
                        },
                    ],
                    [
                        {
                            "text": self.strings("save_for_all"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "all_yes"),
                        }
                    ],
                    [
                        {
                            "text": self.strings("never_save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "all_no"),
                        }
                    ],
                ],
            ):
                return

        if path_ is not None:
            await self.load_module(
                doc,
                message,
                origin=path_,
                save_fs=self._db.get(main.__name__, "permanent_modules_fs", False)
                and not self._db.get(main.__name__, "disable_modules_fs", False),
            )
        else:
            await self.load_module(
                doc,
                message,
                save_fs=self._db.get(main.__name__, "permanent_modules_fs", False)
                and not self._db.get(main.__name__, "disable_modules_fs", False),
            )

    async def load_module(
        self,
        doc: str,
        message: Message,
        name: Optional[Union[str, None]] = None,
        origin: Optional[str] = "<string>",
        did_requirements: Optional[bool] = False,
        save_fs: Optional[bool] = False,
        blob_link: Optional[bool] = False,
    ):
        if any(
            line.replace(" ", "") == "#scope:ffmpeg" for line in doc.splitlines()
        ) and os.system("ffmpeg -version 1>/dev/null 2>/dev/null"):
            if isinstance(message, Message):
                await utils.answer(message, self.strings("ffmpeg_required"))
            return

        if (
            any(line.replace(" ", "") == "#scope:inline" for line in doc.splitlines())
            and not self.inline.init_complete
        ):
            if isinstance(message, Message):
                await utils.answer(message, self.strings("inline_init_failed"))
            return

        if re.search(r"# ?scope: ?hikka_min", doc):
            ver = re.search(r"# ?scope: ?hikka_min ((\d+\.){2}\d+)", doc).group(1)
            ver_ = tuple(map(int, ver.split(".")))
            if main.__version__ < ver_:
                if isinstance(message, Message):
                    if getattr(message, "file", None):
                        m = utils.get_chat_id(message)
                        await message.edit("")
                    else:
                        m = message

                    await self.inline.form(
                        self.strings("version_incompatible").format(ver),
                        m,
                        reply_markup=[
                            {
                                "text": self.lookup("updater").strings("btn_update"),
                                "callback": self.lookup("updater").inline_update,
                            },
                            {
                                "text": self.lookup("updater").strings("cancel"),
                                "action": "close",
                            },
                        ],
                    )
                return

        developer = re.search(r"# ?meta developer: ?(.+)", doc)
        developer = developer.group(1) if developer else False

        blob_link = self.strings("blob_link") if blob_link else ""

        if name is None:
            try:
                node = ast.parse(doc)
                uid = next(n.name for n in node.body if isinstance(n, ast.ClassDef))
            except Exception:
                logger.debug(
                    "Can't parse classname from code, using legacy uid instead",
                    exc_info=True,
                )
                uid = "__extmod_" + str(uuid.uuid4())
        else:
            if name.startswith(self.config["MODULES_REPO"]):
                name = name.split("/")[-1].split(".py")[0]

            uid = name.replace("%", "%%").replace(".", "%d")

        module_name = f"hikka.modules.{uid}"

        doc = geek.compat(doc)

        try:
            try:
                spec = ModuleSpec(
                    module_name,
                    loader.StringLoader(doc, origin),
                    origin=origin,
                )
                instance = self.allmodules.register_module(
                    spec,
                    module_name,
                    origin,
                    save_fs=save_fs,
                )
            except ImportError as e:
                logger.info(
                    "Module loading failed, attemping dependency installation",
                    exc_info=True,
                )
                # Let's try to reinstall dependencies
                try:
                    requirements = list(
                        filter(
                            lambda x: not x.startswith(("-", "_", ".")),
                            map(
                                str.strip,
                                VALID_PIP_PACKAGES.search(doc)[1].split(),
                            ),
                        )
                    )
                except TypeError:
                    logger.warning(
                        "No valid pip packages specified in code, attemping installation from error"
                    )
                    requirements = [e.name]

                logger.debug(f"Installing requirements: {requirements}")

                if not requirements:
                    raise Exception("Nothing to install") from e

                if did_requirements:
                    if message is not None:
                        await utils.answer(
                            message,
                            self.strings("requirements_restart").format(e.name),
                        )

                    return

                if message is not None:
                    await utils.answer(
                        message,
                        self.strings("requirements_installing").format(
                            "\n".join(f"▫️ {req}" for req in requirements)
                        ),
                    )

                pip = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "-q",
                    "--disable-pip-version-check",
                    "--no-warn-script-location",
                    *["--user"] if USER_INSTALL else [],
                    *requirements,
                )

                rc = await pip.wait()

                if rc != 0:
                    if message is not None:
                        await utils.answer(
                            message,
                            self.strings("requirements_failed"),
                        )

                    return

                importlib.invalidate_caches()

                kwargs = utils.get_kwargs()
                kwargs["did_requirements"] = True

                return await self.load_module(**kwargs)  # Try again
            except loader.LoadError as e:
                with contextlib.suppress(ValueError):
                    self.allmodules.modules.remove(instance)  # skipcq: PYL-E0601

                if message:
                    await utils.answer(message, f"◽ <b>{utils.escape_html(str(e))}</b>")
                return
        except BaseException as e:
            logger.exception(f"Loading external module failed due to {e}")

            if message is not None:
                await utils.answer(message, self.strings("load_failed"))

            return

        instance.inline = self.inline

        if hasattr(instance, "__version__") and isinstance(instance.__version__, tuple):
            version = f"<b><i> (v{'.'.join(list(map(str, list(instance.__version__))))})</i></b>"
        else:
            version = ""

        try:
            try:
                self.allmodules.send_config_one(instance, self._db, self.translator)
                await self.allmodules.send_ready_one(
                    instance,
                    self._client,
                    self._db,
                    self.allclients,
                    no_self_unload=True,
                    from_dlmod=bool(message),
                )
            except loader.LoadError as e:
                with contextlib.suppress(ValueError):
                    self.allmodules.modules.remove(instance)

                if message:
                    await utils.answer(message, f"◽ <b>{utils.escape_html(str(e))}</b>")
                return
            except loader.SelfUnload as e:
                logging.debug(f"Unloading {instance}, because it raised `SelfUnload`")
                with contextlib.suppress(ValueError):
                    self.allmodules.modules.remove(instance)

                if message:
                    await utils.answer(message, f"◽ <b>{utils.escape_html(str(e))}</b>")
                return
        except Exception as e:
            logger.exception(f"Module threw because {e}")

            if message is not None:
                await utils.answer(message, self.strings("load_failed"))

            return

        for alias, cmd in self.lookup("settings").get("aliases", {}).items():
            if cmd in instance.commands:
                self.allmodules.add_alias(alias, cmd)

        if message is None:
            return

        try:
            modname = instance.strings("name")
        except KeyError:
            modname = getattr(instance, "name", "ERROR")

        modhelp = ""

        if instance.__doc__:
            modhelp += f"<b>\n◽ Info</b>: {utils.escape_html(inspect.getdoc(instance))}\n"

        subscribe = ""
        subscribe_markup = None

        def loaded_msg(use_subscribe: bool = True):
            nonlocal modname, version, modhelp, developer, origin, subscribe, blob_link
            return self.strings("loaded").format(
                modname.strip(),
                version,
                utils.ascii_face(),
                modhelp,
                developer if not subscribe or not use_subscribe else "",
                self.strings("modlink").format(origin)
                if origin != "<string>" and self.config["share_link"]
                else "",
                blob_link,
                subscribe if use_subscribe else "",
            )

        if developer:
            if developer.startswith("@") and developer not in self.get(
                "do_not_subscribe", []
            ):
                try:
                    if developer in self._client._hikka_cache and getattr(
                        await self._client.get_entity(developer), "left", True
                    ):
                        developer_entity = await self._client.force_get_entity(
                            developer
                        )
                    else:
                        developer_entity = await self._client.get_entity(developer)
                except Exception:
                    developer_entity = None

                if (
                    isinstance(developer_entity, Channel)
                    and getattr(developer_entity, "left", True)
                    and self._db.get(main.__name__, "suggest_subscribe", True)
                ):
                    subscribe = self.strings("suggest_subscribe").format(
                        f"@{utils.escape_html(developer_entity.username)}"
                    )
                    subscribe_markup = [
                        {
                            "text": self.strings("subscribe"),
                            "callback": self._inline__subscribe,
                            "args": (
                                developer_entity.id,
                                functools.partial(loaded_msg, use_subscribe=False),
                                True,
                            ),
                        },
                        {
                            "text": self.strings("no_subscribe"),
                            "callback": self._inline__subscribe,
                            "args": (
                                developer,
                                functools.partial(loaded_msg, use_subscribe=False),
                                False,
                            ),
                        },
                    ]

            try:
                is_channel = isinstance(
                    await self._client.get_entity(developer),
                    Channel,
                )
            except Exception:
                is_channel = False

            developer = self.strings("developer").format(
                utils.escape_html(developer)
                if is_channel
                else f"<b>{utils.escape_html(developer)}</b>"
            )
        else:
            developer = ""

        if any(
            line.replace(" ", "") == "#scope:disable_onload_docs"
            for line in doc.splitlines()
        ):
            await utils.answer(message, loaded_msg(), reply_markup=subscribe_markup)
            return

        for _name, fun in sorted(
            instance.commands.items(),
            key=lambda x: x[0],
        ):
            modhelp += self.strings("single_cmd").format(
                self.get_prefix(),
                _name,
                (
                    utils.escape_html(inspect.getdoc(fun))
                    if fun.__doc__
                    else self.strings("undoc_cmd")
                ),
            )

        if self.inline.init_complete:
            if hasattr(instance, "inline_handlers"):
                for _name, fun in sorted(
                    instance.inline_handlers.items(),
                    key=lambda x: x[0],
                ):
                    modhelp += self.strings("ihandler").format(
                        f"@{self.inline.bot_username} {_name}",
                        (
                            utils.escape_html(inspect.getdoc(fun))
                            if fun.__doc__
                            else self.strings("undoc_ihandler")
                        ),
                    )

        try:
            await utils.answer(message, loaded_msg(), reply_markup=subscribe_markup)
        except telethon.errors.rpcerrorlist.MediaCaptionTooLongError:
            await message.reply(loaded_msg(False))

    async def _inline__subscribe(
        self,
        call: InlineCall,
        entity: int,
        msg: callable,
        subscribe: bool,
    ):
        if not subscribe:
            self.set("do_not_subscribe", self.get("do_not_subscribe", []) + [entity])
            await utils.answer(call, msg())
            await call.answer(self.strings("not_subscribed"))
            return

        await self._client(JoinChannelRequest(entity))
        await utils.answer(call, msg())
        await call.answer(self.strings("subscribed"))

    @loader.owner
    async def unloadmodcmd(self, message: Message):
        """Modulni nomi bo'yicha o'chirish"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("no_class"))
            return

        worked = self.allmodules.unload_module(args)

        self.set(
            "loaded_modules",
            {
                mod: link
                for mod, link in self.get("loaded_modules", {}).items()
                if mod not in worked
            },
        )

        msg = (
            self.strings("unloaded").format(
                ", ".join(
                    [(mod[:-3] if mod.endswith("Mod") else mod) for mod in worked]
                )
            )
            if worked
            else self.strings("not_unloaded")
        )

        await utils.answer(message, msg)

    @loader.owner
    async def clearmodulescmd(self, message: Message):
        """Barcha o'rnatilgan modullarni o'chiring"""
        await self.inline.form(
            self.strings("confirm_clearmodules"),
            message,
            reply_markup=[
                {
                    "text": self.strings("clearmodules"),
                    "callback": self._inline__clearmodules,
                },
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
            ],
        )

    async def _inline__clearmodules(self, call: InlineCall):
        self.set("loaded_modules", {})

        if "DYNO" not in os.environ:
            for file in os.scandir(loader.LOADED_MODULES_DIR):
                os.remove(file)

        self.set("chosen_preset", "none")

        await utils.answer(call, self.strings("all_modules_deleted"))
        await self.lookup("Updater").restart_common(call)

    async def _update_modules(self):
        todo = await self._get_modules_to_load()

        # ◽◽  WARNING!  ◽◽
        # If you are a module developer, and you'll try to bypass this protection to
        # force user join your channel, you will be added to SCAM modules
        # list and you will be banned from Hikka federation.
        # Let USER decide, which channel he will follow. Do not be so petty
        # I hope, you understood me.
        # Thank you

        if "https://mods.hikariatama.ru/forbid_joins.py" in todo.values():
            from ..forbid_joins import install_join_forbidder

            install_join_forbidder(self._client)

        for mod in todo.values():
            await self.download_and_install(mod)

        self._update_modules_in_db()

        aliases = {
            alias: cmd
            for alias, cmd in self.lookup("settings").get("aliases", {}).items()
            if self.allmodules.add_alias(alias, cmd)
        }

        self.lookup("settings").set("aliases", aliases)

        self._fully_loaded = True

        try:
            await self.lookup("Updater").full_restart_complete()
        except AttributeError:
            pass

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._fully_loaded = False

        self._links_cache = {}

        self.allmodules.add_aliases(self.lookup("settings").get("aliases", {}))

        main.hikka.ready.set()

        asyncio.ensure_future(self._update_modules())
        asyncio.ensure_future(self.get_repo_list("full"))

    @loader.loop(interval=3, wait_before=True, autostart=True)
    async def _modules_config_autosaver(self):
        for mod in self.allmodules.modules:
            if not hasattr(mod, "config") or not mod.config:
                continue

            for option, config in mod.config._config.items():
                if not hasattr(config, "_save_marker"):
                    continue

                delattr(mod.config._config[option], "_save_marker")
                self._db.setdefault(mod.__class__.__name__, {}).setdefault(
                    "__config__", {}
                )[option] = config.value
                self._db.save()
