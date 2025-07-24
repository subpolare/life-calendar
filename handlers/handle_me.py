from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

import asyncio, os, re, warnings
from dotenv import load_dotenv

from utils.typing import _keep_typing
from utils.dbtools import get_user_data, set_name, set_birth, set_gender, user_exists

warnings.filterwarnings('ignore')
load_dotenv()

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_PORT      = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')

ME_ACTION, ME_NAME, ME_BIRTHDAY, ME_GENDER = range(4)

async def handle_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exist = await user_exists(update.effective_user.id)
    if not exist:
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Похоже, я ещё ничего о тебе не знаю. Нажми /start, чтобы зарегистрироваться.',
            parse_mode = 'Markdown',
        )
        return ConversationHandler.END

    user_data = await get_user_data(update.effective_user.id)
    gender = user_data.get('gender')
    name = user_data.get('name')
    birth = user_data.get('birth')

    keyboard = [
        [InlineKeyboardButton('Имя', callback_data = 'name'), InlineKeyboardButton('Дату рождения', callback_data = 'birth')],
        [InlineKeyboardButton('Пол', callback_data = 'gender'), InlineKeyboardButton('Ничего', callback_data = 'stop')]
    ]

    gender_text = {'male': 'Парень', 'female': 'Девушка'}.get(gender, 'не указан')

    intro = 'Вот, что я о тебе уже знаю:\n\n'
    if name: 
        name_str   = f'Тебя зовут {name} и ты {"девушка" if gender == "female" else "парень"}\n' 
    if birth: 
        birth_str  = f'Ты родил{"ась" if gender == "female" else "ся"} {birth}\n\n'
    outro = 'Что хочешь поменять?' 
    text = intro + '_' + name_str + birth_str + '_' + outro

    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = text,
        parse_mode   = 'Markdown',
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ME_ACTION

async def me_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    answer = query.data

    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)

    if answer == 'name':
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Как мне к тебе обращаться?',
            parse_mode = 'Markdown'
        )
        return ME_NAME
    elif answer == 'birth':
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Когда у тебя День рождения? Напиши дату в формате ДД.ММ.ГГГГ',
            parse_mode = 'Markdown'
        )
        return ME_BIRTHDAY
    elif answer == 'gender':
        keyboard = [[
            InlineKeyboardButton('Парень', callback_data = 'male'),
            InlineKeyboardButton('Девушка', callback_data = 'female')
        ]]
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = 'Ты парень или девушка?',
            parse_mode   = 'Markdown',
            reply_markup = InlineKeyboardMarkup(keyboard)
        )
        return ME_GENDER
    else:
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Хорошо, если передумаешь — пиши /me',
            parse_mode = 'Markdown'
        )
        return ConversationHandler.END

async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    await set_name(update.effective_user.id, update.message.text)

    keyboard = [
        [InlineKeyboardButton('Имя', callback_data = 'name')],
        [InlineKeyboardButton('День рождения', callback_data = 'birth')],
        [InlineKeyboardButton('Пол', callback_data = 'gender')],
        [InlineKeyboardButton('Закончить', callback_data = 'stop')]
    ]
    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = 'Обновила имя. Что-нибудь ещё?',
        parse_mode   = 'Markdown',
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ME_ACTION

async def change_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', update.message.text.strip()):
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Что-то не так с форматом даты. Пожалуйста, напиши её в формате ДД.ММ.ГГГГ',
            parse_mode = 'Markdown'
        )
        return ME_BIRTHDAY

    await set_birth(update.effective_user.id, update.message.text.strip())

    keyboard = [
        [InlineKeyboardButton('Имя', callback_data = 'name'), InlineKeyboardButton('Дату рождения', callback_data = 'birth')],
        [InlineKeyboardButton('Пол', callback_data = 'gender'), InlineKeyboardButton('Закончить', callback_data = 'stop')]
    ]
    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = 'День рождения обновила. Что-нибудь ещё?',
        parse_mode   = 'Markdown',
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ME_ACTION

async def change_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    query = update.callback_query
    await query.answer()
    gender = query.data

    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
    await set_gender(update.effective_user.id, gender)

    keyboard = [
        [InlineKeyboardButton('Имя', callback_data = 'name'), InlineKeyboardButton('Дату рождения', callback_data = 'birth')],
        [InlineKeyboardButton('Пол', callback_data = 'gender'), InlineKeyboardButton('Закончить', callback_data = 'stop')]
    ]
    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = 'Обновила твой пол. Хочешь поменять что-то еще?',
        parse_mode   = 'Markdown',
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ME_ACTION
