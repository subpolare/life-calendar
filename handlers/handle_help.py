from utils.typing_task import keep_typing
from telegram.ext import ContextTypes
from utils.dbtools import user_exists
from dotenv import load_dotenv
from telegram import Update
import asyncio, warnings, logging

warnings.filterwarnings('ignore')
load_dotenv()

logger = logging.getLogger(__name__)

@keep_typing
async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(3)
    logger.info('User %s requested help', update.effective_user.username)
    exist = await user_exists(update.effective_user.id)
    if not exist:
        logger.info('User %s is not registered for help command', update.effective_user.username)
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = f'Чтобы использовать эту команду, тебе сначала нужно зарегестрироваться. Для этого нажми на /start',
            parse_mode  = 'Markdown'
        )
    help_text = (
        'Вот небольшой список того, что я умею\n\n'
        '/start — Начать наше знакомство с самого начала\n\n'
        '/calendar — Нарисовать календарь с любым событием из твоей жизни\n\n'
        '/me — Узнать, что я знаю о тебе. Здесь же можно отредактировать эти данные\n\n'
        '/oblivion — Безвозвратно удалить все данные о себе. После нажатия на эту команду я еще раз спрошу тебя, уверены ли ты в этом, так что можешь не бояться нажать на эту кнопку случайно\n\n'
        '/community — Отправлю тебе одноразовую ссылку для входа в наше закрытое комьюнити по продлению жизни\n\n'
        '/cancel — Если я вдруг зависну, эта команда может помочь меня перезапустить (а может и не помочь...)'
    )
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = help_text,
        parse_mode = 'Markdown'
    )
