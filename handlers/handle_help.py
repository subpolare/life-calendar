from telegram.ext import ContextTypes
from telegram import Update

import asyncio, warnings
from dotenv import load_dotenv

from utils.typing import _keep_typing

warnings.filterwarnings('ignore')
load_dotenv()

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help instructions to the user."""
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )

    help_text = (
        'TODO: describe how to use the bot here.'
    )

    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = help_text,
        parse_mode = 'Markdown'
    )
