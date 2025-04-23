import logging
import os
import time
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.dispatcher.webhook import get_new_configured_app
from fastapi import FastAPI, Request
import uvicorn

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Токен и webhook URL
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://reelschellangebbc.onrender.com{WEBHOOK_PATH}"  # ← твой адрес


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Таблица
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
SHEET_NAME = "Задания Челленджа по REELS"
sheet = client.open(SHEET_NAME).sheet1

# Память о последних сообщениях
last_messages = {}
user_tasks = {}

# Бот-логика
@dp.message_handler(lambda message: "#задание" in message.text.lower())
async def handle_task(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    task_text = message.text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Проверка на повтор от одного юзера за 10 сек
    current_time = time.time()
    if user_id in last_messages:
        last_text, last_time = last_messages[user_id]
        if task_text == last_text and (current_time - last_time) < 10:
            return  # Просто игнорируем

    last_messages[user_id] = (task_text, current_time)

    try:
        existing_tasks = sheet.col_values(3)
    except Exception as e:
        await message.reply(f"❌ Ошибка при чтении таблицы: {e}")
        return

    if task_text in existing_tasks:
        await message.reply("🚨 Задание не принято, такой ответ уже был!")
        return

    try:
        sheet.append_row([user_id, username, task_text, timestamp])
    except Exception as e:
        await message.reply(f"❌ Ошибка при сохранении в таблицу: {e}")
        return

    if user_id not in user_tasks:
        user_tasks[user_id] = {"username": username, "count": 0}
    user_tasks[user_id]["count"] += 1

    await message.reply(f"✅ Задание принято!")

@dp.message_handler(commands=["статистика"])
async def handle_stats(message: types.Message):
    if not user_tasks:
        await message.reply("Пока никто не отправлял задания 😢")
        return

    stats = "📊 Статистика по заданиям:\n\n"
    for user in user_tasks.values():
        stats += f"@{user['username']}: {user['count']} заданий\n"

    await message.reply(stats)

# FastAPI-приложение
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.to_object(data)
    await dp.process_update(update)
    return {"ok": True}
