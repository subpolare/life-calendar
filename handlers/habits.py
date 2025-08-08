from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from utils.dbtools import set_expectation, get_user_data
from lifecalendar.bridge import create_calendar
from utils.typing_task import keep_typing
from telegram.ext import ContextTypes
from datetime import date
import secrets, os, logging

logger = logging.getLogger(__name__)

QUESTIONS = [
    {
        'text': 'Ты куришь? Если бросил, жми «Нет».',
        'options': [('Да', -10), ('Нет', 0)],
    },
    {
        'text': 'Сколько ты спишь?',
        'options': [
            ('Меньше 6 часов', -5),
            ('6–9 часов', 0),
            ('10 часов и больше', -5),
        ],
    },
    {
        'text': 'Ешь колбасы, сосиски, бекон и другие переработанные мясные продукты?',
        'options': [('Да', -5), ('Нет', 0)],
    },
    {
        'text': 'Занимаешься спортом?',
        'options': [('Нет', -3), ('Редко', 0), ('2 раза в неделю и чаще', 6)],
    },
    {
        'text': 'Ешь сахар? Сюда относится газировка и сладости чаще раза в месяц.',
        'options': [('Да', 0), ('Нет', 5)],
    },
    {
        'text': 'Пьешь алкоголь? Считается даже раз в месяц или по праздникам.',
        'options': [('Да', -2), ('Нет', 7)],
    },
    {
        'text': 'Следишь за тем, чтобы в еде было больше белка, чем жира, много клетчатки, орехов и мало сахара?',
        'options': [('Да', 5), ('Нет', 0)],
    },
    {
        'text': 'Какого цвета на [этой карте качества воздуха](https://www.iqair.com/ru/air-quality-map) город, в котором ты живешь больше всего?',
        'options': [
            ('Синий или зеленый', 2),
            ('Желтый', 0),
            ('Красный или фиолетовый', -3),
        ],
    },
]

@keep_typing
async def ask_habits_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.handle_start import HABIT_INTRO
    logger.info('Prompting user %s for habits intro', update.effective_user.username)
    keyboard = [[
        InlineKeyboardButton('Да', callback_data  = 'yes'),
        InlineKeyboardButton('Нет', callback_data = 'no')
    ]]
    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = 'Хочешь пройти небольшой опрос из 8 вопросов? Он поможет узнать, сколько клеточек именно в твоем календаре, а не в среднем по России',
        reply_markup = InlineKeyboardMarkup(keyboard),
        parse_mode   = 'Markdown'
    )
    return HABIT_INTRO

@keep_typing
async def habits_intro_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    answer = query.data
    logger.info('User %s answered habits intro', update.effective_user.username)
    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
    
    if answer == 'yes':
        context.user_data['habit_idx'] = 0
        context.user_data['delta']     = 0
        return await _ask_next_question(update, context)
    else:
        from handlers.handle_start import finish_start
        return await finish_start(update, context)

async def _ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.handle_start import HABIT_Q
    idx = context.user_data.get('habit_idx', 0)
    logger.info('Asking habit question for user %s', update.effective_user.username)
    if idx >= len(QUESTIONS):
        return await _finish_questions(update, context)
    q = QUESTIONS[idx]
    keyboard = [[InlineKeyboardButton(opt[0], callback_data=str(i)) for i, opt in enumerate(q['options'])]]
    if len(q['options']) > 2:
        keyboard = [
            [InlineKeyboardButton(q['options'][0][0], callback_data='0')],
            [InlineKeyboardButton(q['options'][1][0], callback_data='1')],
            [InlineKeyboardButton(q['options'][2][0], callback_data='2')],
        ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=q['text'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return HABIT_Q

@keep_typing
async def habits_question_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = context.user_data.get('habit_idx', 0)
    q = QUESTIONS[idx]
    choice = int(query.data)
    logger.info('User %s answered habit question', update.effective_user.username)
    context.user_data['delta'] = context.user_data.get('delta', 0) + q['options'][choice][1]
    context.user_data['habit_idx'] = idx + 1
    await context.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    if context.user_data['habit_idx'] < len(QUESTIONS):
        return await _ask_next_question(update, context)
    else:
        return await _finish_questions(update, context)

async def _finish_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delta = context.user_data.get('delta', 0)
    user = await get_user_data(update.effective_user.id)
    gender = user.get('gender', 'male')
    base = 81 if gender == 'female' else 71
    expectation = max(55, base + delta)
    logger.info('User %s finished habits questionnaire', update.effective_user.username)
    await set_expectation(update.effective_user.id, expectation)
    day, month, year = map(int, user['birth'].split('.'))
    birth = date(year, month, day)
    filename = f'tmp/{secrets.token_hex(8)}.png'
    create_calendar(birth, fname=filename, female=(gender=='female'), expectation=expectation)
    with open(filename, 'rb') as photo:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=photo,
            caption='Вот твой календарь с учетом твоего стиля жизни',
            parse_mode='Markdown'
        )
    os.remove(filename)
    sign = '+' if expectation - base >= 0 else ''
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Твоя ожидаемая продолжительность жизни изменилась на {sign}{expectation - base} лет.',
        parse_mode='Markdown'
    )
    from handlers.handle_start import finish_start
    return await finish_start(update, context)

