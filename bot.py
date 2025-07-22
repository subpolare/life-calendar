from handlers.handle_calendar import ACTION_TYPE, EVENT_NAME_POLL, EVENT_NAME_TEXT
from handlers.handle_calendar import handle_calendar, user_action, add_new_event, action
from handlers.handle_start import ASK_BIRTHDAY, ASK, ASK_NAME, ASK_GENDER, ASK_TYPE, ASK_DATE
from handlers.handle_start import handle_start, ask, ask_name, ask_gender, ask_type, ask_dates, create_second_calendar

import telegram 
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

import os, warnings
from dotenv import load_dotenv
warnings.filterwarnings('ignore')
load_dotenv()

LIFE_BOT_TOKEN = os.getenv('LIFE_BOT_TOKEN')
request = HTTPXRequest(
    connection_pool_size = 50.0,
    pool_timeout         = 30.0, 
    connect_timeout      = 10.0,
    read_timeout         = 60.0,
    write_timeout        = 60.0,
    media_write_timeout  = 120.0,
)

# ———————————————————————————————————————— INITIALIZING BOT ————————————————————————————————————————

async def cancel(update: Update, context: ContextTypes. DEFAULT_TYPE):
    await update.message.reply_text('Хорошо, если передумаешь — я всегда тут')
    return ConversationHandler.END

def error_handler(update, context):
    if isinstance(context.error, telegram.error.Forbidden):
        return

def main():
    app = ApplicationBuilder().token(LIFE_BOT_TOKEN).request(request).build()
    app.add_error_handler(error_handler)
    print('✅ The bot has successfully launched and is working while you are drinking tea.')

    start_conversation = ConversationHandler(
        entry_points = [CommandHandler('start', handle_start)],
        states = {
            ASK_BIRTHDAY : [MessageHandler(filters.TEXT & ~filters.COMMAND, ask)],
            ASK          : [CallbackQueryHandler(ask_name)],
            ASK_NAME     : [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            ASK_GENDER   : [CallbackQueryHandler(ask_type)],
            ASK_TYPE     : [CallbackQueryHandler(ask_dates)],
            ASK_DATE     : [MessageHandler(filters.TEXT & ~filters.COMMAND, create_second_calendar)],
        },
        fallbacks = [CommandHandler('cancel', cancel)]
    )

    calendar_conversation = ConversationHandler(
        entry_points = [CommandHandler('calendar', handle_calendar)],
        states = {
            ACTION_TYPE     : [CallbackQueryHandler(user_action)],
            EVENT_NAME_POLL : [CallbackQueryHandler(action)],
            EVENT_NAME_TEXT : [MessageHandler(filters.TEXT & ~filters.COMMAND, add_new_event)],
        },
        fallbacks = [CommandHandler('cancel', cancel)]
    )

    app.add_handler(start_conversation)
    app.add_handler(calendar_conversation)
    app.run_polling()

if __name__ == '__main__':
    main()