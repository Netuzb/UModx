import asyncio
import logging
from ..inline.types import InlineCall, BotInlineMessage
from .. import loader, utils


PRESETS = {
    "wilsonmods": [
        "https://github.com/thomasmod/hikkamods/raw/main/cdeanon.py",
        "https://raw.githubusercontent.com/thomasmod/hikkamods/main/atelegraph.py",
        "https://raw.githubusercontent.com/thomasmod/hikkamods/main/cmovies.py",
        "https://raw.githubusercontent.com/thomasmod/hikkamods/main/cchid.py",
        "https://raw.githubusercontent.com/thomasmod/hikkamods/main/crename.py",
        "https://raw.githubusercontent.com/thomasmod/hikkamods/main/ctiktok.py",
        "https://raw.githubusercontent.com/thomasmod/hikkamods/main/cuploader.py",
        "https://raw.githubusercontent.com/thomasmod/hikkamods/main/kursinfo.py",        
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/mydiary.py",
    ],
    "amoremods": [
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/abstract.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/amoreinfo.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/autoprofile.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/animevoices.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/bull.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/createlinks.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/funquotes.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/hacker.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/imgbb.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/instasave.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/meowvoices.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/mydiary.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/searchpic.py",
        "https://raw.githubusercontent.com/AmoreForever/amoremods/master/telegraphup.py",
    ],
}

@loader.tds
class ThomPresets(loader.Module):
    """Modullar jamlangan bepul doʻkon"""

    strings = {
        "name": "ThomPresets",
        "_wilsonmods_title": "🔥 Thomas modullar",
        "_wilsonmods_desc": "«UModx» yaratuvchisining rasmiy modullari quyida joylashgan",
        "_amoremods_title": "🔥 AmoreForever modullar",
        "_amoremods_desc": "Fazliddin‘ boshchiligida tuzilgan rasmiy modullari",
        "welcome": "🌟 Salom! Bu <b>«UModx»</b> modullar doʻkoni",
        "preset": (
            "<b>{}:</b>\n🚨 <b>Info:</b> <i>{}</i>\n\n🗃️ <b>Ushbu katalogdagi modullar:</b>\n\n{}"
        ),    
        "installing": (
            "<emoji document_id='5451732530048802485'>⏳</emoji> <b>Umumiy hisobda"
            " </b><code>{}</code><b>...</b>"
        ),
        "installing_module": (
            "<emoji document_id='5451732530048802485'>⏳</emoji> <b>oʻrnatilmoqda..."
            " </b><code>{}</code><b> ({}/{} modullar)...</b>\n\n<emoji"
            " document_id='5373141891321699086'>😎</emoji> <i>"
            " {}...</i>"
        ),
        "installed": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Umumiy hisobda"
            " </b><code>{}</code><b> oʻrnatildi!</b>"
        ),
        "back": "↩️ Orqaga",
        "install": "💾️ O'rnatish",
        "already_installed": "✅ [Oʻrnatildi]",
    }

    async def client_ready(self):
        self._markup = utils.chunks(
            [
                {
                    "text": self.strings(f"_{preset}_title"),
                    "callback": self._preset,
                    "args": (preset,),
                }
                for preset in PRESETS
            ],
            1,
        )

        if self.get("sent"):
            return

        self.set("sent", True)

        await self._menu()

    async def _menu(self):
        await self.inline.bot.send_message(
            self._client.tg_id,
            self.strings("welcome"),
            reply_markup=self.inline.generate_markup(self._markup),
        )

    async def _back(self, call: InlineCall):
        await call.edit(self.strings("welcome"), reply_markup=self._markup)

    async def _install(self, call: InlineCall, preset: str):
        await call.delete()
        m = await self._client.send_message(
            self.inline.bot_id, self.strings("installing").format(preset)
        )
        for i, module in enumerate(PRESETS[preset]):
            await m.edit(
                self.strings("installing_module").format(
                    preset, i, len(PRESETS[preset]), module
                )
            )
            await self.lookup("loader").download_and_install(module, None)
            await asyncio.sleep(1)

        if self.lookup("loader")._fully_loaded:
            self.lookup("loader")._update_modules_in_db()

        await m.edit(self.strings("installed").format(preset))
        await self._menu()

    def _is_installed(self, link: str) -> bool:
        return any(
            link.strip().lower() == installed.strip().lower()
            for installed in self.lookup("loader").get("loaded_modules", {}).values()
        )

    async def _preset(self, call: InlineCall, preset: str):
        await call.edit(
            self.strings("preset").format(
                self.strings(f"_{preset}_title"),
                self.strings(f"_{preset}_desc"),
                "\n".join(
                    map(
                        lambda x: x[0],
                        sorted(
                            [
                                (
                                    f"{self.strings('already_installed') if self._is_installed(link) else '▫️'} <b>{link.rsplit('/', maxsplit=1)[1].split('.')[0]}</b>",
                                    int(self._is_installed(link)),
                                )
                                for link in PRESETS[preset]
                            ],
                            key=lambda x: x[1],
                            reverse=True,
                        ),
                    )
                ),
            ),
            reply_markup=[
                {"text": self.strings("back"), "callback": self._back},
                {
                    "text": self.strings("install"),
                    "callback": self._install,
                    "args": (preset,),
                },
            ],
        )

    async def aiogram_watcher(self, message: BotInlineMessage):
        if message.text != "/modullar" or message.from_user.id != self._client.tg_id:
            return

        await self._menu()
