import logging
import atexit
import random
import sys
import os
from telethon.tl.types import Message
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.utils import get_display_name
from .. import loader, main, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )


@loader.tds
class HikkaSettingsMod(loader.Module):
    """Advanced settings for Hikka Userbot"""

    strings = {
        "name": "PremiumSettings",
        "user_nn": "◽ <b>NoNick for this user is now {}</b>",
        "no_cmd": "◽ <b>Please, specify command to toggle NoNick for</b>",
        "cmd_nn": "◽ <b>NoNick for </b><code>{}</code><b> is now {}</b>",
        "cmd404": "◽ <b>Command not found</b>",
        "inline_settings": "◽ <b>Here you can configure your Hikka settings</b>",
        "confirm_update": "◽ <b>Please, confirm that you want to update. Your userbot will be restarted</b>",
        "confirm_restart": "◽ <b>Please, confirm that you want to restart</b>",
        "suggest_fs": "◽ Suggest FS for modules",
        "do_not_suggest_fs": "◽ Suggest FS for modules",
        "use_fs": "◽ Always use FS for modules",
        "do_not_use_fs": "◽ Always use FS for modules",
        "btn_restart": "◽ Restart",
        "btn_update": "◽ Update",
        "close_menu": "◽ Close menu",
        "download_btn": "◽ Download via button",
        "no_download_btn": "◽ Download via button",
        "suggest_subscribe": "◽ Suggest subscribe to channel",
        "do_not_suggest_subscribe": "◽ Suggest subscribe to channel",
        "private_not_allowed": "◽ <b>This command must be executed in chat</b>",
        "nonick_warning": (
            "Warning! You enabled NoNick with default prefix! "
            "You may get muted in Hikka chats. Change prefix or "
            "disable NoNick!"
        ),
        "reply_required": "◽ <b>Reply to a message of user, which needs to be added to NoNick</b>",
        "deauth_confirm": (
            "◽ <b>This action will fully remove Hikka from this account and can't be reverted!</b>\n\n"
            "<i>- Hikka chats will be removed\n"
            "- Session will be terminated and removed\n"
            "- Hikka inline bot will be removed</i>"
        ),
        "logs_cleared": "◽ <b>Jurnallar tozalandi</b>",
        "cmd_nn_list": "◽ <b>NoNick is enabled for these commands:</b>\n\n{}",
        "user_nn_list": "◽ <b>NoNick is enabled for these users:</b>\n\n{}",
        "chat_nn_list": "◽ <b>NoNick is enabled for these chats:</b>\n\n{}",
        "nothing": "◽ <b>Nothing to show...</b>",
    }

    strings_ru = {
        "user_nn": "◽ <b>Состояние NoNick для этого пользователя: {}</b>",
        "no_cmd": "◽ <b>Укажи команду, для которой надо включить\\выключить NoNick</b>",
        "cmd_nn": "◽ <b>Состояние NoNick для </b><code>{}</code><b>: {}</b>",
        "cmd404": "◽ <b>Команда не найдена</b>",
        "inline_settings": "◽ <b>Здесь можно управлять настройками Hikka</b>",
        "confirm_update": "◽ <b>Подтвердите обновление. Юзербот будет перезагружен</b>",
        "confirm_restart": "◽ <b>Подтвердите перезагрузку</b>",
        "suggest_fs": "◽ Предлагать сохранение модулей",
        "do_not_suggest_fs": "◽ Предлагать сохранение модулей",
        "use_fs": "◽ Всегда сохранять модули",
        "do_not_use_fs": "◽ Всегда сохранять модули",
        "btn_restart": "◽ Перезагрузка",
        "btn_update": "◽ Обновление",
        "close_menu": "◽ Закрыть меню",
        "download_btn": "◽ Скачивать кнопкой",
        "no_download_btn": "◽ Скачивать кнопкой",
        "suggest_subscribe": "◽ Предлагать подписку на канал",
        "do_not_suggest_subscribe": "◽ Предлагать подписку на канал",
        "private_not_allowed": "◽ <b>Эту команду нужно выполнять в чате</b>",
        "_cmd_doc_watchers": "Показать список смотрителей",
        "_cmd_doc_watcherbl": "<модуль> - Включить\\выключить смотритель в чате",
        "_cmd_doc_watcher": (
            "<модуль> - Управление глобальными правилами смотрителя\n"
            "Аргументы:\n"
            "[-c - только в чатах]\n"
            "[-p - только в лс]\n"
            "[-o - только исходящие]\n"
            "[-i - только входящие]"
        ),
        "_cmd_doc_nonickuser": "Разрешить пользователю выполнять какую-то команду без ника",
        "_cmd_doc_nonickcmd": "Разрешить выполнять определенную команду без ника",
        "_cls_doc": "Дополнительные настройки Hikka",
        "nonick_warning": (
            "Внимание! Ты включил NoNick со стандартным префиксом! "
            "Тебя могут замьютить в чатах Hikka. Измени префикс или "
            "отключи глобальный NoNick!"
        ),
        "reply_required": "◽ <b>Ответь на сообщение пользователя, для которого нужно включить NoNick</b>",
        "deauth_confirm": (
            "◽ <b>Это действие полностью удалит Hikka с этого аккаунта! Его нельзя отменить</b>\n\n"
            "<i>- Все чаты, связанные с Hikka будут удалены\n"
            "- Сессия Hikka будет сброшена\n"
            "- Инлайн бот Hikka будет удален</i>"
        ),
        "logs_cleared": "◽ <b>Логи очищены</b>",
        "cmd_nn_list": "◽ <b>NoNick включен для этих команд:</b>\n\n{}",
        "user_nn_list": "◽ <b>NoNick включен для этих пользователей:</b>\n\n{}",
        "chat_nn_list": "◽ <b>NoNick включен для этих чатов:</b>\n\n{}",
        "nothing": "◽ <b>Нечего показывать...</b>",
    }

    def get_watchers(self) -> tuple:
        return [
            str(watcher.__self__.__class__.strings["name"])
            for watcher in self.allmodules.watchers
            if watcher.__self__.__class__.strings is not None
        ], self._db.get(main.__name__, "disabled_watchers", {})

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def _uninstall(self, call: InlineCall):
        await call.edit(self.strings("uninstall"))

        async with self._client.conversation("@BotFather") as conv:
            for msg in [
                "/deletebot",
                self.inline.bot_username,
                "Yes, I am totally sure.",
            ]:
                m = await conv.send_message(msg)
                r = await conv.get_response()

                logger.debug(f">> {m.raw_text}")
                logger.debug(f"<< {r.raw_text}")

                await m.delete()
                await r.delete()

        async for dialog in self._client.iter_dialogs(
            None,
            ignore_migrated=True,
        ):
            if (
                dialog.name
                in {
                    "hikka-logs",
                    "hikka-onload",
                    "hikka-assets",
                    "hikka-backups",
                    "hikka-acc-switcher",
                    "silent-tags",
                }
                and dialog.is_channel
                and (
                    dialog.entity.participants_count == 1
                    or dialog.entity.participants_count == 2
                    and dialog.name in {"hikka-logs", "silent-tags"}
                )
                or (
                    self._client.loader.inline.init_complete
                    and dialog.entity.id == self._client.loader.inline.bot_id
                )
            ):
                await self._client.delete_dialog(dialog.entity)

        folders = await self._client(GetDialogFiltersRequest())

        if any(folder.title == "hikka" for folder in folders):
            folder_id = max(
                folders,
                key=lambda x: x.id,
            ).id

            await self._client(UpdateDialogFilterRequest(id=folder_id))

        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.CRITICAL)

        await self._client.log_out()

        await call.edit(self.strings("uninstalled"))

        if "LAVHOST" in os.environ:
            os.system("lavhost restart")
            return

        atexit.register(restart, *sys.argv[1:])
        sys.exit(0)

    async def clearlogscmd(self, message: Message):
        """Clear logs"""
        for handler in logging.getLogger().handlers:
            handler.buffer = []
            handler.handledbuffer = []
            handler.tg_buff = ""

        await utils.answer(message, self.strings("logs_cleared"))

    async def nonickusercmd(self, message: Message):
        """Allow no nickname for certain user"""
        reply = await message.get_reply_message()
        if not reply:
            await utils.answer(message, self.strings("reply_required"))
            return

        u = reply.sender_id
        if not isinstance(u, int):
            u = u.user_id

        nn = self._db.get(main.__name__, "nonickusers", [])
        if u not in nn:
            nn += [u]
            nn = list(set(nn))  # skipcq: PTC-W0018
            await utils.answer(message, self.strings("user_nn").format("on"))
        else:
            nn = list(set(nn) - set([u]))  # skipcq: PTC-W0018
            await utils.answer(message, self.strings("user_nn").format("off"))

        self._db.set(main.__name__, "nonickusers", nn)

    async def nonickchatcmd(self, message: Message):
        """Allow no nickname in certain chat"""
        if message.is_private:
            await utils.answer(message, self.strings("private_not_allowed"))
            return

        chat = utils.get_chat_id(message)

        nn = self._db.get(main.__name__, "nonickchats", [])
        if chat not in nn:
            nn += [chat]
            nn = list(set(nn))  # skipcq: PTC-W0018
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    utils.escape_html((await message.get_chat()).title),
                    "on",
                ),
            )
        else:
            nn = list(set(nn) - set([chat]))  # skipcq: PTC-W0018
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    utils.escape_html((await message.get_chat()).title),
                    "off",
                ),
            )

        self._db.set(main.__name__, "nonickchats", nn)

    async def nonickcmdcmd(self, message: Message):
        """Allow certain command to be executed without nickname"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_cmd"))
            return

        if args not in self.allmodules.commands:
            await utils.answer(message, self.strings("cmd404"))
            return

        nn = self._db.get(main.__name__, "nonickcmds", [])
        if args not in nn:
            nn += [args]
            nn = list(set(nn))
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self.get_prefix() + args,
                    "on",
                ),
            )
        else:
            nn = list(set(nn) - set([args]))  # skipcq: PTC-W0018
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self.get_prefix() + args,
                    "off",
                ),
            )

        self._db.set(main.__name__, "nonickcmds", nn)

    async def nonickcmdscmd(self, message: Message):
        """Returns the list of NoNick commands"""
        if not self._db.get(main.__name__, "nonickcmds", []):
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("cmd_nn_list").format(
                "\n".join(
                    [
                        f"▫️ <code>{self.get_prefix()}{cmd}</code>"
                        for cmd in self._db.get(main.__name__, "nonickcmds", [])
                    ]
                )
            ),
        )

    async def nonickuserscmd(self, message: Message):
        """Returns the list of NoNick users"""
        users = []
        for user_id in self._db.get(main.__name__, "nonickusers", []).copy():
            try:
                user = await self._client.get_entity(user_id)
            except Exception:
                self._db.set(
                    main.__name__,
                    "nonickusers",
                    list(
                        set(self._db.get(main.__name__, "nonickusers", []))
                        - set([user_id])
                    ),
                )
                logger.warning(
                    f"User {user_id} removed from nonickusers list", exc_info=True
                )
                continue

            users += [
                f'▫️ <b><a href="tg://user?id={user_id}">{utils.escape_html(get_display_name(user))}</a></b>'
            ]

        if not users:
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("user_nn_list").format("\n".join(users)),
        )

    async def nonickchatscmd(self, message: Message):
        """Returns the list of NoNick chats"""
        chats = []
        for chat in self._db.get(main.__name__, "nonickchats", []):
            try:
                chat_entity = await self._client.get_entity(int(chat))
            except Exception:
                self._db.set(
                    main.__name__,
                    "nonickchats",
                    list(
                        set(self._db.get(main.__name__, "nonickchats", []))
                        - set([chat])
                    ),
                )
                logger.warning(f"Chat {chat} removed from nonickchats list")
                continue

            chats += [
                f'▫️ <b><a href="{utils.get_entity_url(chat_entity)}">{utils.escape_html(get_display_name(chat_entity))}</a></b>'
            ]

        if not chats:
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("user_nn_list").format("\n".join(chats)),
        )

    async def inline__setting(self, call: InlineCall, key: str, state: bool):
        self._db.set(main.__name__, key, state)

        if key == "no_nickname" and state and self.get_prefix() == ".":
            await call.answer(
                self.strings("nonick_warning"),
                show_alert=True,
            )
        else:
            await call.answer("Configuration value saved!")

        await call.edit(
            self.strings("inline_settings"),
            reply_markup=self._get_settings_markup(),
        )

    async def inline__update(
        self,
        call: InlineCall,
        confirm_required: bool = False,
    ):
        if confirm_required:
            await call.edit(
                self.strings("confirm_update"),
                reply_markup=[
                    {"text": "🪂 Update", "callback": self.inline__update},
                    {"text": "◽ Cancel", "action": "close"},
                ],
            )
            return

        await call.answer("You userbot is being updated...", show_alert=True)
        await call.delete()
        m = await self._client.send_message("me", f"{self.get_prefix()}update --force")
        await self.allmodules.commands["update"](m)

    async def inline__restart(
        self,
        call: InlineCall,
        confirm_required: bool = False,
    ):
        if confirm_required:
            await call.edit(
                self.strings("confirm_restart"),
                reply_markup=[
                    {"text": "◽ Restart", "callback": self.inline__restart},
                    {"text": "◽ Cancel", "action": "close"},
                ],
            )
            return

        await call.answer("You userbot is being restarted...", show_alert=True)
        await call.delete()
        await self.allmodules.commands["restart"](
            await self._client.send_message("me", f"{self.get_prefix()}restart --force")
        )

    def _get_settings_markup(self) -> list:
        return [
            [
                (
                    {
                        "text": "◽ NoNick",
                        "callback": self.inline__setting,
                        "args": (
                            "no_nickname",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "no_nickname", False)
                    else {
                        "text": "◽ NoNick",
                        "callback": self.inline__setting,
                        "args": (
                            "no_nickname",
                            True,
                        ),
                    }
                ),
                (
                    {
                        "text": "◽ Grep",
                        "callback": self.inline__setting,
                        "args": (
                            "grep",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "grep", False)
                    else {
                        "text": "◽ Grep",
                        "callback": self.inline__setting,
                        "args": (
                            "grep",
                            True,
                        ),
                    }
                ),
                (
                    {
                        "text": "◽ InlineLogs",
                        "callback": self.inline__setting,
                        "args": (
                            "inlinelogs",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "inlinelogs", True)
                    else {
                        "text": "◽ InlineLogs",
                        "callback": self.inline__setting,
                        "args": (
                            "inlinelogs",
                            True,
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("suggest_fs"),
                        "callback": self.inline__setting,
                        "args": (
                            "disable_modules_fs",
                            True,
                        ),
                    }
                    if not self._db.get(main.__name__, "disable_modules_fs", False)
                    else {
                        "text": self.strings("do_not_suggest_fs"),
                        "callback": self.inline__setting,
                        "args": (
                            "disable_modules_fs",
                            False,
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("use_fs"),
                        "callback": self.inline__setting,
                        "args": (
                            "permanent_modules_fs",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "permanent_modules_fs", False)
                    else {
                        "text": self.strings("do_not_use_fs"),
                        "callback": self.inline__setting,
                        "args": (
                            "permanent_modules_fs",
                            True,
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("suggest_subscribe"),
                        "callback": self.inline__setting,
                        "args": (
                            "suggest_subscribe",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "suggest_subscribe", True)
                    else {
                        "text": self.strings("do_not_suggest_subscribe"),
                        "callback": self.inline__setting,
                        "args": (
                            "suggest_subscribe",
                            True,
                        ),
                    }
                ),
            ],
            [
                {
                    "text": self.strings("btn_restart"),
                    "callback": self.inline__restart,
                    "args": (True,),
                },
                {
                    "text": self.strings("btn_update"),
                    "callback": self.inline__update,
                    "args": (True,),
                },
            ],
            [{"text": self.strings("close_menu"), "action": "close"}],
        ]