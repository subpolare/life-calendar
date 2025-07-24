import asyncio
import os
import warnings
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from utils.typing import _keep_typing

warnings.filterwarnings('ignore')
load_dotenv()

COMMUNITY_URL = os.getenv('COMMUNITY_URL')

"""Telegram community chat helper.

Set ``COMMUNITY_URL`` in your environment (e.g. in a ``.env`` file) to the
@username of your community chat or to a permanent invite link. The handler
tries to create a new invite link valid for two minutes. If it fails, the
stored ``COMMUNITY_URL`` is sent instead.
"""

async def handle_community(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )

    try:
        invite = await context.bot.create_chat_invite_link(
            chat_id     = COMMUNITY_URL,
            expire_date = datetime.utcnow() + timedelta(minutes = 2)
        )
        link = invite.invite_link
    except Exception:
        link = COMMUNITY_URL

    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = f'Вот ссылка на наш чат: {link}',
        parse_mode = 'Markdown',
    )
