from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import telegram

from typing import Any
from datetime import date
from dotenv import load_dotenv
from utils.dateparser import parse_dates
from utils.typing_task import keep_typing
import os, warnings, asyncio, secrets, random, logging
from utils.life_calendar import create_calendar
from utils.dbtools import get_user_data, set_event, get_events, set_action, get_action, clear_action, delete_event, user_exists
warnings.filterwarnings('ignore')
load_dotenv()

logger = logging.getLogger(__name__)

ACTION_TYPE, EVENT_NAME_POLL, EVENT_NAME_TEXT = range(3)
MONTHS = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря',}

def _fmt(d: date) -> str:
    return f'{d.day} {MONTHS[d.month]} {d.year}'

def _first_date(item: dict[str, Any]) -> date:
    _, dates = next(iter(item.items()))
    first = dates if isinstance(dates, str) else dates[0]
    return date.fromisoformat(first)

def events2text(events: list[dict[str, Any]]) -> str:
    lines = []
    for i, item in enumerate(sorted(events, key = _first_date)):
        name, dates = next(iter(item.items()))
        if isinstance(dates, str):
            dates = [dates]
        dates = [date.fromisoformat(d) for d in dates]

        if len(dates) == 1:
            lines.append(f'{i + 1}. {name}: с {_fmt(dates[0])} года.')
        else:
            start, end = sorted(dates)
            lines.append(f'{i + 1}. {name}: {_fmt(start)} – {_fmt(end)} года.')
    return '\n'.join(lines)

def _to_event(obj):
    if isinstance(obj, list):
        dates = [date.fromisoformat(d) for d in obj]
        return dates[0] if len(dates) == 1 else tuple(dates[:2])
    if isinstance(obj, str):
        return date.fromisoformat(obj)
    return obj

# ———————————————————————————————————————— CALENDAR HANDLERS ————————————————————————————————————————

@keep_typing
async def handle_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info('User %s is creating a calendar', update.effective_user.username)
    await asyncio.sleep(3)
    exist = await user_exists(update.effective_user.id) 
    if not exist: 
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = f'Чтобы использовать эту команду, тебе сначала нужно зарегестрироваться. Для этого нажми на /start', 
            parse_mode  = 'Markdown'
        )
        return ConversationHandler.END

    events = await get_events(update.effective_user.id) 
    await clear_action(update.effective_user.id) 
    events = events2text(events)
    keyboard = [
            [InlineKeyboardButton('Добавить новое событие', callback_data = 'add')],
            [InlineKeyboardButton('Хочу кое-что удалить',   callback_data = 'remove')],
            [InlineKeyboardButton('Давай кое-что поменяем', callback_data = 'edit')],
            [InlineKeyboardButton('Рисуем календарь!',      callback_data = 'calendar')],
            [InlineKeyboardButton('Ничего не хочу',         callback_data = 'stop')],
    ]
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Вот, из каких событий состоит твоя жизнь.\n\n_{events}_\n\nХочешь что-то поменять? Или, может, нарисовать календарь?', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ACTION_TYPE

@keep_typing
async def user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    logger.info('User %s selected action %s', update.effective_user.username, action)
    await set_action(update.effective_user.id, action)

    user_data = await get_user_data(update.effective_user.id)
    gender = user_data['gender']

    events = await get_events(update.effective_user.id)
    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
    await asyncio.sleep(3)
    if action == 'stop': 
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = 'Буду ждать, пока ты вернешься! Нажми /calendar, если захочешь создать новый календарь.' , 
            parse_mode  = 'Markdown'
        )
        return ConversationHandler.END
    elif action == 'add': 
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = (
                f'*Что бы ты хотел{"а" if gender == "female" else ""} добавить на календарь?* Напиши в формате «Курю: с 1.09.2021» или «Занималась плаванием: с 2023 до 2025».\n\n'
                f'Пиши даты в формате ДД.ММ.ГГГГ. Еще можешь написать возраст, например, «Плавание: с 4 до 22 лет» или «Курю: с 17 лет».\n\n'
                f'_Главное, поставь двоеточие после названия, чтобы я не запуталась, а с остальным я разберусь._'
            ), 
            parse_mode = 'Markdown'
        )
        return EVENT_NAME_TEXT
    else:
        keyboard = []
        for i, item in enumerate(sorted(events, key = _first_date)):
            name, _ = next(iter(item.items()))
            keyboard.append([InlineKeyboardButton(f'{i + 1}. {name}', callback_data = str(i))])
        if action == 'remove': 
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = f'Хорошо, что нужно удалить?', 
                parse_mode   = 'Markdown', 
                reply_markup = InlineKeyboardMarkup(keyboard)
            )
        elif action == 'edit': 
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = f'Какое событие хочешь отредактировать?', 
                parse_mode   = 'Markdown', 
                reply_markup = InlineKeyboardMarkup(keyboard)
            ) 
        elif action == 'calendar': 
            keyboard.append([InlineKeyboardButton(f'Просто календарь, без всего', callback_data = 'empty')])
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = f'Что нарисовать на твоем календаре? Выбери нужный вариант', 
                parse_mode   = 'Markdown', 
                reply_markup = InlineKeyboardMarkup(keyboard)
            ) 
        return EVENT_NAME_POLL 

@keep_typing
async def add_new_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(3)
    answer = update.message.text
    logger.info('User %s added a new event', update.effective_user.username)

    user_data = await get_user_data(update.effective_user.id)
    day, month, year = map(int, user_data['birth'].split('.'))

    try: 
        event_type, _ = answer.split(':')
    except: 
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = 'Не могу прочитать твой текст😔 Напиши событие, потом двоеточие и в конце либо даты в формате ДД.ММ.ГГГГ, либо возраст.\n\n_Например, «Плавание: с 16 до 23 лет» или «Дзюдо: с 25.11.2020»_', 
            parse_mode   = 'Markdown', 
        )
        return EVENT_NAME_TEXT
    try:
        event = parse_dates(answer, date(year, month, day))
    except ValueError:
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = 'Не могу прочитать твой текст😔 Напиши событие, потом двоеточие и в конце либо даты в формате ДД.ММ.ГГГГ, либо возраст.\n\n_Например, «Плавание: с 16 до 23 лет» или «Дзюдо: с 25.11.2020»_',
            parse_mode   = 'Markdown',
        )
        return EVENT_NAME_TEXT
    await set_event(update.effective_user.id, event_type, event)
    return await handle_calendar(update, context)

@keep_typing
async def action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.callback_query.message if update.callback_query else update.effective_message
    try:
        await context.bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    except telegram.error.TelegramError:
        pass
    await asyncio.sleep(3)

    query = update.callback_query
    await query.answer()
    action = await get_action(update.effective_user.id)
    logger.info('Executing action %s for user %s', action, update.effective_user.username)
    if query.data != 'empty':
        index = int(query.data)
        events = await get_events(update.effective_user.id)
        events_sorted = sorted(events, key = _first_date)
        item = events_sorted[index]
        event_type, event_dates = next(iter(item.items()))

    if action == 'remove':
        await delete_event(update.effective_user.id, event_type, event_dates)
        logger.info('Removed event for user %s', update.effective_user.username)
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = 'Хорошо, удалила!', 
            parse_mode   = 'Markdown', 
        )
        return await handle_calendar(update, context)
    
    elif action == 'edit':
        await delete_event(update.effective_user.id, event_type, event_dates)
        name = event_type[0].lower() + event_type[1:] if event_type else event_type
        logger.info('Editing event for user %s', update.effective_user.username)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = (
                f'*Напиши про {name} с новым названием или датой в таком формате:* «Курю: с 1.09.2021» или «Занималась плаванием: с 2023 до 2025».\n\n'
                f'Пиши даты в формате ДД.ММ.ГГГГ. Еще можешь написать возраст, например, «Плавание: с 4 до 22 лет» или «Курю: с 17 лет».\n\n'
                f'_Главное, поставь двоеточие после названия, чтобы я не запуталась, а с остальным я разберусь._'
            ), 
            parse_mode = 'Markdown'
        )
        return EVENT_NAME_TEXT
    
    elif action == 'calendar':
        user_data = await get_user_data(update.effective_user.id)
        day, month, year = map(int, user_data['birth'].split('.'))

        birth = date(year, month, day)
        female = user_data['gender'] == 'female'
        filename = f'tmp/{secrets.token_hex(8)}.png'
        
        logger.info('Drawing calendar for user %s', update.effective_user.username)
        create_calendar(
            birth, fname = filename, female = female,
            event = _to_event(event_dates) if query.data != 'empty' else None,
            label = event_type if query.data != 'empty' else None
        )
        with open(filename, 'rb') as photo:
            if query.data != 'empty': 
                phrases = [
                    'Отметила даты в календаре — посмотри, как это смотрится в контексте всей твоей жизни. Захочешь еще один — пиши /calendar',
                    'Проставила события на календаре — смотри, как выглядит общая картина. Для нового календаря нажми /calendar',
                    'Внесла даты в календарь — оцени масштаб в рамках всего твоего жизненного пути. Нужен еще один календарь — пиши /calendar',
                    'Взгляни на это в перспективе всей жизни. Хочешь создать новый календарь — нажми /calendar',
                    'Зафиксировала даты на календаре. Для следующего пиши /calendar',
                    'Оцени это в масштабе всего твоего существования. Нужен новый календарь — пиши /calendar',
                    'Получилась целая временная панорама твоей жизни! Для создания нового календаря пиши /calendar',
                    'Вот, как это выглядит в твоем жизненном контексте. Захочешь еще один календарь — пиши /calendar',
                    'Внесла это в календарь — взгляни на масштабы своего пути. Хочешь сделать еще один календарь? Пиши /calendar',
                    'Смотри, как это выглядит в рамках всей твоей жизни. Для нового календаря — пиши /calendar'
                ]
                message = random.choice(phrases)
            else: 
                message = 'Готово, нарисовала твой новый календарь'
            await context.bot.send_document(
                chat_id    = update.effective_chat.id,
                document   = photo,
                caption    = message, 
                parse_mode = 'Markdown'
            )
            os.remove(filename)
        return ConversationHandler.END

