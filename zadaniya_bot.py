import logging
import os
import time
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

# Открываем таблицу по названию
SHEET_NAME = "Задания Челленджа по REELS"
sheet = client.open(SHEET_NAME).sheet1  # используем первый лист

# Локальный подсчёт статистики
user_tasks = {}

# Храним последние сообщения от пользователей
last_messages = {}

@dp.message_handler(lambda message: "#задание" in message.text.lower())
async def handle_task(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    task_text = message.text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Проверка на повтор за последние 10 секунд
    current_time = time.time()
    if user_id in last_messages:
        last_text, last_time = last_messages[user_id]
        if task_text == last_text and (current_time - last_time) < 10:
            # Дубликат → просто игнорируем
            return

    # Сохраняем текущий текст и время
    last_messages[user_id] = (task_text, current_time)

    # Проверка на дубли в таблице (как раньше)
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

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
