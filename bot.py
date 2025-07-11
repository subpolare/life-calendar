from telegram.constants import ChatAction
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

from datetime import date
from dotenv import load_dotenv
from life_calendar import calendar
import asyncio, logging, os, random, re, secrets, os, warnings
warnings.filterwarnings('ignore')
load_dotenv()

LIFE_BOT_TOKEN = os.getenv('LIFE_BOT_TOKEN')
STAT_BOT_TOKEN = os.getenv('STAT_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_URL       = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')
ENCRYPTION_KEY     = os.getenv('ENCRYPTION_KEY')

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

# ———————————————————————————————————————— START HANDLERS ————————————————————————————————————————

ASK_BIRTHDAY, ASK, ASK_NAME, ASK_GENDER, ASK_SCHOOL_AGE, ASK_UNI_YESNO, ASK_UNI_AGE = range(7)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )

    # Добавить проврку на то, есть ли ДР в SQl: если да, то просить. Если нет, то продолжать жить в этой функции

    await asyncio.sleep(random.uniform(1, 3))
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = f'Привет! Давай вместе соберём твой календарь жизни. Для этого мне нужно узнать о тебе кое-что.\n\n*Когда у тебя День рождения?* Напиши в формате ДД.ММ.ГГГГ, например, 01.09.1990', 
        parse_mode = f'Markdown'
    )

    stop_event.set()
    await typing_task
    return ASK_BIRTHDAY

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )

    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', update.message.text.strip()):
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Что-то не так с форматом даты. Пожалуйста, напиши дату ее в формате ДД.ММ.ГГГГ: например, 01.09.1990',
            parse_mode = 'Markdown'
        )
        return ASK_BIRTHDAY
    
    # Сюда PostgreSQL !!! 
    context.user_data['birthday'] = update.message.text
    
    day, month, year = map(int, context.user_data['birthday'].split('.'))
    filename = f'tmp/{secrets.token_hex(8)}.png'
    calendar(date(year, month, day), filename, first = True) 

    with open(filename, 'rb') as photo:
        await context.bot.send_document(
            chat_id    = update.effective_chat.id,
            document   = photo,
            caption    = f'Держи свой первый календарь жизни. Скинула файлом, чтобы было видно все детали.\n\nПока он на 80 лет и про среднего человек в России, а хочется сделать его лично для тебя.', 
            parse_mode = 'Markdown'
        )
    
    os.remove(filename)

    keyboard = [[
        InlineKeyboardButton('Конечно!', callback_data = True),
        InlineKeyboardButton('Нет, но я за ним вернусь', callback_data = False)
    ]]
    await asyncio.sleep(random.uniform(1, 3))
    await context.bot.send_message(
         chat_id      = update.effective_chat.id,
         text         = f'Хочешь, создам календарь на основе именно твоей жизни?', 
         parse_mode   = 'Markdown', 
         reply_markup = InlineKeyboardMarkup(keyboard)
    )

    stop_event.set()
    await typing_task
    return ASK

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )

    query = update.callback_query 
    await query.answer()
    answer = query.data

    if answer: 
        text = 'Ура! Тогда начнем со знакомства. *Как тебя зовут?* Напиши только имя.\n\n_Если интересно, как я храню твои данные, вот [подробный рассказ](https://github.com/subpolare/life-calendar/blob/main/security/secutiry.md). Коротко — ни я, ни мой создатель не можем посмотреть их без твоего ведома._'
    else:
        text = 'Буду ждать, пока ты вернешься! Нажми /start, если решишь создать новый календарь.' 
        # Как все это прервать???      

    await context.bot.send_message(
        chat_id     = update.effective_chat.id,
        text        = text, 
        parse_mode  = 'Markdown'
    )

    stop_event.set()
    await typing_task
    return ASK_NAME

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )
    await asyncio.sleep(random.uniform(1, 3))

    # Сюда PostgreSQL !!! 
    context.user_data['name'] = update.message.text

    keyboard = [[
            InlineKeyboardButton('Мужской', callback_data = 'male'),
            InlineKeyboardButton('Женский', callback_data = 'female')
    ]]
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Рада познакомиться, {context.user_data["name"]}! В каком роде мне к тебе обращаться? Выбери кнопку с нужным ответом.', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )

    stop_event.set()
    await typing_task
    return ASK_GENDER

async def ask_school_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


# ———————————————————————————————————————— INITIALIZING BOT ————————————————————————————————————————

async def cancel(update: Update, context: ContextTypes. DEFAULT_TYPE) -> int:
    await update.message.reply_text('Окей, если что — я всегда на связи!')
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(LIFE_BOT_TOKEN).build()
    print('✅ The bot has successfully launched and is working while you are drinking tea.')

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', handle_start)],
        states = {
            ASK_BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask)],
            ASK:          [CallbackQueryHandler(ask_name)],
            # ASK_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_school_age)]
        },
        fallbacks = [CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()