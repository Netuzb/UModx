import os
from telethon.tl.types import Message
from telethon.extensions.html import CUSTOM_EMOJIS
from .. import loader, main, translations, utils
from ..inline.types import InlineCall

@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {
        "name": "Settings",
        "too_many_args": (
            "<emoji document_id='5436162517686557387'>🚫</emoji> <b>Too many args</b>"
        ),
        "what_prefix": "❓ <b>What should the prefix be set to?</b>",
        "prefix_incorrect": (
            "<emoji document_id='5436162517686557387'>🚫</emoji> <b>Prefix must be one"
            " symbol in length</b>"
        ),
        "prefix_set": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Command prefix'
            " updated. Type</b> <code>{newprefix}setprefix {oldprefix}</code> <b>to"
            " change it back</b>"
        ),
        "alias_created": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Alias created.'
            " Access it with</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Aliases:</b>\n",
        "no_command": (
            "<emoji document_id='5436162517686557387'>🚫</emoji> <b>Command</b>"
            " <code>{}</code> <b>does not exist</b>"
        ),
        "alias_args": (
            "<emoji document_id='5436162517686557387'>🚫</emoji> <b>You must provide a"
            " command and the alias for it</b>"
        ),
        "delalias_args": (
            "<emoji document_id='5436162517686557387'>🚫</emoji> <b>You must provide the"
            " alias name</b>"
        ),
        "alias_removed": (
            '<emoji document_id="5368324170671202286">👍</emoji> <b>Alias</b>'
            " <code>{}</code> <b>removed</b>."
        ),
        "no_alias": (
            "<emoji document_id='5436162517686557387'>🚫</emoji> <b>Alias</b>"
            " <code>{}</code> <b>does not exist</b>"
        ),
        "db_cleared": (
            '<emoji document_id="5368324170671202286">👍</emoji><b> Database cleared</b>'
        ),
        "confirm_cleardb": "⚠️ <b>Are you sure, that you want to clear database?</b>",
        "cleardb_confirm": "🗑 Clear database",
        "cancel": "🚫 Cancel",
    }

    async def blacklistcommon(self, message: Message):
        args = utils.get_args(message)

        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args"))
            return

        chatid = None
        module = None

        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]

        if len(args) == 2:
            module = args[1]

        if chatid is None:
            chatid = utils.get_chat_id(message)

        module = self.allmodules.get_classname(module)
        return f"{str(chatid)}.{module}" if module else chatid

    async def getuser(self, message: Message):
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            reply = await message.get_reply_message()

            if reply:
                return reply.sender_id

            return message.to_id.user_id if message.is_private else False

    @loader.owner
    @loader.command(ru_doc="<префикс> - Установить префикс команд")
    async def setprefix(self, message: Message):
        """<prefix> - Sets command prefix"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args) != 1:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        oldprefix = self.get_prefix()
        self._db.set(main.__name__, "command_prefix", args)
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                newprefix=utils.escape_html(args[0]),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.owner
    @loader.command(ru_doc="Показать список алиасов")
    async def aliases(self, message: Message):
        """Print all your aliases"""
        aliases = self.allmodules.aliases
        string = self.strings("aliases")

        string += "\n".join(
            [f"▫️ <code>{i}</code> &lt;- {y}" for i, y in aliases.items()]
        )

        await utils.answer(message, string)

    @loader.owner
    @loader.command(ru_doc="Установить алиас для команды")
    async def addalias(self, message: Message):
        """Set an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 2:
            await utils.answer(message, self.strings("alias_args"))
            return

        alias, cmd = args
        if self.allmodules.add_alias(alias, cmd):
            self.set(
                "aliases",
                {
                    **self.get("aliases", {}),
                    alias: cmd,
                },
            )
            await utils.answer(
                message,
                self.strings("alias_created").format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_command").format(utils.escape_html(cmd)),
            )

    @loader.owner
    @loader.command(ru_doc="Удалить алиас для команды")
    async def delalias(self, message: Message):
        """Remove an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args"))
            return

        alias = args[0]
        removed = self.allmodules.remove_alias(alias)

        if not removed:
            await utils.answer(
                message,
                self.strings("no_alias").format(utils.escape_html(alias)),
            )
            return

        current = self.get("aliases", {})
        del current[alias]
        self.set("aliases", current)
        await utils.answer(
            message,
            self.strings("alias_removed").format(utils.escape_html(alias)),
        )

    @loader.owner
    @loader.command(ru_doc="Очистить базу данных")
    async def cleardb(self, message: Message):
        """Clear the entire database, effectively performing a factory reset"""
        await self.inline.form(
            self.strings("confirm_cleardb"),
            message,
            reply_markup=[
                {
                    "text": self.strings("cleardb_confirm"),
                    "callback": self._inline__cleardb,
                },
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
            ],
        )

    async def _inline__cleardb(self, call: InlineCall):
        self._db.clear()
        self._db.save()
        await utils.answer(call, self.strings("db_cleared"))
