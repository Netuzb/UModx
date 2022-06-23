import os
from telethon.tl.types import Message
from .. import loader, main, translations, utils
from ..inline.types import InlineCall


@loader.tds
class CoreMod(loader.Module):
    """Asosiy userbot sozlamalarini boshqaring"""

    strings = {
        "name": "Settings",
        "what_prefix": "◽ <b>Prefiks nimaga oʻzgartirilishi kerak?</b>",
        "prefix_incorrect": "◽ <b>Prefiks uzunligi bitta belgidan iborat bo'lishi kerak</b>",
        "prefix_set": "◽ <b>Buyruq prefiksi yangilandi.</b>\n◽ <b><u>Endilikda buyruq ishlatish</u> quyidagicha:</b>\n <code> — {newprefix}help\n — {newprefix}info\n — {newprefix}update...</code> \n\n◽ <b>Eski prefiks quyidagicha:</b> <code>{oldprefix}</code>",
        "db_cleared": "◽ <b>Ma'lumotlar bazasi tozalandi</b>",
        "lang_saved": "◽ <b><u>Premium-Userbot</u> tili muvaffaqiyatli oʻzgardi!</b>\n◽ <i><b>Oʻzgartirilgan</b> til kodi: {}</i>",
        "incorrect_language": "◽ <b>Tushunarsiz til!</b>\n◽ <i><b>Toʻgʻri til kiritganingizga</b> amin boʻling!</i>",
        "confirm_cleardb": "◽ <b><u>Maʼlumotlar bazasini</u> tozalamoqchi ekanligingizga ishonchingiz komilmi? Iltimos, tasdiqlang.</b>",
        "cleardb_confirm": "◽Ha // Toʻliq",
        "cancel": "◽ Bekor qilish",
    }

    strings_ru = {
        "what_prefix": "◽ <b>А какой префикс ставить то?</b>",
        "prefix_incorrect": "◽ <b>Префикс должен состоять только из одного символа</b>",
        "prefix_set": "◽ <b>Префикс команды был обновлен.</b>\n◽ <b><u>Теперь используйте команду</u> следующим образом:</b> \n<code> — {newprefix}help\n — {newprefix}info\n — {newprefix}update...</code> \n\n◽ <b>Старый префикс выглядит следующим образом:</b> <code>{oldprefix}</code>",
        "lang_saved": "◽ <b>Язык <u>Premium-Userbot</u> успешно изменен!</b>\n◽ <i><b>Изменено</b> на: {}</i>",
        "incorrect_language": "◽ <b>Указан неверный язык</b>\n◽ <i>Убедитесь, что вы вводите <b>правильный язык!</b></i>",
        "_cmd_doc_setprefix": "<префикс> - Установить префикс",
        "_cmd_doc_setlang": "Выбрать предпочитаемый язык перевода\nТребуется перезагрузка после выполнения",
        "_cmd_doc_cleardb": "Сброс до заводских настроек - сброс базы данных",
        "_cls_doc": "Управление базовыми настройками юзербота",
        "confirm_cleardb": "◽ <b>Вы уверены, что хотите сбросить <u>базу данных? Подтвердите пожалуйста!</u></b>",
        "cleardb_confirm": "◽ Очистить базу",
        "cancel": "◽ Отмена",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    @loader.owner
    async def setprefixcmd(self, message: Message):
        """<prefiks> - buyruq prefiksini o'rnatadi"""
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

    async def setlangcmd(self, message: Message):
        """[til] - Standart tilni o'zgartirish"""
        args = utils.get_args_raw(message)
        if not args or len(args) != 2:
            await utils.answer(message, self.strings("incorrect_language"))
            return

        possible_pack_path = os.path.join(
            utils.get_base_dir(),
            f"langpacks/{args.lower()}.json",
        )

        if os.path.isfile(possible_pack_path):
            self._db.set(translations.__name__, "pack", args.lower())

        self._db.set(translations.__name__, "lang", args.lower())
        await self.translator.init()

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                utils.get_lang_flag(args.lower() if args.lower() != "en" else "gb")
            ) + f" <code>{args}</code>",
        )

    @loader.owner
    async def cleardbcmd(self, message: Message):
        """Zavod sozlamalarini tiklashni samarali amalga oshirib, butun ma'lumotlar bazasini tozalaydi"""
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
