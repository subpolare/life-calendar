from telegram import Update
from telegram.constants import ParseMode, ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

import argparse, asyncio, datetime as dt, logging, os, pathlib, subprocess, sys, tempfile
from html2image import Html2Image
from dotenv import load_dotenv

load_dotenv()

LIFE_BOT_TOKEN = os.getenv('LIFE_BOT_TOKEN')
STAT_BOT_TOKEN = os.getenv('STAT_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_URL       = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')
ENCRYPTION_KEY     = os.getenv('ENCRYPTION_KEY')

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ───────────────────────────────────────────────────────────────────────────────
# ПУТИ И НАСТРОЙКИ ДЛЯ КАЛЕНДАРЯ
# ───────────────────────────────────────────────────────────────────────────────

BASE_DIR  = pathlib.Path(__file__).resolve().parent
LC_DIR    = BASE_DIR / 'calendar'
OUT_DIR   = LC_DIR / 'out'
NODE_OPTS = '--openssl-legacy-provider'
HTI       = Html2Image(browser='chrome',output_path=tempfile.gettempdir())


def _run(cmd: list[str], cwd: pathlib.Path, env: dict | None = None) -> None:
    '''Запуск shell-команды с проверкой кода выхода.'''
    logging.info('· %s', ' '.join(cmd))
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def _ensure_front_ready() -> None:
    '''Собрать и экспортировать фронт, если out/ ещё не готов.'''
    if not (LC_DIR / 'node_modules').exists():
        _run(['yarn', 'install'], cwd=LC_DIR)

    if not OUT_DIR.exists() or not any(OUT_DIR.iterdir()):
        env = os.environ | {'NODE_OPTIONS': NODE_OPTS}
        _run(['yarn', 'build'],        cwd=LC_DIR, env=env)
        _run(['yarn', 'next', 'export'], cwd=LC_DIR, env=env)

def _render_calendar(bday: dt.date) -> pathlib.Path:
    '''Синхронно создать PNG календаря и вернуть путь к нему.'''
    _ensure_front_ready()

    url  = (OUT_DIR / 'index.html').as_uri()
    url += f'?year={bday.year}&month={bday.month}&day={bday.day}'

    tmp_png = pathlib.Path(tempfile.mkstemp(suffix='.png')[1])
    HTI.screenshot(url=url, save_as=tmp_png.name, size=(1200, 2000))
    return tmp_png


# ───────────────────────────────────────────────────────────────────────────────
# СТАРТОВОЕ СООБЩЕНИЕ И ПЛАШКА «ПЕЧАТАЕТ»
# ───────────────────────────────────────────────────────────────────────────────

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    greeting = ('Привет! Хочу помочь тебе со здоровьем и развитием. Если ответишь '
                'на пару вопросов, я смогу построить твой собственный календарь '
                'жизни, который поможет тебе лучше понять себя и свою жизнь.')
    await update.message.reply_text(greeting)


async def _keep_typing(chat_id: int, bot, stop_event: asyncio.Event):
    try:
        while not stop_event.is_set():
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=4.5)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        pass


# ───────────────────────────────────────────────────────────────────────────────
# ГЕНЕРАЦИЯ КАЛЕНДАРЯ ЖИЗНИ
# ───────────────────────────────────────────────────────────────────────────────

async def handle_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stop_event  = asyncio.Event()
    typing_task = context.application.create_task(
        _keep_typing(update.effective_chat.id, context.bot, stop_event)
    )

    if not context.args:
        await update.message.reply_text(
            'Формат команды: /calendar YYYY-MM-DD\n'
            'Напр.: /calendar 1990-07-15'
        )
        stop_event.set()
        await typing_task
        return

    try:
        bday = dt.date.fromisoformat(context.args[0])
    except ValueError:
        await update.message.reply_text('Некорректная дата. Нужен формат YYYY-MM-DD.')
        stop_event.set()
        await typing_task
        return

    loop = asyncio.get_running_loop()
    png_path = await loop.run_in_executor(None, _render_calendar, bday)

    try:
        with png_path.open('rb') as img:
            await update.message.reply_photo(img)
    finally:
        png_path.unlink(missing_ok=True)
        stop_event.set()
        await typing_task

# ───────────────────────────────────────────────────────────────────────────────
# ИНИЦИАЦИЯ РАБОТЫ БОТА
# ───────────────────────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(LIFE_BOT_TOKEN).build()
    print('✅ Бот успешно запустился и работает, пока ты пьешь чай')

    app.add_handler(CommandHandler('start', handle_start))
    app.add_handler(CommandHandler('calendar', handle_calendar))
    app.run_polling()

if __name__ == '__main__':
    main()
