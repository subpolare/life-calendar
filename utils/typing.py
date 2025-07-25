import asyncio
from telegram.constants import ChatAction

async def _keep_typing(chat_id: int, bot, stop_event: asyncio.Event):
    try:
        while not stop_event.is_set():
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=4.5)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        pass 