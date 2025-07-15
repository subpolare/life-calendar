from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from dotenv import load_dotenv
from datetime import date, timedelta
from utils.typing import _keep_typing
from life_calendar import create_calendar
from dateutil.relativedelta import relativedelta
from utils.dbtools import set_birth, set_name, set_gender, get_user_data, set_empty_event, get_empty_event
import asyncio, random, os, secrets, re, warnings, datetime
warnings.filterwarnings('ignore')
load_dotenv()

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_PORT      = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')

# ———————————————————————————————————————— START HANDLERS ————————————————————————————————————————

ASK_BIRTHDAY, ASK, ASK_NAME, ASK_GENDER, ASK_TYPE, ASK_DATE = range(6)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    stop_event.set()
    await typing_task
    
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = f'Привет! Давай вместе соберём твой календарь жизни. Для этого мне нужно узнать о тебе кое-что.\n\n*Когда у тебя День рождения?* Напиши в формате ДД.ММ.ГГГГ, например, 01.09.1990', 
        parse_mode = f'Markdown'
    )
    return ASK_BIRTHDAY

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', update.message.text.strip()):
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = f'Что-то не так с форматом даты. Пожалуйста, напиши дату ее в формате ДД.ММ.ГГГГ: например, 01.09.1990',
            parse_mode = 'Markdown'
        )
        return ASK_BIRTHDAY
    
    context.user_data['birthday'] = update.message.text
    await set_birth(update.effective_user.id, context.user_data['birthday'])
    day, month, year = map(int, context.user_data['birthday'].split('.'))
    filename = f'tmp/{secrets.token_hex(8)}.png'
    create_calendar(date(year, month, day), fname = filename, female = False)

    with open(filename, 'rb') as photo:
        await context.bot.send_document(
            chat_id    = update.effective_chat.id,
            document   = photo,
            caption    = f'Держи свой первый календарь жизни. Скинула файлом, чтобы было видно все детали.\n\nПока он про среднего человек в России, но хочется сделать его лично для тебя.', 
            parse_mode = 'Markdown'
        )
    
    os.remove(filename)
    keyboard = [[
        InlineKeyboardButton('Конечно!', callback_data = 'yes'),
        InlineKeyboardButton('Нет, но я за ним вернусь', callback_data = 'no')
    ]]
    await asyncio.sleep(random.uniform(1, 3))
    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Хочешь, создам календарь на основе именно твоей жизни? Для этого я задам тебе несколько вопросов, это займет не больше 5 минут', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ASK

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    query = update.callback_query 
    await query.answer()
    answer = query.data

    await context.bot.delete_message(
        chat_id =query.message.chat.id,
        message_id =query.message.message_id
    )

    await asyncio.sleep(random.uniform(1, 3))
    if answer == 'yes': 
        stop_event.set()
        await typing_task
        text = 'Тогда начнем со знакомства. <b>Как тебя зовут?</b> Напиши только имя.'
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = text, 
            parse_mode  = 'HTML'
        )
        return ASK_NAME
    else:
        stop_event.set()
        await typing_task

        text = 'Буду ждать, пока ты вернешься! Нажми /start, если решишь создать новый календарь.' 
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = text, 
            parse_mode  = 'Markdown'
        )
        return ConversationHandler.END

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    await asyncio.sleep(random.uniform(1, 3))
    context.user_data['name'] = update.message.text
    await set_name(update.effective_user.id, context.user_data['name'])

    keyboard = [[
            InlineKeyboardButton('Парень', callback_data = 'male'),
            InlineKeyboardButton('Девушка', callback_data = 'female')
    ]]
    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Рада познакомиться, {context.user_data["name"]}! Извини за вопрос, но ты парень или девушка? Отвечай честно: это нужно для твоего календаря.', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ASK_GENDER

async def ask_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    query = update.callback_query 
    await query.answer()
    gender = query.data

    await context.bot.delete_message(
        chat_id    = query.message.chat.id,
        message_id = query.message.message_id
    )
    context.user_data['gender'] = gender
    await set_gender(update.effective_user.id, context.user_data['gender'])

    if gender == 'male':
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = 'Отлично! Теперь я готова создать календарь лично для тебя.',
            parse_mode   = 'Markdown', 
        )
    else:  
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = 'Тебе повезло! Тот факт, что ты девушка, разблокировал в твоем календаре сразу 10 лишних строк!', 
            parse_mode   = 'Markdown', 
        )
        user_data = await get_user_data(update.effective_user.id) 
        day, month, year = map(int, user_data['birth'].split('.'))
        filename = f'tmp/{secrets.token_hex(8)}.png'
        create_calendar(date(year, month, day), filename, female = True)  

        with open(filename, 'rb') as photo:
            await context.bot.send_document(
                chat_id    = update.effective_chat.id,
                document   = photo,
                caption    = f'Вот твой новый календарик: на 12% длиннее, чем был. Теперь давай сделаем его еще точнее и добавим события из твоей жизни.', 
                parse_mode = 'Markdown'
            )
        os.remove(filename)

    await asyncio.sleep(3)
    keyboard = [
            [InlineKeyboardButton('Школу + университет', callback_data = 'education')],
            [InlineKeyboardButton('Только школу', callback_data = 'school'), InlineKeyboardButton('Работу', callback_data = 'job')], 
            [InlineKeyboardButton('Сколько я уже курю', callback_data = 'smoking')], 
            [InlineKeyboardButton('Сколько длятся мои отношения', callback_data = 'alcohol')], 
    ]

    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Что хочешь добавить? Давай начнем с чего-то одного, чтобы ты научил{"ась" if gender == "female" else "ся"} создавать свои календари сам{"а" if gender == "female" else ""}', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    
    return ASK_TYPE

async def ask_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    query = update.callback_query 
    await query.answer()
    answer = query.data
    user_data = await get_user_data(update.effective_user.id) 
    gender = user_data['gender']

    await context.bot.delete_message(
        chat_id = query.message.chat.id,
        message_id = query.message.message_id
    )

    # Надо добавить в PostgreSQl, какой вопрос был задан, чтобы понять, на что был получен ответ. 
    # В столбце data храним JSON вида {activity : (start, end)}. На этом этапе передаем {activity : None} в зашифрованном виде

    if answer == 'education': 
        text = f'Во сколько лет ты пош{"ла" if gender == "female" else "ел"} в школу и во сколько закончил{"а" if gender == "female" else ""} или закончишь учебу? Напиши одним сообщением в формате: «С 7 до 22 лет»'
        await set_empty_event(update.effective_user.id, 'Образование', first = True)

    elif answer == 'school': 
        text = f'Во сколько лет ты пош{"ла" if gender == "female" else "ел"} в школу и сколько классов отучил{"ась" if gender == "female" else "ся"}? Напиши одним сообщением в формате: «В 7 лет, 11 классов»'
        await set_empty_event(update.effective_user.id, 'Школа', first = True)

    elif answer == 'smoking': 
        text = f'Напиши возраст, в котором ты начал{"а" if gender == "female" else ""} курить. Например, напиши «В 16 лет».\n\nЕсли уже бросил{"а" if gender == "female" else ""}, то напиши, во сколько это было. Например, «С 16 до 23 лет».'
        await set_empty_event(update.effective_user.id, 'Курение', first = True)

    elif answer == 'family': 
        text = 'Когда у вас начались отношения? Напиши дату в формате ДД.ММ.ГГГГ, например, 19.01.2004.\n\nЕсли хочешь увидеть уже законченные отношения, напиши дату в формате «19.01.2004 - 27.02.2020».'
        await set_empty_event(update.effective_user.id, 'Отношения', first = True)

    else: 
        text = 'С какого возраста ты работаешь? Ответь в формате «С 16 лет» или «С 16 до 49 лет»'
        await set_empty_event(update.effective_user.id, 'Работа', first = True)

    await asyncio.sleep(random.uniform(1, 3))
    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = text, 
        parse_mode   = 'Markdown', 
    )
    return ASK_DATE

async def create_second_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    events = await get_empty_event(update.effective_user.id)
    event_type = next(iter(events[0]))
    answer = update.message.text 

    user_data = await get_user_data(update.effective_user.id)
    day, month, year = map(int, user_data['birth'].split('.'))
    birth = date(year, month, day)

    if event_type == 'Школа': 
        try: 
            age, length = map(int, re.search(r'(\d+).*?(\d+)', answer).groups())
            start = date(year + age + ((month, day) > (8, 31)), 9, 1)
            end = date(start.year + length, 6, 20)
            event = (start, end)
        except: 
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = 'Не могу прочитать твой текст😔 Напиши возраст еще раз, в формате «С 16 лет» или «С 16 до 23 лет»', 
                parse_mode   = 'Markdown', 
            )
    elif event_type == 'Образование': 
            try: 
                start, end = list(map(int, re.findall(r'\d+', answer)))
                start = date(year + start + ((month, day) > (8, 31)), 9, 1)
                end = date(year + end + ((month, day) > (8, 31)), 6, 20)
                event = (start, end)
            except: 
                await context.bot.send_message(
                    chat_id      = update.effective_chat.id,
                    text         = 'Не могу прочитать твой текст😔 Напиши возраст еще раз, в формате «С 7 до 22 лет»', 
                    parse_mode   = 'Markdown', 
                ) 
    else: 
        if event_type == 'Курение': 
            try: 
                dates = list(map(int, re.findall(r'\d+', answer)))
            except: 
                await context.bot.send_message(
                    chat_id      = update.effective_chat.id,
                    text         = 'Не могу прочитать твой текст😔 Напиши возраст еще раз, в формате «С 16 лет» или «С 16 до 23 лет»', 
                    parse_mode   = 'Markdown', 
                )
        elif event_type == 'Отношения': 
            try: 
                dates = [datetime.strptime(d, '%d.%m.%Y').date() for d in re.findall(r'\d{2}\.\d{2}\.\d{4}', answer)]
            except: 
                await context.bot.send_message(
                    chat_id      = update.effective_chat.id,
                    text         = 'Не могу прочитать твой текст😔 Напиши даты еще раз, в формате «19.01.2004» или «19.01.2004 - 27.02.2020»', 
                    parse_mode   = 'Markdown', 
                )
        else: 
            try: 
                dates = list(map(int, re.findall(r'\d+', answer)))
            except: 
                await context.bot.send_message(
                    chat_id      = update.effective_chat.id,
                    text         = 'Не могу прочитать твой текст😔 Напиши возраст еще раз, в формате «С 16 лет» или «С 16 до 49 лет»', 
                    parse_mode   = 'Markdown', 
                )
        if len(dates) == 1: 
            event = date(year + dates[0] + ((month, day) > (8, 31)), 1, 1)
        else: 
            start, end = sorted(dates)
            start = date(year + start + ((month, day) > (8, 31)), 1, 7)
            end   = date(year + end + ((month, day) > (8, 31)), 12, 31)
            event = (start, end)
    
    filename = f'tmp/{secrets.token_hex(8)}.png'
    female = user_data['gender'] == 'female'
    create_calendar(birth, fname = filename, female = female, event = event, label = event_type)

    stop_event.set()
    await typing_task
    with open(filename, 'rb') as photo:
        await context.bot.send_document(
            chat_id    = update.effective_chat.id,
            document   = photo,
            caption    = f'Нанесла даты на календарь — смотри, как это выглядит в масштабах твоей жизни.', 
            parse_mode = 'Markdown'
        )
    
    return ConversationHandler.END 