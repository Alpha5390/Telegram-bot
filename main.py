import logging
import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters import Command
import yt_dlp

import sys
import asyncio

TOKEN = "8183549397:AAHy3nETk7Zn7cJlzHUVX84fzqCWZf_zGC4"  
ADMIN_ID = 6646928202  

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

logging.basicConfig(level=logging.INFO)

CHANNELS_FILE = "channels.json"
USERS_FILE = "users.json"

def read_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] if file == CHANNELS_FILE else {}

def write_json(file, data):
    try:
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Faylga yozishda xatolik: {e}")

REQUIRED_CHANNELS = read_json(CHANNELS_FILE)
USERS = read_json(USERS_FILE)

async def check_subscription(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logging.error(f"Obunani tekshirishda xatolik: {e}")
            continue  
    return True

@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in USERS:
        USERS[user_id] = 0  
        write_json(USERS_FILE, USERS) 

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Guruhga qo‘shish", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true")]
        ]
    )

    await message.answer(
        "🔥 Assalomu alaykum! Bot orqali quyidagilarni yuklab olishingiz mumkin:\n\n"
        "• Instagram - Post, Istorya va Audio\n"
        "• YouTube - Video, Shorts va Audio\n\n"
        "🚀 Yuklab olmoqchi bo'lgan videoga havolani yuboring!",
        reply_markup=keyboard,
    )


@dp.message(Command("stats"))
async def get_stats(message: Message):
    if str(message.from_user.id) != str(ADMIN_ID):  
        await message.reply("❌ Siz admin emassiz!")
        return

    user_count = len(USERS)
    await message.reply(f"📊 Bot foydalanuvchilari soni: {user_count} ta")

@dp.message(F.text)
async def download_video(message: Message):
    user_id = str(message.from_user.id)
    url = message.text.strip()

    if not ("instagram.com" in url or "youtube.com" in url or "youtu.be" in url):
        await message.reply("❌ Iltimos, to‘g‘ri Instagram yoki YouTube havolasini yuboring!")
        return

    if not await check_subscription(user_id):
        await message.reply("❌ Iltimos, kanallarga obuna bo‘ling!")
        return

    USERS[user_id] = USERS.get(user_id, 0) + 1
    write_json(USERS_FILE, USERS)

    edit_1=await message.reply("⏳ Yuklab olish jarayoni boshlandi...")

    try:
        video_file = f"{user_id}_video.mp4"
        ydl_opts = {'format': 'best', 'outtmpl': video_file}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await asyncio.sleep(2)
        if os.path.exists(video_file):  
            edit_2=await bot.edit_message_text(chat_id=message.chat.id, message_id=edit_1.message_id, text="✅ Yuklab olish tugadi!")
            await asyncio.sleep(2)
            await bot.delete_message(chat_id=message.chat.id, message_id=edit_2.message_id)
            await asyncio.sleep(2)
            FILE = FSInputFile(video_file)  # Faylni o'qish va yuborish
            await message.reply_video(FILE, caption="✅ Yuklab olindi!")
        await asyncio.sleep(30)
        os.remove(video_file)  # Faylni o'chirish
    except yt_dlp.utils.DownloadError as e:
        await message.reply("❌ Xatolik: Fayl yuklab olinmadi:\n" + str(e))

    except Exception as e:
        logging.error(f"Yuklab olishda xatolik: {e}")
        await message.reply(f"❌ Xatolik: {e}")


async def main():
    await dp.start_polling(bot)

# Windows uchun asyncio muammosini hal qilish
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
if __name__ == "__main__":
    asyncio.run(main())