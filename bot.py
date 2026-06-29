import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import config
from database import init_db, add_user, get_user, get_messages, get_all_users
from telethon_client import start_client, stop_client

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

init_db()
temp_data = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Отправь /auth +79991234567")

@dp.message(Command("auth"))
async def auth(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используй: /auth +79991234567")
        return
    phone = args[1]
    temp_data[message.from_user.id] = {"phone": phone}
    await message.answer(f"Код отправлен на {phone}. Введи /code 12345")

@dp.message(Command("code"))
async def code(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Введи код: /code 12345")
        return
    code = args[1]
    user_id = message.from_user.id
    phone = temp_data.get(user_id, {}).get("phone")
    if not phone:
        await message.answer("Сначала отправь /auth")
        return

    session_string = f"session_{user_id}"
    add_user(user_id, phone, session_string)
    await message.answer("Авторизация успешна! Начинаю сбор.")
    asyncio.create_task(start_client(user_id, session_string))

@dp.message(Command("stats"))
async def stats(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Ты не авторизован.")
        return
    msgs = get_messages(message.from_user.id)
    await message.answer(f"Всего сообщений: {len(msgs)}")

@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Нет прав")
        return
    users = get_all_users()
    text = "Активные пользователи:\n" + "\n".join([f"{u[0]} - {u[1]}" for u in users])
    await message.answer(text)

@dp.message(Command("stop"))
async def stop(message: types.Message):
    await stop_client(message.from_user.id)
    await message.answer("Сбор остановлен.")

if __name__ == "__main__":
    dp.run_polling(bot)