import logging
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = '7710777066:AAFAboiPrQh346uDox7ldzadGZsI8FOiKRY'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_tasks = {}

@dp.message_handler(lambda message: "#задание" in message.text.lower())
async def handle_task(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    if user_id not in user_tasks:
        user_tasks[user_id] = {"username": username, "count": 0}

    user_tasks[user_id]["count"] += 1
    await message.reply(f"Задание принято! Общее количество от @{username}: {user_tasks[user_id]['count']}")

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
