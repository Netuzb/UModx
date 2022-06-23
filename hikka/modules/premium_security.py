import logging
from typing import List, Union
from telethon.tl.types import Message, PeerUser, User
from telethon.utils import get_display_name
from .. import loader, security, utils, main
from ..inline.types import InlineCall
from ..security import (
    DEFAULT_PERMISSIONS,
    EVERYONE,
    GROUP_ADMIN,
    GROUP_ADMIN_ADD_ADMINS,
    GROUP_ADMIN_BAN_USERS,
    GROUP_ADMIN_CHANGE_INFO,
    GROUP_ADMIN_DELETE_MESSAGES,
    GROUP_ADMIN_INVITE_USERS,
    GROUP_ADMIN_PIN_MESSAGES,
    GROUP_MEMBER,
    GROUP_OWNER,
    PM,
    SUDO,
    SUPPORT,
)

logger = logging.getLogger(__name__)


@loader.tds
class HikkaSecurityMod(loader.Module):
    """Control security settings"""

    strings = {
        "name": "Security",
        "owner_list": "◽ <b>Premium-Userbot </b><code>Owner</code><b> guruhidagilar:</b>\n◽ Barchasi sizning <b><u>userbot</u></b>'ni boshqara oladi.\n\n{}",
        "owner_added": '◽ <b><a href="tg://user?id={}">{}</a> Owner guruhiga kiritildi.</b>',
        "owner_removed": '◽ <b><a href="tg://user?id={}">{}</a> Owner guruhidan olindi.</b>',
        "no_user": "◽ <b>Kimni <code>Owner</code> guruhidan olish kerak?</b> (reply/username)",
        "not_a_user": "◽ <b>Bu foydalanuvchi emas!</b>",
        "li": '◽ <b><a href="tg://user?id={}">{}</a></b> - tanishingiz.',
        "warning": (
            '◽ <b>Iltimos, jarayonni tasdiqlang <a href="tg://user?id={}">{}</a> '
            "shaxsini «<code>{}</code>» guruhiga qoʻshish"
            " va keyinchalik u sizga tegishli barcha buyruqlarni bajara oladi.</b>"
        ),
        "cancel": "◽ Bekor qilish",
        "confirm": "◽ Tasdiqlash",
        "enable_nonick_btn": "◽ Ha // Yoqaman",
        "self": "◽ <b>Siz o'zingizni targ'ib qila olmaysiz/pasaytira olmaysiz!</b>",
        "suggest_nonick": "◽ <i>Ushbu foydalanuvchi uchun NoNick-ni yoqmoqchimisiz?</i>",
        "user_nn": '◽ <b>Endi NoNick <a href="tg://user?id={}">{}</a> uchun yoniq.</b>',
    }

    strings_ru = {
        "owner_list": "◽ <b>Пользователи группы </b><code>owner</code><b>:</b>\n\n{}",
        "no_owner": "◽ <b>Нет пользователей в группе </b><code>owner</code>",
        "no_user": "◽ <b>Укажи, кому выдавать права</b>",
        "not_a_user": "◽ <b>Указанная цель - не пользователь</b>",
        "cancel": "◽ Отмена",
        "confirm": "◽ Подтвердить",
        "self": "◽ <b>Нельзя управлять своими правами!</b>",
        "warning": (
            '◽ <b>Ты действительно хочешь добавить <a href="tg://user?id={}">{}</a> '
            "в группу </b><code>{}</code><b>!\nЭто действие может передать частичный или"
            " полный доступ к юзерботу этому пользователю!</b>"
        ),
        "suggest_nonick": "◽ <i>Хочешь ли ты включить NoNick для этого пользователя?</i>",
        "user_nn": '◽ <b>NoNick для <a href="tg://user?id={}">{}</a> включен</b>',
        "enable_nonick_btn": "◽ Включить",
        "_cmd_doc_security": "[команда] - Изменить настройки безопасности для команды",
        "_cmd_doc_sudoadd": "<пользователь> - Добавить пользователя в группу `sudo`",
        "_cmd_doc_owneradd": "<пользователь> - Добавить пользователя в группу `owner`",
        "_cmd_doc_supportadd": "<пользователь> - Добавить пользователя в группу `support`",
        "_cmd_doc_sudorm": "<пользователь> - Удалить пользователя из группы `sudo`",
        "_cmd_doc_ownerrm": "<пользователь> - Удалить пользователя из группы `owner`",
        "_cmd_doc_supportrm": "<пользователь> - Удалить пользователя из группы `support`",
        "_cmd_doc_sudolist": "Показать пользователей в группе `sudo`",
        "_cmd_doc_ownerlist": "Показать пользователей в группе `owner`",
        "_cmd_doc_supportlist": "Показать пользователей в группе `support`",
        "_cls_doc": "Управление настройками безопасности",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def inline__switch_perm(
        self,
        call: InlineCall,
        command: str,
        group: str,
        level: bool,
        is_inline: bool,
    ):
        cmd = (
            self.allmodules.inline_handlers[command]
            if is_inline
            else self.allmodules.commands[command]
        )

        mask = self._db.get(security.__name__, "masks", {}).get(
            f"{cmd.__module__}.{cmd.__name__}",
            getattr(cmd, "security", security.DEFAULT_PERMISSIONS),
        )

        bit = security.BITMAP[group.upper()]

        if level:
            mask |= bit
        else:
            mask &= ~bit

        masks = self._db.get(security.__name__, "masks", {})
        masks[f"{cmd.__module__}.{cmd.__name__}"] = mask
        self._db.set(security.__name__, "masks", masks)

        if (
            not self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS)
            & bit
            and level
        ):
            await call.answer(
                f"Security value set but not applied. Consider enabling this value in .{'inlinesec' if is_inline else 'security'}",
                show_alert=True,
            )
        else:
            await call.answer("Security value set!")

        await call.edit(
            self.strings("permissions").format(
                f"@{self.inline.bot_username} " if is_inline else self.get_prefix(),
                command,
            ),
            reply_markup=self._build_markup(cmd, is_inline),
        )

    async def inline__switch_perm_bm(
        self,
        call: InlineCall,
        group: str,
        level: bool,
        is_inline: bool,
    ):
        mask = self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS)
        bit = security.BITMAP[group.upper()]

        if level:
            mask |= bit
        else:
            mask &= ~bit

        self._db.set(security.__name__, "bounding_mask", mask)

        await call.answer("Bounding mask value set!")
        await call.edit(
            self.strings("global"),
            reply_markup=self._build_markup_global(is_inline),
        )

    def _build_markup(
        self,
        command: callable,
        is_inline: bool = False,
    ) -> List[List[dict]]:
        perms = self._get_current_perms(command, is_inline)
        if not is_inline:
            return utils.chunks(
                [
                    {
                        "text": f"{'✅' if level else '◽'} {self.strings[group]}",
                        "callback": self.inline__switch_perm,
                        "args": (
                            command.__name__.rsplit("cmd", maxsplit=1)[0],
                            group,
                            not level,
                            is_inline,
                        ),
                    }
                    for group, level in perms.items()
                ],
                2,
            ) + [
                [
                    {
                        "text": self.strings("close_menu"),
                        "action": "close",
                    }
                ]
            ]

        return utils.chunks(
            [
                {
                    "text": f"{'✅' if level else '◽'} {self.strings[group]}",
                    "callback": self.inline__switch_perm,
                    "args": (
                        command.__name__.rsplit("_inline_handler", maxsplit=1)[0],
                        group,
                        not level,
                        is_inline,
                    ),
                }
                for group, level in perms.items()
            ],
            2,
        ) + [[{"text": self.strings("close_menu"), "action": "close"}]]

    def _build_markup_global(self, is_inline: bool = False) -> List[List[dict]]:
        perms = self._get_current_bm(is_inline)
        return utils.chunks(
            [
                {
                    "text": f"{'✅' if level else '◽'} {self.strings[group]}",
                    "callback": self.inline__switch_perm_bm,
                    "args": (group, not level, is_inline),
                }
                for group, level in perms.items()
            ],
            2,
        ) + [[{"text": self.strings("close_menu"), "action": "close"}]]

    def _get_current_bm(self, is_inline: bool = False) -> dict:
        return self._perms_map(
            self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS),
            is_inline,
        )

    @staticmethod
    def _perms_map(perms: int, is_inline: bool) -> dict:
        return (
            {
                "sudo": bool(perms & SUDO),
                "support": bool(perms & SUPPORT),
                "everyone": bool(perms & EVERYONE),
            }
            if is_inline
            else {
                "sudo": bool(perms & SUDO),
                "support": bool(perms & SUPPORT),
                "group_owner": bool(perms & GROUP_OWNER),
                "group_admin_add_admins": bool(perms & GROUP_ADMIN_ADD_ADMINS),
                "group_admin_change_info": bool(perms & GROUP_ADMIN_CHANGE_INFO),
                "group_admin_ban_users": bool(perms & GROUP_ADMIN_BAN_USERS),
                "group_admin_delete_messages": bool(
                    perms & GROUP_ADMIN_DELETE_MESSAGES
                ),
                "group_admin_pin_messages": bool(perms & GROUP_ADMIN_PIN_MESSAGES),
                "group_admin_invite_users": bool(perms & GROUP_ADMIN_INVITE_USERS),
                "group_admin": bool(perms & GROUP_ADMIN),
                "group_member": bool(perms & GROUP_MEMBER),
                "pm": bool(perms & PM),
                "everyone": bool(perms & EVERYONE),
            }
        )

    def _get_current_perms(
        self,
        command: callable,
        is_inline: bool = False,
    ) -> dict:
        config = self._db.get(security.__name__, "masks", {}).get(
            f"{command.__module__}.{command.__name__}",
            getattr(command, "security", self._client.dispatcher.security._default),
        )

        return self._perms_map(config, is_inline)

    async def _resolve_user(self, message: Message):
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)

        if not args and not reply:
            await utils.answer(message, self.strings("no_user"))
            return

        user = None

        if args:
            try:
                if str(args).isdigit():
                    args = int(args)

                user = await self._client.get_entity(args)
            except Exception:
                pass

        if user is None:
            user = await self._client.get_entity(reply.sender_id)

        if not isinstance(user, (User, PeerUser)):
            await utils.answer(message, self.strings("not_a_user"))
            return

        if user.id == self._tg_id:
            await utils.answer(message, self.strings("self"))
            return

        return user

    async def _add_to_group(
        self,
        message: Union[Message, InlineCall],  # noqa: F821
        group: str,
        confirmed: bool = False,
        user: int = None,
    ):
        if user is None:
            user = await self._resolve_user(message)
            if not user:
                return

        if isinstance(user, int):
            user = await self._client.get_entity(user)

        if not confirmed:
            await self.inline.form(
                self.strings("warning").format(
                    user.id,
                    utils.escape_html(get_display_name(user)),
                    group,
                ),
                message=message,
                ttl=10 * 60,
                reply_markup=[
                    {
                        "text": self.strings("cancel"),
                        "action": "close",
                    },
                    {
                        "text": self.strings("confirm"),
                        "callback": self._add_to_group,
                        "args": (group, True, user.id),
                    },
                ],
            )
            return

        self._db.set(
            security.__name__,
            group,
            list(set(self._db.get(security.__name__, group, []) + [user.id])),
        )

        m = (
            self.strings(f"{group}_added").format(
                user.id,
                utils.escape_html(get_display_name(user)),
            )
            + "\n\n"
            + self.strings("suggest_nonick")
        )

        await utils.answer(message, m)
        await message.edit(
            m,
            reply_markup=[
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
                {
                    "text": self.strings("enable_nonick_btn"),
                    "callback": self._enable_nonick,
                    "args": (user,),
                },
            ],
        )

    async def _enable_nonick(self, call: InlineCall, user: User):
        self._db.set(
            main.__name__,
            "nonickusers",
            list(set(self._db.get(main.__name__, "nonickusers", []) + [user.id])),
        )

        await call.edit(
            self.strings("user_nn").format(
                user.id,
                utils.escape_html(get_display_name(user)),
            )
        )

        await call.unload()

    async def _remove_from_group(self, message: Message, group: str):
        user = await self._resolve_user(message)
        if not user:
            return

        self._db.set(
            security.__name__,
            group,
            list(set(self._db.get(security.__name__, group, [])) - {user.id}),
        )

        m = self.strings(f"{group}_removed").format(
            user.id,
            utils.escape_html(get_display_name(user)),
        )

        await utils.answer(message, m)

    async def _list_group(self, message: Message, group: str):
        _resolved_users = []
        for user in self._db.get(security.__name__, group, []) + (
            [self._tg_id] if group == "owner" else []
        ):
            try:
                _resolved_users += [await self._client.get_entity(user)]
            except Exception:
                pass

        if _resolved_users:
            await utils.answer(
                message,
                self.strings(f"{group}_list").format(
                    "\n".join(
                        [
                            self.strings("li").format(
                                i.id, utils.escape_html(get_display_name(i))
                            )
                            for i in _resolved_users
                        ]
                    )
                ),
            )
        else:
            await utils.answer(message, self.strings(f"no_{group}"))

    async def owneraddcmd(self, message: Message):
        """<user> - Foydalanuvchini “ega”ga qo‘shing"""
        await self._add_to_group(message, "owner")

    async def ownerrmcmd(self, message: Message):
        """<user> - Foydalanuvchini "ega"dan olib tashlang"""
        await self._remove_from_group(message, "owner")

    async def ownerlistcmd(self, message: Message):
        """Foydalanuvchilarni “ega” roʻyxati"""
        await self._list_group(message, "owner")