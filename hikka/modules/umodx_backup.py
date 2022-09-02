__version__ = (2, 1, 4)

#            ▀█▀ █ █ █▀█ █▀▄▀█ ▄▀█ █▀
#             █  █▀█ █▄█ █ ▀ █ █▀█ ▄█  
#             https://t.me/netuzb
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import datetime
import io
import json
import logging
import time
from telethon.tl.types import Message
from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

soso = "◽ "
premium = """🌟 <b>«<u>UModx</u>»</b> - zamonaviy qatlamga xush kelibsiz!
◽ <b>«Maʼlumot oʻrnida»</b> - <u>UModx</u> yangilanishlari sizga bildirishnoma orqali yetib keladi

◽ .help - <b>barcha mavjud modullar</b>
◽ /start - <b>yuzerbot haqida maʼlumot</b>
◽ /modullar - <b>modullar doʻkoni</b>"""

@loader.tds
class BackupMod(loader.Module):
    """Automatic database backup"""

    strings = {
        "name": "Backup",
        "soso_hecham": "— bekor qilish —",
        "period": premium + "\n\n◽ <b>Quyidagi «Premium-Userbot»</b> backuper.\n◽ Backup uchun qulay vaqtni belgilang (soatda).",
        "saved": soso + "<b>Backup davri saqlandi!</b> Siz uni keyinroq qayta sozlash uchun quyidagicha ishlating: <code>.set_backup_period</code>",
        "never": soso + "<b>Men avtomatik backup nusxalarini yaratmayman.</b> Siz uni keyinroq qayta sozlashingiz mumkin: <code>.set_backup_period</code>",
        "invalid_args": soso + "<b>To'g'ri backup davrini soatlarda yoki o'chirish uchun «0» ni belgilang</b>",
    }

    strings_ru = {
        "period": "◽ <b>Это «Premium-Userbot»</b> бэкапер.\n◽ Установите время для бэкапа (в часах). ",
        "soso_hecham": soso + "отменить",    
        "saved": soso + "<b>Периодичность сохранена!</b> Ее можно изменить с помощью: <code>.set_backup_period</code>",
        "never": soso + "Я не буду делать автоматические резервные копии. Можно отменить используя .set_backup_period",
        "invalid_args": soso + "<b>Укажи правильную периодичность в часах, или `0` для отключения</b>",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        if not self.get("period"):
            await self.inline.bot.send_photo(
                self._tg_id,
                photo="http://f0664355.xsph.ru/img/info_post.png",
                caption=self.strings("period"),
                reply_markup=self.inline.generate_markup(
                    utils.chunks(
                        [
                            {"text": f"«{i} soat»", "data": f"backup_period/{i}"}
                            for i in {1, 2, 4, 6, 8, 12, 24, 48, 168}
                        ],
                        3,
                    )
                    + [[{"text": f"{self.strings('soso_hecham')}", "data": "backup_period/never"}]]
                ),
            )

        self._backup_channel, _ = await utils.asset_channel(
            self._client,
            "Premium",
            ".",
            silent=True,
            archive=True,
            avatar="http://f0664355.xsph.ru/img/new_avatar.png",
            _folder="premium",
        )

        self.handler.start()

    async def backup_period_callback_handler(self, call: InlineCall):
        if not call.data.startswith("backup_period"):
            return

        if call.data == "backup_period/never":
            self.set("period", "disabled")
            await call.answer(self.strings("never"), show_alert=True)

            await self.inline.bot.delete_message(
                call.message.chat.id,
                call.message.message_id,
            )
            return

        period = int(call.data.split("/")[1]) * 60 * 60

        self.set("period", period)
        self.set("last_backup", round(time.time()))

        await call.answer(self.strings("saved"), show_alert=True)

        await self.inline.bot.delete_message(
            call.message.chat.id,
            call.message.message_id,
        )

    async def set_backup_periodcmd(self, message: Message):
        """<time in hours> - Change backup frequency"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit() or int(args) not in range(200):
            await utils.answer(message, self.strings("invalid_args"))
            return

        if not int(args):
            self.set("period", "disabled")
            await utils.answer(message, f"<b>{self.strings('never')}</b>")
            return

        period = int(args) * 60 * 60
        self.set("period", period)
        self.set("last_backup", round(time.time()))
        await utils.answer(message, f"<b>{self.strings('saved')}</b>")

    @loader.loop(interval=1)
    async def handler(self):
        try:
            if not self.get("period"):
                await asyncio.sleep(3)
                return

            if not self.get("last_backup"):
                self.set("last_backup", round(time.time()))
                await asyncio.sleep(self.get("period"))
                return

            if self.get("period") == "disabled":
                raise loader.StopLoop

            await asyncio.sleep(
                self.get("last_backup") + self.get("period") - time.time()
            )

            backup = io.BytesIO(json.dumps(self._db).encode("utf-8"))
            backup.name = f"premium-usernot-db-backup-{getattr(datetime, 'datetime', datetime).now().strftime('%d-%m-%Y-%H-%M')}.json"

            await self._client.send_file(
                self._backup_channel,
                backup,
            )
            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("HikkaBackup failed")
            await asyncio.sleep(60)
