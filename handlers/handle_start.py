from telegram.constants import ChatAction
from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from datetime import date
from dotenv import load_dotenv
from security import encryption
from life_calendar import calendar
import asyncio, random, os, secrets, re, warnings, asyncpg, json
warnings.filterwarnings('ignore')
load_dotenv()

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_PORT      = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')

async def _keep_typing(chat_id: int, bot, stop_event: asyncio.Event):
    try:
        while not stop_event.is_set():
            await bot.send_chat_action(chat_id = chat_id, action = ChatAction.TYPING)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout = 4.5)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        pass

# ———————————————————————————————————————— DATABASE USING ————————————————————————————————————————

async def get_database_pool():
    return await asyncpg.create_pool(DATABASE_URL)

async def get_or_create_user_key(user_id: int, conn):
    res = await conn.fetchrow('SELECT key FROM users WHERE id = $1;', user_id)
    if res and res['key']:
        key_record = json.loads(res['key'])
        user_key = encryption.decrypt_key(key_record)
        return user_key
    else:
        # Создаем новый ключ, шифруем мастер-ключом и сохраняем
        user_key = encryption.generate_user_key()
        key_record = encryption.encrypt_key(user_key)
        await conn.execute('''
            UPDATE users SET key = $2 WHERE id = $1;
        ''', user_id, json.dumps(key_record))
        return user_key

async def set_birth(user_id: int, birth: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(birth.encode(), user_key)
        await conn.execute('''
            INSERT INTO users(id, birth) VALUES($1, $2)
            ON CONFLICT (id) DO UPDATE SET birth = EXCLUDED.birth;
        ''', user_id, json.dumps(enc))
    await pool.close()

async def set_name(user_id: int, name: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(name.encode(), user_key)
        await conn.execute('UPDATE users SET name = $2 WHERE id = $1;', user_id, json.dumps(enc))
    await pool.close()

async def set_gender(user_id: int, gender: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(gender.encode(), user_key)
        await conn.execute('UPDATE users SET gender = $2 WHERE id = $1;', user_id, json.dumps(enc))
    await pool.close()

async def get_user_data(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        res = await conn.fetchrow('SELECT name, birth, gender, key FROM users WHERE id = $1;', user_id)
        user_key = encryption.decrypt_key(json.loads(res['key']))
        data = {}
        for k in ['name', 'birth', 'gender']:
            if res[k]:
                data[k] = encryption.decrypt(json.loads(res[k]), user_key).decode()
        return data

# ———————————————————————————————————————— START HANDLERS ————————————————————————————————————————

ASK_BIRTHDAY, ASK, ASK_NAME, ASK_GENDER = range(4)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )
    
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
    
    context.user_data['birthday'] = update.message.text
    await set_birth(update.effective_user.id, context.user_data['birthday'])
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
        InlineKeyboardButton('Конечно!', callback_data = 'yes'),
        InlineKeyboardButton('Нет, но я за ним вернусь', callback_data = 'no')
    ]]
    await asyncio.sleep(random.uniform(1, 3))
    stop_event.set()
    await typing_task
    await context.bot.send_message(
         chat_id      = update.effective_chat.id,
         text         = f'Хочешь, создам календарь на основе именно твоей жизни?', 
         parse_mode   = 'Markdown', 
         reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ASK

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )

    query = update.callback_query 
    await query.answer()
    answer = query.data

    await context.bot.delete_message(
        chat_id =query.message.chat.id,
        message_id =query.message.message_id
    )

    if answer == 'yes': 
        text = 'Ура! Тогда начнем со знакомства. <b>Как тебя зовут?</b> Напиши только имя.\n\n<i>Если интересно, как я храню твои данные, вот <a href="https://github.com/subpolare/life-calendar/blob/main/security/secutiry.md">подробный рассказ</a>. Коротко — ни я, ни мой создатель не можем посмотреть их без твоего ведома.</i>'
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = text, 
            parse_mode  = 'HTML'
        )

        stop_event.set()
        await typing_task
        return ASK_NAME
    else:
        text = 'Буду ждать, пока ты вернешься! Нажми /start, если решишь создать новый календарь.' 
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = text, 
            parse_mode  = 'Markdown'
        )

        stop_event.set()
        await typing_task
        return ConversationHandler.END

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )
    await asyncio.sleep(random.uniform(1, 3))
    context.user_data['name'] = update.message.text
    await set_name(update.effective_user.id, context.user_data['name'])

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

async def ask_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )

    query = update.callback_query 
    await query.answer()
    gender = query.data

    await context.bot.delete_message(
        chat_id =query.message.chat.id,
        message_id =query.message.message_id
    )
    context.user_data['gender'] = gender
    await set_gender(update.effective_user.id, context.user_data['gender'])

    if gender == 'male':
        text = f'Теперь точно знакомы!'
    else:  
        text = f'Теперь точно знакомы!'
    
    stop_event.set()
    await typing_task

    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = text, 
        parse_mode   = 'Markdown', 
    )

    return ConversationHandler.END 