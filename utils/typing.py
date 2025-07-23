import asyncio
from telegram.constants import ChatAction
try:
    # PTB >= 20 ships ChatActionSender in telegram.helpers
    from telegram.helpers import ChatActionSender  # type: ignore
except Exception:  # pragma: no cover - fallback for older PTB
    # minimal fallback for environments without ChatActionSender
    class ChatActionSender:
        def __init__(self, action: ChatAction, chat_id: int, bot):
            self.action = action
            self.chat_id = chat_id
            self.bot = bot
            self._task = None
            self._stop_event = asyncio.Event()

        async def __aenter__(self):
            async def _run():
                try:
                    while not self._stop_event.is_set():
                        await self.bot.send_chat_action(
                            chat_id=self.chat_id,
                            action=self.action,
                        )
                        try:
                            await asyncio.wait_for(self._stop_event.wait(), 4.5)
                        except asyncio.TimeoutError:
                            pass
                except asyncio.CancelledError:
                    pass

            self._task = asyncio.create_task(_run())
            return self

        async def __aexit__(self, exc_type, exc, tb):
            self._stop_event.set()
            if self._task is not None:
                await self._task

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
