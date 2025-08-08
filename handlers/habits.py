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
        'text': 'Ты куришь? Считаются не только обычные сигареты, но и любые другие',
        'options': [
            ('Курю обычные сигареты', -10), 
            ('Только электронки', -3), 
            ('Уже бросил', -2), 
            ('Не курю', 0)
        ],
    },
    {
        'text': 'Сколько в день ты спишь? Понимаю, что иногда хочется поспать подольше, а иногда надо работать до утра, но сколько часов сна выходит чаще всего?',
        'options': [
            ('Меньше 6 часов', -5),
            ('От 6 до 9 часов', 0),
            ('10 часов и больше', -5),
        ],
    },
    {
        'text': 'Как ты относишься к колбасе, сосискам, бекону и всему такому? Ешь их или стараешься избегать?',
        'options': [('Да, ем', -5), ('Избегаю', 0)],
    },
    {
        'text': 'Как часто ты занимаешься спортом?',
        'options': [
            ('Не чаще раза в месяц', -3), 
            ('Пару раз в месяц', 0), 
            ('2 раза в неделю и больше', 6)
        ],
    },
    {
        'text': 'Как ты относишься к сладкому и газировкам? Часто ешь и пьешь их?',
        'options': [
            ('Не слежу за этим', -2), 
            ('Стараюсь не очень часто', 0), 
            ('Не чаще раза в месяц', 5)
        ],
    },
    {
        'text': 'Ты пьешь алкоголь?',
        'options': [
            ('Да', -2), 
            ('Только по праздникам', 0), 
            ('Вообще не пью', 7)
        ],
    },
    {
        'text': 'Следишь за тем, чтобы в еде белка было больше, чем жира? Считать КБЖУ необязательно, достаточно избегать жирного и часто есть то, в чем много белка',
        'options': [('Да', 5), ('Нет', 0)],
    },
    {
        'text': 'Какого цвета город, в котором ты живешь, на [этой карте качества воздуха](https://www.iqair.com/ru/air-quality-map)?',
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
    keyboard = [
        [InlineKeyboardButton('Конечно', callback_data  = 'yes')],
        [InlineKeyboardButton('Давай потом?', callback_data = 'no')]
    ]

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
    keyboard = [[InlineKeyboardButton(opt[0], callback_data = str(i)) for i, opt in enumerate(q['options'])]]

    if len(q['options']) > 2:
        keyboard = []
        for i in range(len(q['options'])): 
            keyboard.append([InlineKeyboardButton(q['options'][i][0], callback_data = f'{i}')])

    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = q['text'],
        reply_markup = InlineKeyboardMarkup(keyboard),
        parse_mode   = 'Markdown'
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

    await context.bot.delete_message(
        chat_id    = query.message.chat.id, 
        message_id = query.message.message_id
    )

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
    filename = f'tmp/{secrets.token_hex(8)}.png'
    create_calendar(date(year, month, day), fname = filename, expectation = expectation)

    with open(filename, 'rb') as photo:
        await context.bot.send_document(
            chat_id    = update.effective_chat.id,
            document   = photo,
            caption    = 'Вот твой календарь с учетом твоего стиля жизни',
            parse_mode = 'Markdown'
        )
    os.remove(filename)

    sign = '+' if expectation - base >= 0 else ''
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = f'Твоя ожидаемая продолжительность жизни изменилась на {sign}{expectation - base} лет.',
        parse_mode = f'Markdown'
    )

    from handlers.handle_start import finish_start
    return await finish_start(update, context)