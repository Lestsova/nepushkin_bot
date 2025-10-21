import logging
import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Загружаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Проверка токена
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в переменных окружения Render!")

bot = Bot(token=BOT_TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot)

# --- Хранение состояний ---
user_data = {}

# --- Кнопки выбора формата ---
kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(
    KeyboardButton("📜 Пирожок"),
    KeyboardButton("🧪 Порошок"),
    KeyboardButton("🕯 Депрессяшок"),
    KeyboardButton("✍️ Экспромт"),
)

# --- Команда /start ---
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    text = (
        "👋 Добро пожаловать в бот канала *«Это вам не Пушкин»*!\n\n"
        "Выберите формат стиха, который хотите отправить:"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

# --- Выбор формата ---
@dp.message_handler(lambda msg: msg.text in ["📜 Пирожок", "🧪 Порошок", "🕯 Депрессяшок", "✍️ Экспромт"])
async def choose_format(message: types.Message):
    user_data[message.from_user.id] = {"format": message.text}
    await message.answer("✍️ Введите ваш стих:")

# --- Получение текста стиха ---
@dp.message_handler(lambda msg: msg.from_user.id in user_data and "text" not in user_data[msg.from_user.id])
async def get_text(message: types.Message):
    user_data[message.from_user.id]["text"] = message.text
    await message.answer("📛 Укажите имя автора или напишите *Анонимно*:", parse_mode="Markdown")

# --- Получение имени ---
@dp.message_handler(lambda msg: msg.from_user.id in user_data and "author" not in user_data[msg.from_user.id])
async def get_author(message: types.Message):
    user_data[message.from_user.id]["author"] = message.text
    data = user_data[message.from_user.id]

    preview = (
        f"📝 *Проверьте данные перед отправкой:*\n\n"
        f"{data['format']}\n\n"
        f"{data['text']}\n\n"
        f"👤 Автор: _{data['author']}_"
    )

    kb_confirm = ReplyKeyboardMarkup(resize_keyboard=True)
    kb_confirm.add(KeyboardButton("✅ Отправить"), KeyboardButton("❌ Отменить"))

    await message.answer(preview, parse_mode="Markdown", reply_markup=kb_confirm)

# --- Подтверждение ---
@dp.message_handler(lambda msg: msg.text in ["✅ Отправить", "❌ Отменить"])
async def confirm(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        await message.answer("⚠️ Нет данных для отправки. Начните заново: /start")
        return

    if message.text == "❌ Отменить":
        del user_data[user_id]
        await message.answer("🚫 Отменено. Чтобы начать заново, введите /start", reply_markup=kb)
        return

    data = user_data[user_id]
    text_to_send = f"{data['format']}\n\n{data['text']}\n\n👤 Автор: _{data['author']}_"

    await bot.send_message(CHANNEL_ID, text_to_send, parse_mode="Markdown")
    await message.answer("✨ Спасибо 🙏  Ваш стих отправлен на рассмотрение! Возвращайтесь, когда будет вдохновение!✨", reply_markup=kb)

    del user_data[user_id]

# --- Keep Alive для Render ---
async def keep_alive():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        return
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    logging.info(f"🔄 Pinged {url} — status {resp.status}")
        except Exception as e:
            logging.error(f"Ошибка ping: {e}")
        await asyncio.sleep(600)  # каждые 10 минут

# --- Webhook ---
async def on_startup(dp):
    url = os.getenv("RENDER_EXTERNAL_URL")
    if url:
        webhook_url = f"{url}/webhook"
        await bot.set_webhook(webhook_url)
        logging.info(f"✅ Webhook установлен: {webhook_url}")
        asyncio.create_task(keep_alive())

# --- Обработка webhook запросов ---
async def handle_webhook(request):
    data = await request.json()
    update = types.Update.to_object(data)
    await dp.process_update(update)
    return web.Response()

# --- Запуск сервера aiohttp ---
async def main():
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

    await on_startup(dp)
    logging.info("🤖 Бот запущен и готов к работе 24/7!")

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
