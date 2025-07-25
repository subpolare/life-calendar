import warnings, os, asyncio
from dotenv import load_dotenv
from telegram.ext import ContextTypes
from utils.typing import _keep_typing
from telegram import Update, ChatJoinRequest
from datetime import datetime, timedelta, timezone
warnings.filterwarnings('ignore')
load_dotenv()

COMMUNITY_ID = os.getenv('COMMUNITY_ID')

# ———————————————————————————————————————— GATE KEEPER ————————————————————————————————————————

class InviteStore:
    def __init__(self):
        self._data: dict[str, tuple[int, datetime]] = {}

    def add(self, link: str, user_id: int, expires_at: datetime):
        self._data[link] = (user_id, expires_at)

    def pop(self, link: str):
        return self._data.pop(link, (None, None))[0]

    def cleanup(self):
        now = datetime.now(timezone.utc)
        for link, (_, exp) in list(self._data.items()):
            if exp <= now:
                del self._data[link]

store = InviteStore()

async def gatekeeper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req: ChatJoinRequest = update.chat_join_request
    ok_user = store.pop(req.invite_link)
    if ok_user == req.from_user.id:
        await context.bot.approve_chat_join_request(COMMUNITY_ID, req.from_user.id)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'У нас новый участник: {req.from_user.mention_html()} 🎉',
            parse_mode = 'Markdown',
        )
    else:
        await context.bot.decline_chat_join_request(COMMUNITY_ID, req.from_user.id)

# ———————————————————————————————————————— COMMUNITY HANDLER ————————————————————————————————————————

async def handle_community(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))
    await asyncio.sleep(3)
    try:
        expires = datetime.now(timezone.utc) + timedelta(minutes = 2)
        invite = await context.bot.create_chat_invite_link(
            chat_id              = COMMUNITY_ID,
            expire_date          = expires,
            creates_join_request = True,
        )
        link = invite.invite_link

        stop_event.set()
        await typing_task
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Держи [ссылку]({link}) на наше закрытое комьюнити — она действует всего 5 минут (если не успеешь зайти, попроси еще одну — я поделюсь)',
            parse_mode = 'Markdown',
        )
        store.add(link.invite_link, update.effective_user.id, expires)
    except: 
        stop_event.set()
        await typing_task
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Не получается сгенерировать ссылку :( Обратись в поддержку: мой создатель создаст ее специально для тебя',
            parse_mode = 'Markdown',
        )


