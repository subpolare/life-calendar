from handlers.handle_calendar import ACTION_TYPE, EVENT_NAME_POLL, EVENT_NAME_TEXT
from handlers.handle_calendar import handle_calendar, user_action, add_new_event, action
from handlers.handle_start import ASK_BIRTHDAY, ASK, ASK_NAME, ASK_GENDER, ASK_TYPE, ASK_DATE, ASK_MORE, DELETE_DATA
from handlers.handle_start import handle_start, ask, ask_name, ask_gender, ask_type, ask_dates, create_second_calendar, clean_data, ask_more
from handlers.handle_oblivion import DELETE_ACCOUNT, handle_oblivion, oblivion_answer
from handlers.handle_community import handle_community, gatekeeper
from handlers.handle_help import handle_help
from handlers.handle_me import (
    ME_ACTION, ME_NAME, ME_BIRTHDAY, ME_GENDER,
    handle_me, me_option, change_name, change_birthday, change_gender,
)
from utils.dbtools import init_pool, close_pool

import telegram 
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, 
    ConversationHandler, CallbackQueryHandler, ChatJoinRequestHandler
)

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

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, telegram.error.Forbidden):
        return
    print(f'Unhandled error: {context.error}')

def main():
    application = (
        ApplicationBuilder()
        .token(LIFE_BOT_TOKEN)
        .post_init(lambda app: init_pool())
        .post_shutdown(lambda app: close_pool())
        .request(request)
        .build()
    )
    application.add_error_handler(error_handler)
    print('✅ The bot has successfully launched and is working while you are drinking tea.')

    start_conversation = ConversationHandler(
        entry_points = [CommandHandler('start', handle_start)],
        states = {
            ASK_BIRTHDAY : [MessageHandler(filters.TEXT & ~filters.COMMAND, ask)],
            DELETE_DATA  : [CallbackQueryHandler(clean_data)],
            ASK          : [CallbackQueryHandler(ask_name)],
            ASK_NAME     : [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            ASK_GENDER   : [CallbackQueryHandler(ask_type)],
            ASK_TYPE     : [CallbackQueryHandler(ask_dates)],
            ASK_DATE     : [MessageHandler(filters.TEXT & ~filters.COMMAND, create_second_calendar)],
            ASK_MORE     : [CallbackQueryHandler(ask_more)],
        },
        fallbacks = [CommandHandler('cancel', cancel)],
        allow_reentry = True
    )

    calendar_conversation = ConversationHandler(
        entry_points = [CommandHandler('calendar', handle_calendar)],
        states = {
            ACTION_TYPE     : [CallbackQueryHandler(user_action)],
            EVENT_NAME_POLL : [CallbackQueryHandler(action)],
            EVENT_NAME_TEXT : [MessageHandler(filters.TEXT & ~filters.COMMAND, add_new_event)],
        },
        fallbacks = [CommandHandler('cancel', cancel)],
        allow_reentry = True
    )

    me_conversation = ConversationHandler(
        entry_points = [CommandHandler('me', handle_me)],
        states = {
            ME_ACTION    : [CallbackQueryHandler(me_option)],
            ME_NAME      : [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name)],
            ME_BIRTHDAY  : [MessageHandler(filters.TEXT & ~filters.COMMAND, change_birthday)],
            ME_GENDER    : [CallbackQueryHandler(change_gender)],
        },
        fallbacks = [CommandHandler('cancel', cancel)],
        allow_reentry = True
    )

    oblivion_conversation = ConversationHandler(
        entry_points = [CommandHandler('oblivion', handle_oblivion)],
        states = {
            DELETE_ACCOUNT : [CallbackQueryHandler(oblivion_answer)],
        },
        fallbacks = [CommandHandler('cancel', cancel)],
        allow_reentry = True
    )

    application.add_handler(start_conversation)
    application.add_handler(calendar_conversation)
    application.add_handler(me_conversation)
    application.add_handler(oblivion_conversation)
    application.add_handler(ChatJoinRequestHandler(gatekeeper))
    application.add_handler(CommandHandler('community', handle_community))
    application.add_handler(CommandHandler('help', handle_help))
    application.run_polling()

if __name__ == '__main__':
    main()
