import asyncio
from telethon import TelegramClient, events
from database import save_message
import config

clients = {}

async def start_client(user_id, session_string):
    client = TelegramClient(session_string, config.API_ID, config.API_HASH)
    await client.start()
    clients[user_id] = client

    @client.on(events.NewMessage)
    async def handler(event):
        if event.message.text:
            save_message(user_id, event.message.text, event.chat_id, event.sender_id)

    await client.run_until_disconnected()

async def stop_client(user_id):
    if user_id in clients:
        await clients[user_id].disconnect()
        del clients[user_id]