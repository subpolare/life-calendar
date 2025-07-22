from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from typing import Any
from datetime import date
from dotenv import load_dotenv
from utils.typing import _keep_typing
from life_calendar import create_calendar
import os, warnings, asyncio, re, datetime
from utils.dbtools import get_user_data, set_event, get_events, set_action, get_action, clear_action
warnings.filterwarnings('ignore')
load_dotenv()

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_PORT      = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')

ACTION_TYPE, EVENT_NAME_POLL, EVENT_NAME_TEXT = range(3)
MONTHS = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря',}

def _fmt(d: date) -> str:
    return f'{d.day} {MONTHS[d.month]} {d.year}'

def events2text(events: list[dict[str, Any]]) -> str:
    def _first_date(item: dict[str, Any]) -> date:
        _, dates = next(iter(item.items()))
        first = dates if isinstance(dates, str) else dates[0]
        return date.fromisoformat(first)

    lines = []
    for i, item in enumerate(sorted(events, key=_first_date)):
        name, dates = next(iter(item.items()))
        if isinstance(dates, str):
            dates = [dates]
        dates = [date.fromisoformat(d) for d in dates]

        if len(dates) == 1:
            lines.append(f'{name}: с {_fmt(dates[0])} года.')
        else:
            start, end = sorted(dates)
            lines.append(f'{i + 1}. {name}: {_fmt(start)} – {_fmt(end)} года.')
    return '\n'.join(lines)

# ———————————————————————————————————————— CALENDAR HANDLERS ————————————————————————————————————————

async def handle_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))
    await asyncio.sleep(3)

    events = await get_events(update.effective_user.id) 
    await clear_action(update.effective_user.id) 
    events = events2text(events)
    keyboard = [
            [InlineKeyboardButton('Добавить новое событие',     callback_data = 'add')],
            [InlineKeyboardButton('Удалить что-то',             callback_data = 'remove')],
            [InlineKeyboardButton('Поменять название или даты', callback_data = 'edit')],
            [InlineKeyboardButton('Нарисовать календарь',       callback_data = 'calendar')],
            [InlineKeyboardButton('Назад',                      callback_data = 'stop')],
    ]
    stop_event.set()
    await typing_task
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Вот, из каких событий состоит твоя жизнь.\n\n_{events}_\n\nХочешь что-то поменять? Или, может, нарисовать календарь?', 
        parse_mode   = 'Markdown', 
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return ACTION_TYPE

async def user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))

    query = update.callback_query 
    await query.answer()
    action = query.data
    await set_action(update.effective_user.id, action)

    user_data = await get_user_data(update.effective_user.id) 
    gender = user_data['gender']

    events = await get_events(update.effective_user.id) 
    names = [list(event.keys())[0] for event in events]
    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
    await asyncio.sleep(3)
    
    stop_event.set()
    await typing_task
    if action == 'stop': 
        stop_event.set()
        await typing_task
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
                f'**Что бы ты хотел{"а" if gender == "female" else ""} добавить на календарь?** Напиши в формате «Курю: с 1.09.2021» или «Занималась плаванием: с 2023 до 2025».\n\n'
                f'Пиши даты в формате ДД.ММ.ГГГГ. Еще можешь написать возраст, например, «Плавание: с 4 до 22 лет» или «Курю: с 17 лет».\n\n'
                f'_Главное, поставь двоеточие после названия, чтобы я не запуталась, а с остальным я разберусь._'
            ), 
            parse_mode = 'Markdown'
        )
        return EVENT_NAME_TEXT
    else:
        if action == 'remove': 
            keyboard = [InlineKeyboardButton(name, callback_data = i) for i, name in enumerate(names)] 
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = f'Что ты хочешь удалить?', 
                parse_mode   = 'Markdown', 
                reply_markup = InlineKeyboardMarkup(keyboard)
            )
        elif action == 'edit': 
            keyboard = [InlineKeyboardButton(name, callback_data = i) for i, name in enumerate(names)] 
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = f'Что ты хочешь поменять?', 
                parse_mode   = 'Markdown', 
                reply_markup = InlineKeyboardMarkup(keyboard)
            ) 
        elif action == 'calendar': 
            keyboard = [InlineKeyboardButton(name, callback_data = i) for i, name in enumerate(names)] 
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = f'Что что мне нанести на твой календарь?', 
                parse_mode   = 'Markdown', 
                reply_markup = InlineKeyboardMarkup(keyboard)
            ) 
        return EVENT_NAME_POLL 

async def add_new_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))
    await asyncio.sleep(3)
    answer = update.message.text 

    user_data = await get_user_data(update.effective_user.id)
    day, month, year = map(int, user_data['birth'].split('.'))
    birth = date(year, month, day)

    try: 
        event_type, _ = answer.split(':')
    except: 
        stop_event.set()
        await typing_task
        await context.bot.send_message(
            chat_id      = update.effective_chat.id,
            text         = 'Не могу прочитать твой текст😔 Напиши событие, потом двоеточие и в конце либо даты в формате ДД.ММ.ГГГГ, либо возраст.\n\n_Например, «Плавание: с 16 до 23 лет» или «Дзюдо: с 25.11.2020»_', 
            parse_mode   = 'Markdown', 
        )
        return EVENT_NAME_TEXT

    try:
        dates = list(map(int, re.findall(r'\d+', answer)))
        if len(dates) == 1: 
            event = date(year + dates[0] + ((month, day) > (8, 31)), 1, 1)
        elif len(dates) == 2: 
            start, end = sorted(dates)
            start = date(year + start + ((month, day) > (8, 31)), 1, 7)
            end   = date(year + end + ((month, day) > (8, 31)), 12, 31)
            event = (start, end)
        else: 
            raise ValueError(f'Expected 1 or 2 numbers')
    except: 
        try:
            dates = []
            for day, month, year in re.findall(r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b', answer):
                y = int(year)
                if y < 100:
                    y += 2000 if y < 50 else 1900
                try:
                    dates.append(date(y, int(month), int(day)))
                except ValueError:
                    continue 
            if not dates:
                raise ValueError('Не найдено ни одной даты')
            if len(dates) > 2:
                raise ValueError('Ожидалось не больше двух дат')
            event = tuple(dates) if len(dates) == 2 else dates[0]
        except: 
            stop_event.set()
            await typing_task
            await context.bot.send_message(
                chat_id      = update.effective_chat.id,
                text         = 'DateError. Не могу прочитать твой текст😔 Напиши событие, потом двоеточие и в конце либо даты в формате ДД.ММ.ГГГГ, либо возраст.\n\n_Например, «Плавание: с 16 до 23 лет» или «Дзюдо: с 25.11.2020»_', 
                parse_mode   = 'Markdown', 
            )
            return EVENT_NAME_TEXT
            
    await set_event(update.effective_user.id, event_type, event)
    stop_event.set()
    await typing_task
    return await handle_calendar(update, context)

async def action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(_keep_typing(update.effective_chat.id, context.bot, stop_event))
    await asyncio.sleep(3)

    query = update.callback_query 
    await query.answer()
    answer = query.data
    action = await get_action(update.effective_user.id)