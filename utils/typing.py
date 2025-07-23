import asyncio
from telegram.constants import ChatAction
from telegram.helpers import ChatActionSender

async def _keep_typing(chat_id: int, bot, stop_event: asyncio.Event):
    try:
        async with ChatActionSender(
            action = ChatAction.TYPING,
            chat_id = chat_id,
            bot     = bot
        ):
            await stop_event.wait()
    except asyncio.CancelledError:
        pass
