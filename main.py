
import asyncio
import os
import re
import asyncpg

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated


TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OWNER_ID = 711427177

bot = Bot(token=TOKEN) if TOKEN else None
dp = Dispatcher()
pool = None

last_chat_message = {}
repeat_count = {}

LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me|telegram\.me|@\w+|[a-zA-Z0-9_-]+\.(ru|com|uz))",
    re.IGNORECASE
)

BLACKLIST = [
    "ам", "am", "ami", "a.m", "ами", "aminga", "a@m",
    "a#m", "a_m", "а_м", "а*м", "amman", "porno",
    "kotmisan", "кутагим", "jalab", "jallab", "kot",
    "куток", "suka", "dalbayop", "suchara", "pidaraz",
    "qotagim", "seks", "sikihsamiz", "kotimga", "amimga",
    "oneni", "ski", "сикади", "секс", "sikadi", "сикишади",
    "sikishadi", "жалаб", "ски", "котогим", "кото", "qoto",
    "quto", "qutogim", "qotogim", "nastroy", "nastroyga",
    "skay", "скай", "котла", "порно", "настрой",
    "настройга", "куто", "кутла", "yiban", "dalbayobla",
    "yibanla", "сиктираман", "qotogimmi", "dalbayob",
    "siktiraman", "кутток", "кутоо", "kotto", "junli",
    "kutoq", "qotogimi", "xuy", "хуй", "сикиш", "sikish",
    "naxuy", "nаxuy", "нахуй", "qottogi", "куттоги"
]


# ================ DATABASE ================

async def init_db():
    global pool

    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY,
                full_name TEXT,
                username TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups(
                chat_id BIGINT PRIMARY KEY,
                title TEXT
            )
        """)


async def save_user(user):
    if user is None:
        return

    async with pool.acquire() as db:
        await db.execute("""
            INSERT INTO users(user_id, full_name, username)
            VALUES($1, $2, $3)
            ON CONFLICT(user_id)
            DO UPDATE SET
                full_name = EXCLUDED.full_name,
                username = EXCLUDED.username
        """, user.id, user.full_name, user.username)


async def save_group(chat):
    async with pool.acquire() as db:
        result = await db.execute("""
            INSERT INTO groups(chat_id, title)
            VALUES($1, $2)
            ON CONFLICT(chat_id)
            DO UPDATE SET title = EXCLUDED.title
        """, chat.id, chat.title or "Nomsiz guruh")

        return result == "INSERT 0 1"


# ================ START ================

@dp.message(Command("start"))
async def start(message: Message):
    if message.from_user:
        await save_user(message.from_user)

    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Men Yordamchi botman. 🛡\n\n"
        "🚫 Spam va flood nazorati\n"
        "🔗 Reklama va havolalar\n"
        "🤬 Nomaqbul so'zlar\n"
        "♻️ Takroriy xabarlar\n"
        "🚪 Kirish-chiqish xabarlarini o'chirish\n\n"
        "To'liq ishlashim uchun meni guruhga administrator qiling "
        "va xabarlarni o'chirish huquqini bering."
    )

    if message.chat.type == "private":
        try:
            await bot.send_message(
                OWNER_ID,
                f"🆕 Yangi foydalanuvchi\n\n"
                f"👤 Ism: {message.from_user.full_name}\n"
                f"🆔 ID: {message.from_user.id}\n"
                f"📛 Username: @{message.from_user.username or 'yo‘q'}"
            )
        except Exception as e:
            print(f"Owner xabari: {e}")


# ================ BOT GURUHGA QO'SHILISHI ================

@dp.my_chat_member()
async def bot_added(event: ChatMemberUpdated):
    if event.chat.type not in ("group", "supergroup"):
        return

    status = event.new_chat_member.status

    if status in ("member", "administrator"):
        new = await save_group(event.chat)

        if new:
            try:
                await bot.send_message(
                    OWNER_ID,
                    f"🆕 Bot yangi guruhga qo'shildi\n\n"
                    f"👥 Guruh: {event.chat.title}\n"
                    f"🆔 ID: {event.chat.id}"
                )
            except Exception as e:
                print(f"Owner xabari: {e}")


# ================ KIRISH-CHIQISH XABARLARINI O'CHIRISH ================

@dp.message(F.new_chat_members)
async def delete_join_message(message: Message):
    try:
        await message.delete()
        print(f"✅ Kirish xabari o'chirildi: {message.chat.id}")
    except Exception as e:
        print(f"❌ Kirish xabarini o'chirish xatosi: {e}")


@dp.message(F.left_chat_member)
async def delete_leave_message(message: Message):
    try:
        await message.delete()
        print(f"✅ Chiqish xabari o'chirildi: {message.chat.id}")
    except Exception as e:
        print(f"❌ Chiqish xabarini o'chirish xatosi: {e}")


# ================ E'LON YUBORISH ================

async def send_to_groups(message: Message):
    async with pool.acquire() as db:
        groups = await db.fetch("SELECT chat_id FROM groups")

    success = 0
    failed = 0

    for group in groups:
        chat_id = group["chat_id"]

        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )

            elif message.video:
                await bot.send_video(
                    chat_id=chat_id,
                    video=message.video.file_id,
                    caption=message.caption
                )

            elif message.document:
                await bot.send_document(
                    chat_id=chat_id,
                    document=message.document.file_id,
                    caption=message.caption
                )

            elif message.text:
                text = message.text.replace("/elon", "", 1).strip()

                if not text:
                    continue

                await bot.send_message(chat_id, text)

            else:
                continue

            success += 1

        except Exception as e:
            failed += 1
            print(f"❌ E'lon yuborilmadi {chat_id}: {e}")

    await message.answer(
        f"✅ E'lon yuborildi\n\n"
        f"📢 Muvaffaqiyatli: {success}\n"
        f"❌ Xato: {failed}"
    )


@dp.message(Command("elon"))
async def text_elon(message: Message):
    if message.from_user and message.from_user.id == OWNER_ID:
        await send_to_groups(message)


@dp.message(F.photo | F.video | F.document)
async def media_elon(message: Message):
    if message.from_user and message.from_user.id == OWNER_ID:
        await send_to_groups(message)


# ================ MODERATOR ================

@dp.message(F.text)
async def moderator(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    if not message.from_user:
        return

    await save_group(message.chat)
    await save_user(message.from_user)

    try:
        member = await bot.get_chat_member(
            message.chat.id,
            message.from_user.id
        )

        if member.status in ("administrator", "creator"):
            return

    except Exception as e:
        print(f"Adminni tekshirish xatosi: {e}")
        return

    text = message.text.lower().strip()
    chat_id = message.chat.id
    user_id = message.from_user.id

    last = last_chat_message.get(chat_id)

    # Ketma-ket bir xil xabar
    if (
        last
        and last["user_id"] == user_id
        and last["text"] == text
    ):
        key = (chat_id, user_id)
        repeat_count[key] = repeat_count.get(key, 0) + 1

        try:
            await message.delete()

            if repeat_count[key] == 1:
                warn = await message.answer(
                    f"🚫 {message.from_user.full_name}, "
                    "ketma-ket bir xil xabar yubormang!"
                )
                await asyncio.sleep(7)
                await warn.delete()

        except Exception as e:
            print(f"Takroriy xabar xatosi: {e}")

        return

    last_chat_message[chat_id] = {
        "user_id": user_id,
        "text": text
    }
    repeat_count[(chat_id, user_id)] = 0

    # Nomaqbul so'zlar
    for word in BLACKLIST:
        if re.search(
            rf"\b{re.escape(word)}\b",
            text,
            re.IGNORECASE
        ):
            try:
                await message.delete()
                warn = await message.answer(
                    f"🚫 {message.from_user.full_name}, "
                    "odobsiz so'z yozmang!"
                )
                await asyncio.sleep(7)
                await warn.delete()

            except Exception as e:
                print(f"Nomaqbul xabar xatosi: {e}")

            return

    # Havolalar
    clean = re.sub(r"\s+", "", text)

    if LINK_PATTERN.search(clean):
        try:
            await message.delete()
            warn = await message.answer(
                f"🚫 {message.from_user.full_name}, "
                "guruhga ruxsatsiz havola yubormang!"
            )
            await asyncio.sleep(7)
            await warn.delete()

        except Exception as e:
            print(f"Havola xatosi: {e}")


# ================ RUN ================

async def main():
    if not TOKEN:
        raise RuntimeError("Railway Variables ichida BOT_TOKEN yo'q!")

    if not DATABASE_URL:
        raise RuntimeError("Railway Variables ichida DATABASE_URL yo'q!")

    await init_db()

    print("🤖 Bot ishga tushmoqda...")

    await dp.start_polling(
        bot,
        allowed_updates=[
            "message",
            "my_chat_member",
            "chat_member"
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
