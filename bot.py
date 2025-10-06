\
    import os
    import logging
    from aiogram import Bot, Dispatcher, types
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    from aiogram.utils.executor import start_webhook
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.state import State, StatesGroup
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHANNEL_ID = os.getenv("CHANNEL_ID")
    PUBLIC_URL = os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", "8000"))

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is missing. Set BOT_TOKEN in your environment.")
        raise SystemExit("BOT_TOKEN is required")

    if not PUBLIC_URL:
        logger.error("PUBLIC_URL environment variable is missing. Set PUBLIC_URL to your app URL (e.g. https://your-app.onrender.com)")
        raise SystemExit("PUBLIC_URL is required for webhook mode")

    if not CHANNEL_ID:
        logger.warning("CHANNEL_ID not set. Default channel actions will fail unless CHANNEL_ID is provided.")

    WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
    WEBHOOK_URL = PUBLIC_URL.rstrip("/") + WEBHOOK_PATH

    bot = Bot(token=BOT_TOKEN)
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

    @dp.message_handler(state=PoemForm.text, content_types=types.ContentTypes.TEXT)
    async def process_poem(message: types.Message, state: FSMContext):
        await state.update_data(text=message.text)
        await message.answer("Как подписать этот стих? Напиши имя/псевдоним автора.")
        await PoemForm.author.set()

    @dp.message_handler(state=PoemForm.author, content_types=types.ContentTypes.TEXT)
    async def process_author(message: types.Message, state: FSMContext):
        author_text = message.text.strip()
        if author_text.startswith("✅") or "отправить" in author_text.lower():
            await message.answer("Пожалуйста, укажи автора *текстом* — не нажимай кнопку.", parse_mode="Markdown")
            return
        await state.update_data(author=author_text)
        data = await state.get_data()
        preview = f"✨ Получено:\n\nФормат: {data.get('format')}\n\nСтих:\n{data.get('text')}\n\nАвтор: {data.get('author')}"
        await message.answer(preview, reply_markup=confirm_keyboard)
        await PoemForm.confirm.set()

    @dp.callback_query_handler(lambda c: c.data == "confirm", state=PoemForm.confirm)
    async def confirm_submission(callback_query: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        text_to_send = f"✨ Новый стих от подписчика:\n\nФормат: {data.get('format')}\n\n*{data.get('text')}*\n\nАвтор: _{data.get('author')}_"
        try:
            if CHANNEL_ID:
                await bot.send_message(int(CHANNEL_ID), text_to_send, parse_mode="Markdown")
            else:
                logger = logging.getLogger(__name__)
                logger.warning("CHANNEL_ID is not set; skipping sending to channel.")
            await bot.send_message(
                callback_query.from_user.id,
                "✅ Спасибо! Ваш стих отправлен на рассмотрение редакции.\n\nВозвращайтесь, когда будет вдохновение ✨",
                reply_markup=send_again_keyboard
            )
        except Exception as e:
            logging.exception("Failed to deliver poem to channel: %s", e)
            await bot.send_message(callback_query.from_user.id, f"Произошла ошибка при отправке в канал: {e}")
        await state.finish()
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "edit", state=PoemForm.confirm)
    async def edit_submission(callback_query: types.CallbackQuery, state: FSMContext):
        await bot.send_message(callback_query.from_user.id, "Хорошо! Пришли, пожалуйста, исправленный стих:")
        await PoemForm.text.set()
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data == "send_again", state='*')
    async def send_again(callback_query: types.CallbackQuery, state: FSMContext):
        await state.finish()
        await bot.send_message(
            callback_query.from_user.id,
            "Выбери формат стиха для нового отправления:",
            reply_markup=format_keyboard
        )
        await callback_query.answer()

    @dp.message_handler(commands='cancel', state='*')
    async def cancel(message: types.Message, state: FSMContext):
        await state.finish()
        await message.answer("Действие отменено. Чтобы начать сначала, набери /start.")

    async def on_startup(dp):
        # set webhook to Render's URL (PUBLIC_URL must be set)
        await bot.set_webhook(WEBHOOK_URL)
        logging.info("Webhook set to %s", WEBHOOK_URL)

    async def on_shutdown(dp):
        logging.info("Shutting down..")
        await bot.delete_webhook()
        await dp.storage.close()
        await dp.storage.wait_closed()

    if __name__ == '__main__':
        logging.info("Starting webhook server at %s:%s%s", "0.0.0.0", PORT, WEBHOOK_PATH)
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            skip_updates=True,
            host="0.0.0.0",
            port=PORT,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )
