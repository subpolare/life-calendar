from handlers.handle_start import ASK_BIRTHDAY, ASK, ASK_NAME, ASK_GENDER
from handlers.handle_start import handle_start, ask, ask_name, ask_gender, ask_dates

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

from dotenv import load_dotenv
import logging, os, os, warnings
warnings.filterwarnings('ignore')
load_dotenv()

LIFE_BOT_TOKEN = os.getenv('LIFE_BOT_TOKEN')
STAT_BOT_TOKEN = os.getenv('STAT_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_PORT      = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')
ENCRYPTION_KEY     = os.getenv('ENCRYPTION_KEY')

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ———————————————————————————————————————— INITIALIZING BOT ————————————————————————————————————————


async def cancel(update: Update, context: ContextTypes. DEFAULT_TYPE):
    await update.message.reply_text('Хорошо, если что — я всегда на связи!')
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(LIFE_BOT_TOKEN).build()
    print('✅ The bot has successfully launched and is working while you are drinking tea.')

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', handle_start)],
        states = {
            ASK_BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask)],
            ASK         : [CallbackQueryHandler(ask_name)],
            ASK_NAME    : [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
            ASK_GENDER  : [CallbackQueryHandler(ask_dates)],
        },
        fallbacks = [CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()