import asyncio
import os
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 711427177
ALLOWED_GROUPS = {
    -5153035696,
    -1002222222222,
    -1003333333333,
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Faqat bir marta xabar yuborish uchun
KNOWN_USERS = set()
KNOWN_GROUPS = set()

# Linklarni aniqlash uchun
LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me|telegram\.me|@\w+|[a-zA-Z0-9_-]+\.(ru|com|uz))",
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

    if message.chat.type == "private":
        if message.from_user.id not in KNOWN_USERS:
            KNOWN_USERS.add(message.from_user.id)

            await bot.send_message(
                OWNER_ID,
                f"""🆕 Yangi foydalanuvchi

👤 Ism: {message.from_user.full_name}
🆔 ID: {message.from_user.id}
📛 Username: @{message.from_user.username if message.from_user.username else "yo'q"}"""
            )


@dp.message(F.text)
async def check_links(message: Message):
    # Guruhdan tashqarida ishlamasin
    if message.chat.type not in ("group", "supergroup"):
        return

    # Yangi guruh haqida faqat bir marta xabar berish
    if message.chat.id not in KNOWN_GROUPS:
        KNOWN_GROUPS.add(message.chat.id)

        await bot.send_message(
            OWNER_ID,
            f"""🆕 Bot yangi guruhga qo'shildi

👥 Guruh: {message.chat.title}
🆔 Chat ID: {message.chat.id}"""
        )

    # Adminlarni tekshirish
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)

    if member.status in ("administrator", "creator"):
        return

    text = message.text.lower()
    clean_text = re.sub(r"\s+", "", text)

    # Qora ro'yxatdagi so'zlarni tekshirish
    for word in BLACKLIST:
        if word in text:
            await message.delete()

            msg = await message.answer(
                f"🚫 {message.from_user.full_name}, taqiqlangan so'z ishlatdingiz!"
            )

            await asyncio.sleep(5)
            await msg.delete()
            return

    # Link topilsa
    if LINK_PATTERN.search(clean_text):
        await message.delete()

        msg = await message.answer(
            f"🚫 {message.from_user.full_name}, guruhda link yuborish taqiqlangan!"
        )

        await asyncio.sleep(5)
        await msg.delete()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
