from telegram.constants import ChatAction
from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from datetime import date
from dotenv import load_dotenv
from utils.dateparser import parse_dates
from utils.typing_task import keep_typing
from lifecalendar.bridge import create_calendar
import asyncio, random, os, secrets, re, warnings, logging
from utils.dbtools import (
    set_birth, set_name, set_gender, get_user_data,
    set_empty_event, set_event, user_exists, delete_data
)
from handlers.habits import ask_habits_intro
warnings.filterwarnings('ignore')
load_dotenv()

logger = logging.getLogger(__name__)

def _get_events(gender):
    events = [
        {(0, 22) : [
            {'key' : 'education',    'label' : 'Образование', 'button' : 'Школу + университет', 'message' : f'*Когда ты начал{"а" if gender == "female" else ""} учиться, а когда закончил{"а" if gender == "female" else ""}?* Выбери любой удобный формат ответа, вот пара примеров:\n\n~ С 7 до 22 лет\n~ С сентября 2011 до июня 2028\n~ С 01.09.2011 до 22.06.2028'},
            {'key' : 'school',       'label' : 'Школа',       'button' : 'Только школу',        'message' : f'*Когда ты пош{"ла" if gender == "female" else "ел"} и когда закончил{"а" if gender == "female" else ""} ее?* Выбери любой удобный формат ответа, вот пара примеров:\n\n~ С 7 до 18 лет\n~ С сентября 2011 до июня 2022\n~ С 01.09.2011 до 22.06.2022'},
            {'key' : 'job',          'label' : 'Работа',      'button' : 'Сколько я работаю',   'message' : f'*Когда ты впервые начал{"а" if gender == "female" else ""} работать?* Выбери любой удобный формат ответа, вот пара примеров:\n\n~ В 13 лет\n~ В 13 с половиной лет\n~ С 13 до 21\n~ В июне 2017'},
            {'key' : 'smoking',      'label' : 'Курение',     'button' : 'Сколько я уже курю',  'message' : f'*Когда ты начал{"а" if gender == "female" else ""} курить?* Выбери любой удобный формат ответа, вот пара примеров:\n\n~ В 13 лет\n~ В 13 с половиной лет\n~ С 13 до 21\n~ С июня 2017 до августе 2009'},
            {'key' : 'relationship', 'label' : 'Отношения',   'button' : 'Мои отношения',       'message' : f'*Когда начались твои отношения? Если они закончились, то напиши, когда это было.* Выбери любой удобный формат ответа, вот пара примеров:\n\n~ С 09.08.2024\n~ С 9 августа 2024\n~ С октября 2015 до января 2017'}
        ]},
    ]
    return events 

PHRASES = [
    'Отметила все на календаре — смотри, как это смотрится в масштабе твоей жизни',
    'Смотри, как это выглядит в рамках твоей жизни', 
    'Нанесла даты на календарь', 
    'Смотри — выглядит как полноценная часть твоей жизни', 
    'Нарисовала твой новый календарь', 
]

def _get_age(birth_date: date) -> int:
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

# ———————————————————————————————————————— START HANDLERS ————————————————————————————————————————

ASK_BIRTHDAY, ASK, ASK_NAME, ASK_GENDER, ASK_TYPE, ASK_DATE, ASK_MORE, HABIT_INTRO, HABIT_Q, HABIT_EFFECTS, DELETE_DATA = range(11)

@keep_typing
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exist = await user_exists(update.effective_user.id)
    if exist: 
        logger.info('User %s invoked /start', update.effective_user.username)
        user_data = await get_user_data(update.effective_user.id) 
        gender = user_data['gender']

        keyboard = [
            [InlineKeyboardButton(f'Да, все удаляем!', callback_data = 'yes')],
            [InlineKeyboardButton(f'Нет, я случайно сюда нажал{"а" if gender == "female" else ""}', callback_data = 'no')]
        ]
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = f'Уверен{"а" if gender == "female" else ""}, что хочешь начать регистрацию сначала? Если да, я удалю все, что знаю о тебе, и ты внесешь все данные заново.', 
            parse_mode   = f'Markdown', 
            reply_markup = InlineKeyboardMarkup(keyboard)
        )
        return DELETE_DATA 
    else:
        logger.info('New user %s started registration', update.effective_user.username)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Привет! Давай вместе соберём твой календарь жизни. Для этого мне нужно узнать о тебе кое-что.\n\n*Когда у тебя День рождения?* Напиши в формате ДД.ММ.ГГГГ, например, 01.09.1990', 
            parse_mode = f'Markdown'
        )
        return ASK_BIRTHDAY

@keep_typing    
async def clean_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    answer = query.data
    logger.info('User %s chose to %s data', update.effective_user.username, 'clean' if answer == 'yes' else 'keep')

    if answer == 'yes':
        await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
        await delete_data(update.effective_user.id)
        return await handle_start(update, context)
    else: 
        await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Фух, а то я испугалась...',
            parse_mode = 'Markdown'
        )
        return ConversationHandler.END

@keep_typing
async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: 
        day, month, year = map(int, update.message.text.strip().split('.'))
        if (date.today() - date(year, month, day)).days / 365.25 > 120:
            raise ValueError
        if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', update.message.text.strip()): 
            logger.warning('User %s provided invalid birthday', update.effective_user.username)
            raise ValueError
    except: 
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Что-то не так с форматом даты. Пожалуйста, напиши дату ее в формате ДД.ММ.ГГГГ: например, 01.09.1990',
            parse_mode = 'Markdown'
        )
        return ASK_BIRTHDAY
    
    logger.info('User %s set birthday', update.effective_user.username)
    await set_birth(update.effective_user.id, update.message.text)
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Записала', 
        parse_mode   = 'Markdown'
    )
    await context.bot.send_chat_action(
        chat_id = update.effective_chat.id, 
        action  = ChatAction.TYPING
    )
    await asyncio.sleep(3)

    keyboard = [[
        InlineKeyboardButton('Парень', callback_data = 'male'),
        InlineKeyboardButton('Девушка', callback_data = 'female')
    ]]

    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'*Извини за вопрос, но ты парень или девушка?* Отвечай честно: это нужно для твоего календаря.', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ASK_GENDER

@keep_typing
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query 
    await query.answer()
    gender = query.data

    await context.bot.delete_message(
        chat_id    = query.message.chat.id,
        message_id = query.message.message_id
    )
    context.user_data['gender'] = gender
    await set_gender(update.effective_user.id, context.user_data['gender'])

    user_data = await get_user_data(update.effective_user.id) 
    day, month, year = map(int, user_data['birth'].split('.'))
    filename = f'tmp/{secrets.token_hex(8)}.png'
    create_calendar(date(year, month, day), filename, female = gender)  

    with open(filename, 'rb') as photo:
        await context.bot.send_document(
            chat_id    = update.effective_chat.id,
            document   = photo,
            caption    = f'Держи свой первый календарь жизни. Скинула файлом, чтобы было видно все детали.\n\nПока он про среднего человека в России, но хочется сделать его лично для тебя', 
            parse_mode = 'Markdown'
        )
    await context.bot.send_chat_action(
        chat_id = update.effective_chat.id, 
        action  = ChatAction.TYPING
    )

    os.remove(filename)
    keyboard = [[
        InlineKeyboardButton('Конечно!', callback_data = 'yes'),
        InlineKeyboardButton('Нет, но я вернусь', callback_data = 'no')
    ]]
    await asyncio.sleep(5)
    
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Хочешь, создам календарь на основе именно твоей жизни? Для этого я задам тебе несколько вопросов, это займет не больше 5 минут', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ASK

@keep_typing
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query 
    await query.answer()
    answer = query.data

    await context.bot.delete_message(
        chat_id = query.message.chat.id,
        message_id = query.message.message_id
    )

    await asyncio.sleep(3)
    if answer == 'yes':  
        text = 'Тогда начнем со знакомства. Как тебя зовут?'
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = text, 
            parse_mode  = 'Markdown'
        )
        return ASK_NAME
    else:    
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = 'Буду ждать, пока ты вернешься! Нажми /start, если решишь создать новый календарь.' , 
            parse_mode  = 'Markdown'
        )
        return ConversationHandler.END
    
@keep_typing
async def ask_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    await set_name(update.effective_user.id, name)
    return await ask_event(update, context)

@keep_typing
async def ask_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(3)
    user_data = await get_user_data(update.effective_user.id)
    day, month, year = map(int, user_data['birth'].split('.'))
    gender = user_data.get('gender')

    age = _get_age(date(year, month, day))
    events = _get_events(gender)

    for age_range in events:
        for key, events in age_range.items():
            if key[0] <= age <= key[1]:
                break

    sample = random.sample(events, k = min(5, len(events)))
    available_events = [e for e in sample if e['key'] not in context.user_data.get('added_events', set())]

    keyboard = []
    row = []
    for e in available_events:
        row.append(InlineKeyboardButton(e['button'], callback_data = e['key']))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    if context.user_data.get('added_events'):
        keyboard.append([InlineKeyboardButton('Давай закончим', callback_data = 'finish')])

    if not context.user_data.get('added_events'):
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = f'Что хочешь добавить? Для начала выбери одно событие. Со временем ты сможешь создавать свои календари сам{"а" if user_data["gender"] == "female" else ""}',
            parse_mode   = 'Markdown',
            reply_markup = InlineKeyboardMarkup(keyboard)
        )
        return ASK_TYPE

    if len(keyboard) == 1:
        return await ask_habits_intro(update, context)

    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = 'Что ещё хочешь добавить? Чуть позже научу тебя добавлять любые события уже без моих подсказок',
        parse_mode   = 'Markdown',
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ASK_TYPE


@keep_typing
async def ask_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query 
    await query.answer()
    answer = query.data
    if answer == 'finish':
        await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
        return await ask_habits_intro(update, context)

    user_data = await get_user_data(update.effective_user.id)
    gender = user_data.get('gender')
    events = _get_events(gender)

    if not gender:
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Упс, не получилось вспомнить твои данные. Давай начнём заново? Нажми на /start',
            parse_mode = 'Markdown',
        )
        return ConversationHandler.END

    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)

    first = not context.user_data.get('added_events')
    picked = None

    for age_range in events:
        for _, events in age_range.items():
            picked = next((e for e in events if e['key'] == answer), None)
            if picked:
                break
        if picked:
            break

    if not picked:
        await context.bot.send_message(
            chat_id    = update.effective_chat.id, 
            text       = 'Случайно потеряла то, что ты выбрал. Давай ещё раз', 
            parse_mode = 'Markdown'
        )
        return ASK_TYPE

    context.user_data['event_key']     = picked['key']
    context.user_data['event_label']   = picked['label']
    context.user_data['event_message'] = picked['message']
    await set_empty_event(update.effective_user.id, picked['label'], first = first)

    await asyncio.sleep(3)
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = context.user_data['event_message'], 
        parse_mode   = 'Markdown', 
    )
    return ASK_DATE

@keep_typing
async def create_second_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    user_data = await get_user_data(update.effective_user.id)
    day, month, year = map(int, user_data['birth'].split('.'))
    birth = date(year, month, day)

    label = context.user_data.get('event_label')
    key   = context.user_data.get('event_key')

    try:
        event = parse_dates(answer, birth)
    except Exception:
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Не могу прочитать твою дату...' + context.user_data['event_message'], 
            parse_mode = 'Markdown', 
        )
        return ASK_DATE

    await set_event(update.effective_user.id, label, event)
    if key:
        context.user_data.setdefault('added_events', set()).add(key)

    filename = f'tmp/{secrets.token_hex(8)}.png'
    female = user_data['gender'] == 'female'
    create_calendar(birth, fname = filename, female = female, event = event, label = label)

    with open(filename, 'rb') as photo:
        await context.bot.send_document(
            chat_id    = update.effective_chat.id,
            document   = photo,
            caption    = random.choice(PHRASES),
            parse_mode = 'Markdown'
        )
        os.remove(filename)
    await context.bot.send_chat_action(
        chat_id = update.effective_chat.id, 
        action  = ChatAction.TYPING
    )
    await asyncio.sleep(3)

    keyboard = [[
        InlineKeyboardButton('Конечно!', callback_data = 'more_yes'),
        InlineKeyboardButton('Лучше потом', callback_data = 'more_no')
    ]]
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = 'Хочешь добавить ещё одно событие?',
        parse_mode   = 'Markdown',
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ASK_MORE

@keep_typing
async def ask_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    answer = query.data

    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
    if answer == 'more_yes':
        return await ask_event(update, context)
    else:
        return await ask_habits_intro(update, context)
        # return await finish_start(update, context)

@keep_typing
async def finish_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(3)
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = (
            'Чтобы ты мог разблокировать новые клеточки в нем, каждый день я буду присылать тебе полезные советы по продлению жизни.\n\n'
            'Я собираю их из статей научного журнала [nature](https://www.nature.com/) и разных журналов nature reviews. Это топовые научные журналы, '
            'каждая статья в которых проверяется учеными со всего мира.'
        ),
        parse_mode = 'Markdown',
    )
    await context.bot.send_chat_action(
        chat_id = update.effective_chat.id, 
        action  = ChatAction.TYPING
    )

    await asyncio.sleep(7)
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = (
            'Теперь ты можешь создавать свои собственные календари с любыми событиями из жизни. Для этого нажми на /calendar\n\nА если хочешь поменять какую-то информацию о себе, нажми на /me'
        ),
        parse_mode = 'Markdown',
    )

    # await context.bot.send_chat_action(
    #     chat_id = update.effective_chat.id, 
    #     action  = ChatAction.TYPING
    # )
    # await asyncio.sleep(3)
    # await context.bot.send_message(
    #     chat_id      = update.effective_chat.id,
    #     text         = 'Теперь ты можешь создавать свои собственные календари с любыми событиями из жизни. Для этого нажми на /calendar\n\nА еще вступай в наше закрытое комьюнити, для этого нажми на /community',
    #     parse_mode   = 'Markdown',
    # )
    return ConversationHandler.END
