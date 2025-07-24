from telegram.ext import ContextTypes
from utils.typing import _keep_typing
from dotenv import load_dotenv
from telegram import Update
import asyncio, warnings

warnings.filterwarnings('ignore')
load_dotenv()

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    help_text = (
        'Вот небольшой список того, что я умею\n\n'
        '/start — Начать наше знакомство с самого начала\n\n'
        '/calendar — Нарисовать календарь с любым событием из твоей жизни\n\n'
        '/me — Узнать, что я знаю о тебе. Здесь же можно отредактировать эти данные\n\n'
        '/oblivion — Безвозвратно удалить все данные о себе. После нажатия на эту команду я еще раз спрошу тебя, уверены ли ты в этом, так что можешь не бояться нажать на эту кнопку случайно\n\n'
        '/cancel — Если я вдруг зависну, эта команда может помочь меня перезапустить (а может и не помочь...)'
    )

    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = help_text,
        parse_mode = 'Markdown'
    )
