import asyncio
import os
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Linklarni aniqlash uchun
LINK_PATTERN = re.compile(
    r"(https?://|www\.|t.me|T.me|.ru|.com|.uz|telegram.me|t\.me/|telegram\.me/|@\w+)",
    re.IGNORECASE
)
BLACKLIST = [
    "minet",
    "porno",
    "kotmisan",
    "bukmeker",
    "am",
    "jalab",
    "jallab",
    "kot",
     "am",
    "aminga",
    "suka",
    "dalbayop",
    "suchara",
    "pidaraz",
    "ami",
    "qotagim",
]

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("🛡 Moderator Bot ishga tushdi!")


@dp.message(F.text)
async def check_links(message: Message):
    # Guruhdan tashqarida ishlamasin
    if message.chat.type not in ("group", "supergroup"):
        return

    # Adminlarni tekshirish
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)

    if member.status in ("administrator", "creator"):
        return
text = message.text.lower()

for word in BLACKLIST:
    if word in text:
        await message.delete()

        msg = await message.answer(
            f"🚫 {message.from_user.full_name}, taqiqlangan so'z ishlatdingiz!"
        )

        await asyncio.sleep(15)
        await msg.delete()
        return
        
        # Link topilsa
    if LINK_PATTERN.search(message.text):
        await message.delete()

        msg = await message.answer(
            f"🚫 {message.from_user.full_name}, guruhda link yuborish taqiqlangan!"
        )

        await asyncio.sleep(15)

        await msg.delete()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
