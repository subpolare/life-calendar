from telegram.ext import ContextTypes
from telegram import Update

import os, warnings
from dotenv import load_dotenv
warnings.filterwarnings('ignore')
load_dotenv()

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_PORT      = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')

# ———————————————————————————————————————— CALENDAR HANDLERS ————————————————————————————————————————


async def handle_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass