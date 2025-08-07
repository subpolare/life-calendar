from dotenv import load_dotenv
import warnings, os, asyncio, random, logging
from utils.dbtools import user_exists
from telegram.ext import ContextTypes
from utils.typing_task import keep_typing
from telegram import Update, ChatJoinRequest
from datetime import datetime, timedelta, timezone
warnings.filterwarnings('ignore')
load_dotenv()

logger = logging.getLogger(__name__)

COMMUNITY_ID = os.getenv('COMMUNITY_ID')

# ———————————————————————————————————————— GATE KEEPER ————————————————————————————————————————

async def gatekeeper(update: Update, context: ContextTypes.DEFAULT_TYPE, store = None):
    req: ChatJoinRequest = update.chat_join_request

    logger.info('Join request from %s', req.from_user.username)
    ok_user = store.pop(req.invite_link.invite_link)

    if ok_user == req.from_user.id:
        logger.info('Accepted join request for %s', req.from_user.username)

        emoji = random.choice(['🌼', '🌸', '🍀', '🌺', '🌳', '🍁', '🌲', '🍃', '🌷', '🌻', '🌱', '🌿', '💮', '🪴', '🌾', '🪻'])
        await context.bot.approve_chat_join_request(COMMUNITY_ID, req.from_user.id)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'{emoji} У нас новый участник: {req.from_user.mention_html()}',
            parse_mode = 'HTML',
        )
    else:
        logger.info('Rejected join request for %s', req.from_user.username)
        await context.bot.decline_chat_join_request(COMMUNITY_ID, req.from_user.id)

# ———————————————————————————————————————— COMMUNITY HANDLER ————————————————————————————————————————

@keep_typing
async def handle_community(update: Update, context: ContextTypes.DEFAULT_TYPE, store = None):
    await asyncio.sleep(3)
    exist = await user_exists(update.effective_user.id)
    if not exist:
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = f'Чтобы использовать эту команду, тебе сначала нужно зарегестрироваться. Для этого нажми на /start', 
            parse_mode  = 'Markdown'
        )
    try:
        expires = datetime.now(timezone.utc) + timedelta(minutes = 2)
        invite = await context.bot.create_chat_invite_link(
            chat_id              = COMMUNITY_ID,
            expire_date          = expires,
            creates_join_request = True,
        )
        link = invite.invite_link
        store.add(link, update.effective_user.id, expires)

        logger.info('Generated invite link for user %s', update.effective_user.username)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Держи [ссылку]({link}) на наше закрытое комьюнити — она действует всего 5 минут (если не успеешь зайти, попроси еще одну — я поделюсь)',
            parse_mode = 'Markdown',
        )
    except Exception as exc:
        logger.error('Failed to generate invite link for user %s: %s', update.effective_user.username, exc)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Не получается сгенерировать ссылку :( Обратись в поддержку: мой создатель сам создаст ее специально для тебя',
            parse_mode = 'Markdown',
        )

