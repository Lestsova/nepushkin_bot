from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import os

API_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class PoemForm(StatesGroup):
    format = State()
    text = State()
    author = State()
    confirm = State()

format_keyboard = InlineKeyboardMarkup(row_width=2)
format_keyboard.add(
    InlineKeyboardButton("📜 Пирожок", callback_data="format_pirozhok"),
    InlineKeyboardButton("💊 Порошок", callback_data="format_poroshek"),
    InlineKeyboardButton("🌧 Депрессяшок", callback_data="format_depress"),
    InlineKeyboardButton("🎭 Экспромт", callback_data="format_exprompt"),
)

confirm_keyboard = InlineKeyboardMarkup(row_width=2)
confirm_keyboard.add(
    InlineKeyboardButton("✅ Всё верно — отправить", callback_data="confirm"),
    InlineKeyboardButton("✏️ Исправить", callback_data="edit")
)

send_again_keyboard = InlineKeyboardMarkup().add(
    InlineKeyboardButton("📝 Отправить ещё один стих", callback_data="send_again")
)

@dp.message_handler(commands='start')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
    "👋 Добро пожаловать в бот канала *Это вам не Пушкин*!\n\n"
    "Здесь вы можете предложить свой стих, который, возможно, будет опубликован 💫. Выбери формат стиха:",
    parse_mode="Markdown",
    reply_markup=format_keyboard
)
@dp.callback_query_handler(lambda c: c.data.startswith("format_"), state='*')
async def process_format(callback_query: types.CallbackQuery, state: FSMContext):
    format_map = {
        "format_pirozhok": "📜 Пирожок",
        "format_poroshek": "💊 Порошок",
        "format_depress": "🌧 Депрессяшок",
        "format_exprompt": "🎭 Экспромт"
    }
    selected = format_map.get(callback_query.data, "Неизвестно")
    await state.update_data(format=selected)
    await bot.send_message(callback_query.from_user.id, f"Формат выбран: {selected}\nТеперь пришли, пожалуйста, сам стих:")
    await PoemForm.text.set()

@dp.message_handler(state=PoemForm.text)
async def process_poem(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Как подписать этот стих? Напиши имя/псевдоним автора.")
    await PoemForm.author.set()

@dp.message_handler(state=PoemForm.author)
async def process_author(message: types.Message, state: FSMContext):
    author_text = message.text.strip()
    if author_text.startswith("✅") or "отправить" in author_text.lower():
        await message.answer("Пожалуйста, укажи автора *текстом* — не нажимай кнопку.", parse_mode="Markdown")
        return
    await state.update_data(author=author_text)
    data = await state.get_data()
    preview = f"✨ Получено:\n\nФормат: {data['format']}\n\nСтих:\n{data['text']}\n\nАвтор: {data['author']}"
    await message.answer(preview, reply_markup=confirm_keyboard)
    await PoemForm.confirm.set()

@dp.callback_query_handler(lambda c: c.data == "confirm", state=PoemForm.confirm)
async def confirm_submission(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text_to_send = f"✨ Новый стих от подписчика:\n\nФормат: {data['format']}\n\n*{data['text']}*\n\nАвтор: _{data['author']}_"
    try:
        await bot.send_message(CHANNEL_ID, text_to_send, parse_mode="Markdown")
        await bot.send_message(
            callback_query.from_user.id,
            "✅ Спасибо! Ваш стих отправлен на рассмотрение редакции.\n\nВозвращайтесь, когда будет вдохновение ✨",
            reply_markup=send_again_keyboard
        )
    except Exception as e:
        await bot.send_message(callback_query.from_user.id, f"Произошла ошибка при отправке в канал: {e}")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "edit", state=PoemForm.confirm)
async def edit_submission(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "Хорошо! Пришли, пожалуйста, исправленный стих:")
    await PoemForm.text.set()

@dp.callback_query_handler(lambda c: c.data == "send_again", state='*')
async def send_again(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.send_message(
        callback_query.from_user.id,
        "Выбери формат стиха для нового отправления:",
        reply_markup=format_keyboard
    )

@dp.message_handler(commands='cancel', state='*')
async def cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено. Чтобы начать сначала, набери /start.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

