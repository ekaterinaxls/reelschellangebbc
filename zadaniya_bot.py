import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Получаем токен из переменной окружения
API_TOKEN = os.getenv("API_TOKEN")

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Подключение к Google Таблице
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

# Открываем таблицу по названию (можно заменить на свою)
SHEET_NAME = "Задания Челленджа по REELS"
sheet = client.open(SHEET_NAME).sheet1  # используем первый лист

# Словарь для локального подсчёта статистики (опционально)
user_tasks = {}

@dp.message_handler(lambda message: "#задание" in message.text.lower())
async def handle_task(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    task_text = message.text
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Запись в Google Таблицу
    try:
        sheet.append_row([user_id, username, task_text, timestamp])
    except Exception as e:
        await message.reply(f"Ошибка при сохранении в таблицу: {e}")
        return

    # Подсчёт заданий
    if user_id not in user_tasks:
        user_tasks[user_id] = {"username": username, "count": 0}
    user_tasks[user_id]["count"] += 1

    await message.reply(f"✅ Задание принято!\nОбщее количество от @{username}: {user_tasks[user_id]['count']}")

@dp.message_handler(commands=["статистика"])
async def handle_stats(message: types.Message):
    if not user_tasks:
        await message.reply("Пока никто не отправлял задания 😢")
        return

    stats = "📊 Статистика по заданиям:\n\n"
    for user in user_tasks.values():
        stats += f"@{user['username']}: {user['count']} заданий\n"

    await message.reply(stats)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
