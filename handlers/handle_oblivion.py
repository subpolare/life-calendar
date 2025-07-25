from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from utils.typing import keep_typing
from utils.dbtools import user_exists, get_user_data, delete_user

from dotenv import load_dotenv
import os, warnings, asyncio

warnings.filterwarnings('ignore')
load_dotenv()

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_PORT      = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')

DELETE_ACCOUNT = range(1)

@keep_typing
async def handle_oblivion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exist = await user_exists(update.effective_user.id)
    if not exist:
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Похоже, я ещё ничего о тебе не знаю. Нажми /start, чтобы зарегистрироваться.',
            parse_mode = 'Markdown'
        )
        return ConversationHandler.END

    user_data = await get_user_data(update.effective_user.id)
    gender = user_data.get('gender')

    keyboard = [
        [InlineKeyboardButton('Да, навсегда удаляем!', callback_data = 'yes')],
        [InlineKeyboardButton(f'Нет, я передумал{"а" if gender == "female" else ""}', callback_data = 'no')]
    ]
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = f'Уверен{"а" if gender == "female" else ""}, что хочешь стереть все данные? Это действие необратимо.',
        parse_mode   = 'Markdown',
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return DELETE_ACCOUNT

@keep_typing
async def oblivion_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    answer = query.data

    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
    if answer == 'yes':
        await delete_user(update.effective_user.id)
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Готово! Я удалила все твои настройки. Если захочешь начать заново, нажми /start.',
            parse_mode = 'Markdown'
        )
        return ConversationHandler.END
    else:
        await context.bot.send_message(
            chat_id    = update.effective_chat.id,
            text       = 'Фух, а то я испугалась...',
            parse_mode = 'Markdown'
        )
        return ConversationHandler.END
