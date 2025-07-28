from dotenv import load_dotenv
import warnings, os, asyncio, random
from utils.dbtools import user_exists
from telegram.ext import ContextTypes
from utils.typing_task import keep_typing
from telegram import Update, ChatJoinRequest
from datetime import datetime, timedelta, timezone
warnings.filterwarnings('ignore')
load_dotenv()

COMMUNITY_ID = os.getenv('COMMUNITY_ID')

# ———————————————————————————————————————— GATE KEEPER ————————————————————————————————————————

async def gatekeeper(update: Update, context: ContextTypes.DEFAULT_TYPE, store = None):
    req: ChatJoinRequest = update.chat_join_request
    
    print(f'👀 I see someone trying to join: {req.invite_link.invite_link}')
    ok_user = store.pop(req.invite_link.invite_link)
    print(f'👀 That\'s who it is: {ok_user}') 
    print(f'That\'s what I\'m waiting for: {req.from_user.id}')

    if ok_user == req.from_user.id:
        print('✅ Accepted')

        emoji = random.choice(['🌼', '🌸', '🍀', '🌺', '🌳', '🍁', '🌲', '🍃', '🌷', '🌻', '🌱', '🌿', '💮', '🪴', '🌾', '🪻'])
        await context.bot.approve_chat_join_request(COMMUNITY_ID, req.from_user.id)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'{emoji} У нас новый участник: {req.from_user.mention_html()}',
            parse_mode = 'HTML',
        )
    else:
        print('❌ Rejected')
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

        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Держи [ссылку]({link}) на наше закрытое комьюнити — она действует всего 5 минут (если не успеешь зайти, попроси еще одну — я поделюсь)',
            parse_mode = 'Markdown',
        )
    except: 
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Не получается сгенерировать ссылку :( Обратись в поддержку: мой создатель сам создаст ее специально для тебя',
            parse_mode = 'Markdown',
        )
