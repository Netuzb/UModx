import logging
import re
import string
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.types import Message
from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class InlineStuffMod(loader.Module):
    """Inline botni oʻzgartirish"""

    strings = {
        "name": "InlineChange",
        "bot_username_invalid": "◽ <b>Ko'rsatilgan bot foydalanuvchi nomi noto'g'ri. U </b><code>bot</code><b> bilan tugashi va kamida 4 ta belgi</b>ni o'z ichiga olishi kerak.",
        "bot_username_occupied": "◽ <b>Ushbu foydalanuvchi nomi allaqachon band</b>",
        "bot_updated": "◽ <b>Konfiguratsiya muvaffaqiyatli saqlandi. O'zgarishlarni qo'llash uchun userbotni qayta ishga tushiring</b>",
    }

    strings_ru = {
        "bot_username_invalid": "◽ <b>Неправильный ник бота. Он должен заканчиваться на </b><code>bot</code><b> и быть не короче чем 5 символов</b>",
        "bot_username_occupied": "◽ <b>Такой ник бота уже занят</b>",
        "bot_updated": "◽ <b>Настройки сохранены. Для их применения нужно перезагрузить юзербот</b>",
        "_cmd_doc_ch_hikka_bot": "<username> - Изменить юзернейм инлайн бота",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def watcher(self, message: Message):
        if (
            getattr(message, "out", False)
            and getattr(message, "via_bot_id", False)
            and message.via_bot_id == self.inline.bot_id
            and "This message will be deleted automatically"
            in getattr(message, "raw_text", "")
        ):
            await message.delete()
            return

        if (
            not getattr(message, "out", False)
            or not getattr(message, "via_bot_id", False)
            or message.via_bot_id != self.inline.bot_id
            or "premium gallery..." not in getattr(message, "raw_text", "")
        ):
            return

        id_ = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text).group(1)

        await message.delete()

        m = await message.respond("<b>◽ premium gallery...</b>")

        await self.inline.gallery(
            message=m,
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
            force_me=self.inline._custom_map[id_].get("force_me", False),
            disable_security=self.inline._custom_map[id_].get(
                "disable_security", False
            ),
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    async def change_inlinecmd(self, message: Message):
        """<username> - Premium inline bot foydalanuvchi nomini oʻzgartirish"""
        args = utils.get_args_raw(message).strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(
                litera not in (string.ascii_letters + string.digits + "_")
                for litera in args
            )
        ):
            await utils.answer(message, self.strings("bot_username_invalid"))
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings("bot_username_occupied"))
                return

        self._db.set("hikka.inline", "custom_bot", args)
        self._db.set("hikka.inline", "bot_token", None)
        await utils.answer(message, self.strings("bot_updated"))
