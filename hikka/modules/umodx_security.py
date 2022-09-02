import logging
import time
from typing import List, Union

from telethon.tl.types import Message, PeerUser, User
from telethon.utils import get_display_name
from telethon.hints import EntityLike

from .. import loader, security, utils, main
from ..inline.types import InlineCall, InlineMessage
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

    service_strings = {
        "for": "for",
        "forever": "forever",
        "user": "user",
        "chat": "chat",
        "command": "command",
        "module": "module",
        "day": "day",
        "days": "days",
        "hour": "hour",
        "hours": "hours",
        "minute": "minute",
        "minutes": "minutes",
        "second": "second",
        "seconds": "seconds",
    }

    strings = {
        "name": "Security",
        "no_command": "🚫 <b>Command </b><code>{}</code><b> not found!</b>",
        "permissions": (
            "🔐 <b>Here you can configure permissions for </b><code>{}{}</code>"
        ),
        "close_menu": "🙈 Close this menu",
        "global": (
            "🔐 <b>Here you can configure global bounding mask. If the permission is"
            " excluded here, it is excluded everywhere!</b>"
        ),
        "owner": "😎 Owner",
        "group_owner": "🧛‍♂️ Group owner",
        "group_admin_add_admins": "🧑‍⚖️ Admin (add members)",
        "group_admin_change_info": "🧑‍⚖️ Admin (change info)",
        "group_admin_ban_users": "🧑‍⚖️ Admin (ban)",
        "group_admin_delete_messages": "🧑‍⚖️ Admin (delete msgs)",
        "group_admin_pin_messages": "🧑‍⚖️ Admin (pin)",
        "group_admin_invite_users": "🧑‍⚖️ Admin (invite)",
        "group_admin": "🧑‍⚖️ Admin (any)",
        "group_member": "👥 In group",
        "pm": "🤙 In PM",
        "everyone": "🌍 Everyone (Inline)",
        "owner_list": (
            "<emoji document_id='5386399931378440814'>😎</emoji> <b>Users in group"
            " </b><code>owner</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id='5386399931378440814'>😎</emoji> <b>There is no users in"
            " group </b><code>owner</code>"
        ),
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> added to group </b><code>owner</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> removed from group </b><code>owner</code>'
        ),
        "no_user": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>Specify user to"
            " permit</b>"
        ),
        "not_a_user": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>Specified entity is"
            " not a user</b>"
        ),
        "li": '⦿ <b><a href="tg://user?id={}">{}</a></b>',
        "warning": (
            "⚠️ <b>Please, confirm, that you want to add <a"
            ' href="tg://user?id={}">{}</a> to group </b><code>{}</code><b>!\nThis'
            " action may reveal personal info and grant full or partial access to"
            " userbot to this user</b>"
        ),
        "cancel": "🚫 Cancel",
        "confirm": "👑 Confirm",
        "enable_nonick_btn": "🔰 Enable",
        "self": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>You can't"
            " promote/demote yourself!</b>"
        ),
        "suggest_nonick": "🔰 <i>Do you want to enable NoNick for this user?</i>",
        "user_nn": '🔰 <b>NoNick for <a href="tg://user?id={}">{}</a> enabled</b>',
        "what": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>You need to specify"
            " the type of target as first argument (</b><code>user</code><b> or"
            " </b><code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>You didn't specify"
            " the target of security rule</b>"
        ),
        "no_rule": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>You didn't specify"
            " the rule (module or command)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Please, confirm that you want to give {} <a href='{}'>{}</a> a"
            " permission to use {} </b><code>{}</code><b> {}?</b>"
        ),
        "rule_added": (
            "🔐 <b>You gave {} <a href='{}'>{}</a> a"
            " permission to use {} </b><code>{}</code><b> {}</b>"
        ),
        "confirm_btn": "👑 Confirm",
        "cancel_btn": "🚫 Cancel",
        "multiple_rules": (
            "🔐 <b>Unable to unambiguously determine the security rule. Please, choose"
            " the one you meant:</b>\n\n{}"
        ),
        "rules": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Targeted security"
            " rules:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>No targeted security"
            " rules</b>"
        ),
        "owner_target": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>This user is owner"
            " and can't be promoted by targeted security</b>"
        ),
        "rules_removed": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Targeted security"
            ' rules for <a href="{}">{}</a> removed</b>'
        ),
        **service_strings,
    }

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
                "Security value set but not applied. Consider enabling this value in"
                f" .{'inlinesec' if is_inline else 'security'}",
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
        return (
            utils.chunks(
                [
                    {
                        "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
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
            )
            + [[{"text": self.strings("close_menu"), "action": "close"}]]
            if is_inline
            else utils.chunks(
                [
                    {
                        "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
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
            )
            + [
                [
                    {
                        "text": self.strings("close_menu"),
                        "action": "close",
                    }
                ]
            ]
        )

    def _build_markup_global(self, is_inline: bool = False) -> List[List[dict]]:
        perms = self._get_current_bm(is_inline)
        return utils.chunks(
            [
                {
                    "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
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
            getattr(command, "security", self._client.dispatcher.security.default),
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

        if user.id == self.tg_id:
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

        if user.id not in getattr(self._client.dispatcher.security, group):
            getattr(self._client.dispatcher.security, group).append(user.id)

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

        if user.id in getattr(self._client.dispatcher.security, group):
            getattr(self._client.dispatcher.security, group).remove(user.id)

        m = self.strings(f"{group}_removed").format(
            user.id,
            utils.escape_html(get_display_name(user)),
        )

        await utils.answer(message, m)

    async def _list_group(self, message: Message, group: str):
        _resolved_users = []
        for user in getattr(self._client.dispatcher.security, group) + (
            [self.tg_id] if group == "owner" else []
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

    @loader.command(ru_doc="<пользователь> - Добавить пользователя в группу `owner`")
    async def owneradd(self, message: Message):
        """<user> - Add user to `owner`"""
        await self._add_to_group(message, "owner")

    @loader.command(ru_doc="<пользователь> - Удалить пользователя из группы `owner`")
    async def ownerrm(self, message: Message):
        """<user> - Remove user from `owner`"""
        await self._remove_from_group(message, "owner")

    @loader.command(ru_doc="Показать список пользователей в группе `owner`")
    async def ownerlist(self, message: Message):
        """List users in `owner`"""
        await self._list_group(message, "owner")

    def _lookup(self, needle: str) -> str:
        return (
            []
            if needle.lower().startswith(self.get_prefix())
            else (
                [f"module/{self.lookup(needle).__class__.__name__}"]
                if self.lookup(needle)
                else []
            )
        ) + (
            [f"command/{needle.lower().strip(self.get_prefix())}"]
            if needle.lower().strip(self.get_prefix()) in self.allmodules.commands
            else []
        )

    @staticmethod
    def _extract_time(args: list) -> int:
        suffixes = {
            "d": 24 * 60 * 60,
            "h": 60 * 60,
            "m": 60,
            "s": 1,
        }
        for suffix, quantifier in suffixes.items():
            duration = next(
                (
                    int(arg.rsplit(suffix, maxsplit=1)[0])
                    for arg in args
                    if arg.endswith(suffix)
                    and arg.rsplit(suffix, maxsplit=1)[0].isdigit()
                ),
                None,
            )
            if duration is not None:
                return duration * quantifier

        return 0

    def _convert_time(self, duration: int) -> str:
        return (
            (
                f"{duration // (24 * 60 * 60)} "
                + self.strings(f"day{'s' if duration // (24 * 60 * 60) > 1 else ''}")
            )
            if duration >= 24 * 60 * 60
            else (
                (
                    f"{duration // (60 * 60)} "
                    + self.strings(f"hour{'s' if duration // (60 * 60) > 1 else ''}")
                )
                if duration >= 60 * 60
                else (
                    (
                        f"{duration // 60} "
                        + self.strings(f"minute{'s' if duration // 60 > 1 else ''}")
                    )
                    if duration >= 60
                    else (
                        f"{duration} "
                        + self.strings(f"second{'s' if duration > 1 else ''}")
                    )
                )
            )
        )

    async def _add_rule(
        self,
        call: InlineCall,
        target_type: str,
        target: EntityLike,
        rule: str,
        duration: int,
    ):
        self._client.dispatcher.security.add_rule(
            target_type,
            target,
            rule,
            duration,
        )

        await call.edit(
            self.strings("rule_added").format(
                self.strings(target_type),
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
                self.strings(rule.split("/", maxsplit=1)[0]),
                rule.split("/", maxsplit=1)[1],
                (self.strings("for") + " " + self._convert_time(duration))
                if duration
                else self.strings("forever"),
            )
        )

    async def _confirm(
        self,
        obj: Union[Message, InlineMessage],
        target_type: str,
        target: EntityLike,
        rule: str,
        duration: int,
    ):
        await utils.answer(
            obj,
            self.strings("confirm_rule").format(
                self.strings(target_type),
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
                self.strings(rule.split("/", maxsplit=1)[0]),
                rule.split("/", maxsplit=1)[1],
                (self.strings("for") + " " + self._convert_time(duration))
                if duration
                else self.strings("forever"),
            ),
            reply_markup=[
                {
                    "text": self.strings("confirm_btn"),
                    "callback": self._add_rule,
                    "args": (target_type, target, rule, duration),
                },
                {"text": self.strings("cancel_btn"), "action": "close"},
            ],
        )
