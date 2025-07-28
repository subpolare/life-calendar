from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from datetime import date
from dotenv import load_dotenv
from utils.dateparser import parse_dates
from utils.typing_task import keep_typing
from utils.life_calendar import create_calendar
import asyncio, random, os, secrets, re, warnings
from utils.dbtools import (
    set_birth, set_name, set_gender, get_user_data,
    set_empty_event, set_event, user_exists, delete_data
)
from handlers.habits import ask_habits_intro, habits_intro_answer, habits_question_answer
warnings.filterwarnings('ignore')
load_dotenv()

# ———————————————————————————————————————— START HANDLERS ————————————————————————————————————————

ASK_BIRTHDAY, ASK, ASK_NAME, ASK_GENDER, ASK_TYPE, ASK_DATE, ASK_MORE, HABIT_INTRO, HABIT_Q, DELETE_DATA = range(10)

@keep_typing
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exist = await user_exists(update.effective_user.id) 
    if exist: 
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
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            caption    = f'Держи свой первый календарь жизни. Скинула файлом, чтобы было видно все детали.\n\nПока он про среднего человека в России, но хочется сделать его лично для тебя', 
            parse_mode = 'Markdown'
        )
    
    os.remove(filename)
    keyboard = [[
        InlineKeyboardButton('Конечно!', callback_data = 'yes'),
        InlineKeyboardButton('Нет, но я вернусь', callback_data = 'no')
    ]]
    await asyncio.sleep(random.uniform(1, 3))
    
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

    await asyncio.sleep(random.uniform(1, 3))
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
async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(random.uniform(1, 3))
    context.user_data['name'] = update.message.text
    await set_name(update.effective_user.id, context.user_data['name'])

    keyboard = [[
        InlineKeyboardButton('Парень', callback_data = 'male'),
        InlineKeyboardButton('Девушка', callback_data = 'female')
    ]]
    
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Рада познакомиться, {context.user_data["name"]}! Извини за вопрос, но ты парень или девушка? Отвечай честно: это нужно для твоего календаря.', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ASK_GENDER

@keep_typing
async def ask_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    return await ask_event(update, context)

@keep_typing
async def ask_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = context.user_data.get('gender', 'male')
    added = context.user_data.get('added_events', set())
    keyboard = []
    row1 = []
    if 'education' not in added:
        row1.append(InlineKeyboardButton('Школу + университет', callback_data = 'education'))
    if row1:
        keyboard.append(row1)
    row2 = []
    if 'school' not in added:
        row2.append(InlineKeyboardButton('Только школу', callback_data = 'school'))
    if 'job' not in added:
        row2.append(InlineKeyboardButton('Работу', callback_data = 'job'))
    if row2:
        keyboard.append(row2)
    if 'smoking' not in added:
        keyboard.append([InlineKeyboardButton('Сколько я уже курю', callback_data = 'smoking')])
    if added:
        keyboard.append([InlineKeyboardButton('Давай закончим', callback_data = 'finish')])

    if keyboard:
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = f'Что хочешь добавить? Давай начнем с чего-то одного, чтобы ты научил{"ась" if gender == "female" else "ся"} создавать свои календари сам{"а" if gender == "female" else ""}',
            parse_mode   = 'Markdown',
            reply_markup = InlineKeyboardMarkup(keyboard)
        )
        return ASK_TYPE
    else:
        return await ask_habits_intro(update, context)

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
    if not gender:
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Упс, не получилось получить твои данные. Давай начнём заново: нажми /start',
            parse_mode = 'Markdown',
        )
        return ConversationHandler.END

    await context.bot.delete_message(
        chat_id = query.message.chat.id,
        message_id = query.message.message_id
    )

    first = not context.user_data.get('added_events')
    context.user_data['event_type'] = answer
    if answer == 'education':
        text = f'Во сколько лет ты пош{"ла" if gender == "female" else "ел"} в школу и во сколько закончил{"а" if gender == "female" else ""} или закончишь учебу? Напиши одним сообщением в формате: «С 7 до 22 лет»'
        await set_empty_event(update.effective_user.id, 'Образование', first = first)

    elif answer == 'school':
        text = f'Во сколько лет ты пош{"ла" if gender == "female" else "ел"} в школу и сколько классов отучил{"ась" if gender == "female" else "ся"}? Напиши одним сообщением в формате: «В 7 лет, 11 классов»'
        await set_empty_event(update.effective_user.id, 'Школа', first = first)

    elif answer == 'smoking':
        text = f'Напиши возраст, в котором ты начал{"а" if gender == "female" else ""} курить. Например, напиши «В 16 лет».\n\nЕсли уже бросил{"а" if gender == "female" else ""}, то напиши, во сколько это было. Например, «С 16 до 23 лет».'
        await set_empty_event(update.effective_user.id, 'Курение', first = first)

    else:
        text = 'С какого возраста ты работаешь? Ответь в формате «С 16 лет» или «С 16 до 49 лет»'
        await set_empty_event(update.effective_user.id, 'Работа', first = first)

    await asyncio.sleep(random.uniform(1, 3))
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = text, 
        parse_mode   = 'Markdown', 
    )
    return ASK_DATE

@keep_typing
async def create_second_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event_key = context.user_data.get('event_type')
    key_map = {
        'education': 'Образование',
        'school': 'Школа',
        'smoking': 'Курение',
        'job': 'Работа'
    }
    event_type = key_map.get(event_key)
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
                text         = 'Не могу прочитать твой текст😔 Напиши возраст еще раз, в формате «В 7 лет, 11 классов»', 
                parse_mode   = 'Markdown', 
            )
            return ASK_DATE
    elif event_type == 'Образование': 
        try: 
            m = re.search(r'(\d+).*?(\d+)', answer)
            start, end = map(int, m.groups())
            start = date(year + start + ((month, day) > (8, 31)), 9, 1)
            end = date(year + end + ((month, day) > (8, 31)), 6, 20)
            event = (start, end)
        except: 
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = 'Не могу прочитать твой текст😔 Напиши возраст еще раз, в формате «С 7 до 22 лет»', 
                parse_mode   = 'Markdown', 
            ) 
            return ASK_DATE
    else:
        try:
            event = parse_dates(answer, date(year, month, day))
        except ValueError:
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = 'Не могу прочитать твой текст😔 Напиши возраст еще раз, в формате «С 16 лет» или «С 16 до 23 лет»',
                parse_mode   = 'Markdown',
            )
            return ASK_DATE

    await set_event(update.effective_user.id, event_type, event)
    key_map = {
        'Образование': 'education',
        'Школа': 'school',
        'Курение': 'smoking',
        'Работа': 'job'
    }
    ev_key = key_map.get(event_type)
    if ev_key:
        context.user_data.setdefault('added_events', set()).add(ev_key)

    filename = f'tmp/{secrets.token_hex(8)}.png'
    female = user_data['gender'] == 'female'
    create_calendar(birth, fname = filename, female = female, event = event, label = event_type)

    with open(filename, 'rb') as photo:
        await context.bot.send_document(
            chat_id    = update.effective_chat.id,
            document   = photo,
            caption    = f'Нанесла даты на календарь — смотри, как это выглядит в масштабах твоей жизни. ',
            parse_mode = 'Markdown'
        )
        os.remove(filename)

    await asyncio.sleep(3)

    keyboard = [[
        InlineKeyboardButton('Да', callback_data = 'more_yes'),
        InlineKeyboardButton('Нет', callback_data = 'more_no')
    ]]
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = 'Хочешь заполнить остальные? Это всегда можно сделать позже и добавить на календарь любые события.',
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

    await asyncio.sleep(3)
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = 'Теперь ты можешь создавать свои собственные календари с любыми событиями из жизни. Для этого нажми на /calendar\n\nА еще вступай в наше закрытое комьюнити, для этого нажми на /community',
        parse_mode   = 'Markdown',
    )
    return ConversationHandler.END