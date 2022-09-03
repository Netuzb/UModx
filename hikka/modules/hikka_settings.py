import logging
import atexit
import random
import sys
import os

import telethon
from telethon.tl.types import Message
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.functions.channels import JoinChannelRequest
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
        "name": "HikkaSettings",
        "watchers": (
            "<emoji document_id='5424885441100782420'>👀</emoji>"
            " <b>Watchers:</b>\n\n<b>{}</b>"
        ),
        "mod404": (
            "<emoji document_id='5447207618793708263'>🚫</emoji> <b>Watcher {} not"
            " found</b>"
        ),
        "disabled": (
            "<emoji document_id='5424885441100782420'>👀</emoji> <b>Watcher {} is now"
            " <u>disabled</u></b>"
        ),
        "enabled": (
            "<emoji document_id='5424885441100782420'>👀</emoji> <b>Watcher {} is now"
            " <u>enabled</u></b>"
        ),
        "args": (
            "<emoji document_id='5447207618793708263'>🚫</emoji> <b>You need to specify"
            " watcher name</b>"
        ),
        "user_nn": (
            "<emoji document_id='5469791106591890404'>🪄</emoji> <b>NoNick for this user"
            " is now {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id='5469791106591890404'>🪄</emoji> <b>Please, specify"
            " command to toggle NoNick for</b>"
        ),
        "cmd_nn": (
            "<emoji document_id='5469791106591890404'>🪄</emoji> <b>NoNick for"
            " </b><code>{}</code><b> is now {}</b>"
        ),
        "cmd404": (
            "<emoji document_id='5469791106591890404'>🪄</emoji> <b>Command not"
            " found</b>"
        ),
        "inline_settings": "⚙️ <b>Here you can configure your Hikka settings</b>",
        "confirm_update": (
            "🧭 <b>Please, confirm that you want to update. Your userbot will be"
            " restarted</b>"
        ),
        "confirm_restart": "🔄 <b>Please, confirm that you want to restart</b>",
        "suggest_fs": "✅ Suggest FS for modules",
        "do_not_suggest_fs": "🚫 Suggest FS for modules",
        "use_fs": "✅ Always use FS for modules",
        "do_not_use_fs": "🚫 Always use FS for modules",
        "btn_restart": "🔄 Restart",
        "btn_update": "🧭 Update",
        "close_menu": "😌 Close menu",
        "custom_emojis": "✅ Custom emojis",
        "no_custom_emojis": "🚫 Custom emojis",
        "suggest_subscribe": "✅ Suggest subscribe to channel",
        "do_not_suggest_subscribe": "🚫 Suggest subscribe to channel",
        "private_not_allowed": (
            "<emoji document_id='5447207618793708263'>🚫</emoji> <b>This command must be"
            " executed in chat</b>"
        ),
        "nonick_warning": (
            "Warning! You enabled NoNick with default prefix! "
            "You may get muted in Hikka chats. Change prefix or "
            "disable NoNick!"
        ),
        "reply_required": (
            "<emoji document_id='5447207618793708263'>🚫</emoji> <b>Reply to a message"
            " of user, which needs to be added to NoNick</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>This action will fully remove Hikka from this account and can't be"
            " reverted!</b>\n\n<i>- Hikka chats will be removed\n- Session will be"
            " terminated and removed\n- Hikka inline bot will be removed</i>"
        ),
        "deauth_confirm_step2": (
            "⚠️ <b>Are you really sure you want to delete Hikka?</b>"
        ),
        "deauth_yes": "I'm sure",
        "deauth_no_1": "I'm not sure",
        "deauth_no_2": "I'm uncertain",
        "deauth_no_3": "I'm struggling to answer",
        "deauth_cancel": "🚫 Cancel",
        "deauth_confirm_btn": "😢 Delete",
        "uninstall": "😢 <b>Uninstalling Hikka...</b>",
        "uninstalled": (
            "😢 <b>Hikka uninstalled. Web interface is still active, you can add another"
            " account</b>"
        ),
        "logs_cleared": "🗑 <b>Logs cleared</b>",
        "cmd_nn_list": (
            "<emoji document_id='5469791106591890404'>🪄</emoji> <b>NoNick is enabled"
            " for these commands:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id='5469791106591890404'>🪄</emoji> <b>NoNick is enabled"
            " for these users:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id='5469791106591890404'>🪄</emoji> <b>NoNick is enabled"
            " for these chats:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id='5427052514094619126'>🤷‍♀️</emoji> <b>Nothing to"
            " show...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>This command gives access to your Hikka web interface. It's not"
            " recommended to run it in public group chats. Consider using it in <a"
            " href='tg://openmessage?user_id={}'>Saved messages</a>. Type"
            " </b><code>{}proxypass force_insecure</code><b> to ignore this warning</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>This command gives access to your Hikka web interface. It's not"
            " recommended to run it in public group chats. Consider using it in <a"
            " href='tg://openmessage?user_id={}'>Saved messages</a>.</b>"
        ),
        "opening_tunnel": "🔁 <b>Opening tunnel to Hikka web interface...</b>",
        "tunnel_opened": "🎉 <b>Tunnel opened. This link is valid for about 1 hour</b>",
        "web_btn": "🌍 Web interface",
        "btn_yes": "🚸 Open anyway",
        "btn_no": "🔻 Cancel",
        "lavhost_web": (
            "✌️ <b>This link leads to your Hikka web interface on lavHost</b>\n\n<i>💡"
            " You'll need to authorize using lavHost credentials, specified on"
            " registration</i>"
        ),
        "disable_stats": "✅ Anonymous stats allowed",
        "enable_stats": "🚫 Anonymous stats disabled",
    }

    def get_watchers(self) -> tuple:
        return [
            str(watcher.__self__.__class__.strings["name"])
            for watcher in self.allmodules.watchers
            if watcher.__self__.__class__.strings is not None
        ], self._db.get(main.__name__, "disabled_watchers", {})


    @loader.command(ru_doc="Очистить логи")
    async def clearlogs(self, message: Message):
        """Clear logs"""
        for handler in logging.getLogger().handlers:
            handler.buffer = []
            handler.handledbuffer = []
            handler.tg_buff = ""

        await utils.answer(message, self.strings("logs_cleared"))

    @loader.command(ru_doc="Включить NoNick для определенного пользователя")
    async def nonickuser(self, message: Message):
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
            nn = list(set(nn) - {u})
            await utils.answer(message, self.strings("user_nn").format("off"))

        self._db.set(main.__name__, "nonickusers", nn)

    @loader.command(ru_doc="Включить NoNick для определенного чата")
    async def nonickchat(self, message: Message):
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
            nn = list(set(nn) - {chat})
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    utils.escape_html((await message.get_chat()).title),
                    "off",
                ),
            )

        self._db.set(main.__name__, "nonickchats", nn)

    @loader.command(ru_doc="Включить NoNick для определенной команды")
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
            nn = list(set(nn) - {args})
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self.get_prefix() + args,
                    "off",
                ),
            )

        self._db.set(main.__name__, "nonickcmds", nn)

    @loader.command(ru_doc="Показать список активных NoNick команд")
    async def nonickcmds(self, message: Message):
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

    @loader.command(ru_doc="Показать список активных NoNick пользователей")
    async def nonickusers(self, message: Message):
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
                        (
                            set(self._db.get(main.__name__, "nonickusers", []))
                            - {user_id}
                        )
                    ),
                )

                logger.warning(
                    f"User {user_id} removed from nonickusers list", exc_info=True
                )
                continue

            users += [
                "▫️ <b><a"
                f' href="tg://user?id={user_id}">{utils.escape_html(get_display_name(user))}</a></b>'
            ]

        if not users:
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("user_nn_list").format("\n".join(users)),
        )

    @loader.command(ru_doc="Показать список активных NoNick чатов")
    async def nonickchats(self, message: Message):
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
                        (set(self._db.get(main.__name__, "nonickchats", [])) - {chat})
                    ),
                )

                logger.warning(f"Chat {chat} removed from nonickchats list")
                continue

            chats += [
                "▫️ <b><a"
                f' href="{utils.get_entity_url(chat_entity)}">{utils.escape_html(get_display_name(chat_entity))}</a></b>'
            ]

        if not chats:
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("user_nn_list").format("\n".join(chats)),
        )

    async def inline__setting(self, call: InlineCall, key: str, state: bool = False):
        if callable(key):
            key()
            telethon.extensions.html.CUSTOM_EMOJIS = not main.get_config_key(
                "disable_custom_emojis"
            )
        else:
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
                    {"text": "🚫 Cancel", "action": "close"},
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
                    {"text": "🔄 Restart", "callback": self.inline__restart},
                    {"text": "🚫 Cancel", "action": "close"},
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
                        "text": "✅ NoNick",
                        "callback": self.inline__setting,
                        "args": (
                            "no_nickname",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "no_nickname", False)
                    else {
                        "text": "🚫 NoNick",
                        "callback": self.inline__setting,
                        "args": (
                            "no_nickname",
                            True,
                        ),
                    }
                ),
                (
                    {
                        "text": "✅ Grep",
                        "callback": self.inline__setting,
                        "args": (
                            "grep",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "grep", False)
                    else {
                        "text": "🚫 Grep",
                        "callback": self.inline__setting,
                        "args": (
                            "grep",
                            True,
                        ),
                    }
                ),
                (
                    {
                        "text": "✅ InlineLogs",
                        "callback": self.inline__setting,
                        "args": (
                            "inlinelogs",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "inlinelogs", True)
                    else {
                        "text": "🚫 InlineLogs",
                        "callback": self.inline__setting,
                        "args": (
                            "inlinelogs",
                            True,
                        ),
                    }
                ),
            ],
            [
                {
                    "text": self.strings("do_not_suggest_fs"),
                    "callback": self.inline__setting,
                    "args": (
                        "disable_modules_fs",
                        False,
                    ),
                }
                if self._db.get(main.__name__, "disable_modules_fs", False)
                else {
                    "text": self.strings("suggest_fs"),
                    "callback": self.inline__setting,
                    "args": (
                        "disable_modules_fs",
                        True,
                    ),
                }
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
                (
                    {
                        "text": self.strings("no_custom_emojis"),
                        "callback": self.inline__setting,
                        "args": (
                            lambda: main.save_config_key(
                                "disable_custom_emojis", False
                            ),
                        ),
                    }
                    if main.get_config_key("disable_custom_emojis")
                    else {
                        "text": self.strings("custom_emojis"),
                        "callback": self.inline__setting,
                        "args": (
                            lambda: main.save_config_key("disable_custom_emojis", True),
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("disable_stats"),
                        "callback": self.inline__setting,
                        "args": ("stats", False),
                    }
                    if self._db.get(main.__name__, "stats", True)
                    else {
                        "text": self.strings("enable_stats"),
                        "callback": self.inline__setting,
                        "args": (
                            "stats",
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

    @loader.owner
    @loader.command(ru_doc="Показать настройки")
    async def settings(self, message: Message):
        """Show settings menu"""
        await self.inline.form(
            self.strings("inline_settings"),
            message=message,
            reply_markup=self._get_settings_markup(),
        )

    @loader.owner
    @loader.command(ru_doc="Открыть тоннель к веб-интерфейсу Hikka")
    async def weburl(self, message: Message, force: bool = False):
        """Opens web tunnel to your Hikka web interface"""
        if "LAVHOST" in os.environ:
            form = await self.inline.form(
                self.strings("lavhost_web"),
                message=message,
                reply_markup={
                    "text": self.strings("web_btn"),
                    "url": await main.hikka.web.get_url(proxy_pass=False),
                },
                gif="https://t.me/hikari_assets/28",
            )
            return

        if (
            not force
            and not message.is_private
            and "force_insecure" not in message.raw_text.lower()
        ):
            try:
                if not await self.inline.form(
                    self.strings("privacy_leak_nowarn").format(self._client.tg_id),
                    message=message,
                    reply_markup=[
                        {
                            "text": self.strings("btn_yes"),
                            "callback": self.weburl,
                            "args": (True,),
                        },
                        {"text": self.strings("btn_no"), "action": "close"},
                    ],
                    gif="https://i.gifer.com/embedded/download/Z5tS.gif",
                ):
                    raise Exception
            except Exception:
                await utils.answer(
                    message,
                    self.strings("privacy_leak").format(
                        self._client.tg_id,
                        self.get_prefix(),
                    ),
                )

            return

        if force:
            form = message
            await form.edit(
                self.strings("opening_tunnel"),
                reply_markup={"text": "🕔 Wait...", "data": "empty"},
                gif=(
                    "https://i.gifer.com/origin/e4/e43e1b221fd960003dc27d2f2f1b8ce1.gif"
                ),
            )
        else:
            form = await self.inline.form(
                self.strings("opening_tunnel"),
                message=message,
                reply_markup={"text": "🕔 Wait...", "data": "empty"},
                gif=(
                    "https://i.gifer.com/origin/e4/e43e1b221fd960003dc27d2f2f1b8ce1.gif"
                ),
            )

        url = await main.hikka.web.get_url(proxy_pass=True)

        await form.edit(
            self.strings("tunnel_opened"),
            reply_markup={"text": self.strings("web_btn"), "url": url},
            gif="https://t.me/hikari_assets/28",
        )

    @loader.loop(interval=1, autostart=True)
    async def loop(self):
        obj = self.allmodules.get_approved_channel
        if not obj:
            return

        channel, event = obj

        try:
            await self._client(JoinChannelRequest(channel))
        except Exception:
            logger.exception("Failed to join channel")
            event.status = False
            event.set()
        else:
            event.status = True
            event.set()
