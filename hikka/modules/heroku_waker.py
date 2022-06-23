import logging
import os

try:
    import redis
except ImportError as e:
    if "DYNO" in os.environ:
        raise e

from telethon.tl.types import Message
from .. import loader, main, utils, heroku

logger = logging.getLogger(__name__)


@loader.tds
class HerokuMod(loader.Module):
    """Stuff related to Hikka Heroku installation"""

    strings = {
        "name": "Heroku",
        "redisdocs": (
            "🥡 <b>Redis ma'lumotlar bazasi</b>\n\n"
            "🇷🇺 <b>Agar siz Rossiyadan bo'lsangiz yoki shunchaki tashqi xizmatdan foydalanmoqchi bo'lsangiz:</b>\n"
            "1. https://redis.com ga kiring\n"
            "2. Hisob qaydnomasini ro'yxatdan o'tkazing\n"
            "3. Ma'lumotlar bazasi namunasini yarating\n"
            "4. Redis ma'lumotlar bazasi URL manzilini orqali kiriting <code>.setredis &lt;redis_url&gt;</code>\n"
            "<i>💡 Namuna: URL tuzilishi <code>redis://:PASSWORD@ENDPOINT</code></i>\n\n"
            "♓️ <b>Agar siz Rossiyadan bo'lmasangiz, shunchaki yoqing </b><code>heroku-redis</code><b>. Ushbu harakat uchun Heroku hisobini tekshirish talab qilinadi!</b>"
        ),
        "url_invalid": "🚫 <b>URL noto‘g‘ri ko‘rsatilgan</b>",
        "url_saved": "✅ <b>URL saqlandi</b>",
    }

    strings_ru = {
        "redisdocs": (
            "🥡 <b>База данных Redis</b>\n\n"
            "🇷🇺 <b>Если ты из России, или просто хочешь использовать внешний сервис:</b>\n"
            "1. Перейди на https://redis.com\n"
            "2. Зарегистрируйся\n"
            "3. Создай базу данных\n"
            "4. Введи Database URL в <code>.setredis &lt;redis_url&gt;</code>\n"
            "<i>💡 Подсказка: URL выглядит так: <code>redis://:PASSWORD@ENDPOINT</code></i>\n\n"
            "♓️ <b>Если ты не из России, можешь просто активировать плагин </b><code>heroku-redis</code><b> в Hikka app Heroku. Для этого тебе нужно будет верифицировать аккаунт</b>"
        ),
        "url_invalid": "🚫 <b>Указан неверный URL</b>",
        "url_saved": "✅ <b>URL сохранен</b>",
    }

    async def client_ready(self, client, db):

        self._db = db
        self._client = client
        self._bot = "@WebpageBot"

        if "DYNO" not in os.environ:
            raise loader.SelfUnload

        await utils.dnd(client, self._bot, True)

        self._heroku_url = heroku.get_app(api_token=main.hikka.api_token)[0].web_url
        self._heroku_pinger.start()

    async def setrediscmd(self, message: Message):
        """<redis_url> - Set Redis Database URL"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("redisdocs"))
            return

        try:
            redis.from_url(args)
        except Exception:
            await utils.answer(message, self.strings("url_invalid"))
            return

        main.save_config_key("redis_uri", args)
        await self._db.redis_init()
        await self._db.remote_force_save()
        await utils.answer(message, self.strings("url_saved"))

    @loader.loop(interval=20 * 60, wait_before=True)
    async def _heroku_pinger(self):
        """Sends request to Heroku webapp through WebpageBot"""
        async with self._client.conversation(self._bot) as conv:
            m = await conv.send_message(self._heroku_url)
            r = await conv.get_response()
            await m.delete()
            await r.delete()
