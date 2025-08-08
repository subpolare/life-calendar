from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from utils.dbtools import set_expectation, get_user_data, set_habbit
from lifecalendar.bridge import create_calendar
from utils.typing_task import keep_typing
from telegram.ext import ContextTypes
import secrets, os, logging, asyncio
from datetime import date

logger = logging.getLogger(__name__)

HABIT_FIELDS = ['smoking', 'sleep', 'meat', 'sport', 'sugar', 'alcohol', 'food', 'air']
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
        'options': [('Слежу', 5), ('Не слежу', 0)],
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

EFFECTS_TEXTS = {
    'eff_smoking' : 'Курение — прямой удар по сосудам и лёгким. Чем меньше затяжек, тем лучше выносливость и восстановление. Бросаешь — через недели легче дышать, через месяцы падают риски.',
    'eff_sleep'   : 'Сон — буфер для мозга и гормонов. 7–9 часов стабильно: меньше тяги к сладкому, лучше память, крепче иммунитет. Засыпай и просыпайся в одно и то же время.',
    'eff_alcohol' : 'Алкоголь — седативный яд. Ломает сон, тормозит восстановление, повышает риск рака даже при «умеренности». Чем реже, тем лучше.',
    'eff_sport'   : 'Движение — таблетка. 150 минут в неделю + 2 силовых — ниже давление, выше инсулин-чувствительность и настроение. Организм скажет спасибо.',
    'eff_sweet'   : 'Сладкое даёт короткий подъём и длинную тягу. Пики глюкозы = усталость и голод. Замени печенье и соки на фрукты и орехи, держи белок в каждом приёме.',
    'eff_meat'    : 'Мясо — белок, железо, B12. Норма — ок, переработанное и жареное — лишние риски. Добавляй овощи и бобовые, чередуй рыбу и птицу.',
    'eff_kbju'    : 'КБЖУ — рычаги. Дефицит калорий — минус вес, профицит — рост. Белок 1.2–1.6 г/кг держит сытость, жиры нужны гормонам, углеводы — энергии и спорту.',
    'eff_air'     : 'Воздух тоже еда. PM2.5 и дым бьют по сердцу и мозгу. Проветривай, поставь фильтр, обходи магистрали. Парки — бесплатный апгрейд.',
}

def _habit_value(idx: int, choice: int, female: bool) -> str:
    if idx == 0:
        v = ['Куришь обычные сигареты', 'Куришь только электронки', 'Бросила' if female else 'Бросил', 'Не куришь']
        return v[choice]
    if idx == 1:
        v = ['Обычно спишь меньше 6 часов', 'Обычно спишь от 6 до 9 часов', 'Обычно спишь больше 9 часов']
        return v[choice]
    if idx == 2:
        v = ['Ешь колбасы, бекон и другое переработанное мясо', 'Не ешь колбасы, бекон и другое переработанное мясо']
        return v[choice]
    if idx == 3:
        v = ['Занимаешься спортом не чаще раза в месяц', 'Занимаешься спортом пару раз в месяц', 'Занимаешься спортом минимум 2 раза в неделю']
        return v[choice]
    if idx == 4:
        v = ['Часто ешь сладкое', 'Стараешься не есть сладкое', 'Не ешь сладкое']
        return v[choice]
    if idx == 5:
        v = ['Пьешь', 'Редко пьешь', 'Не пьешь']
        return v[choice]
    if idx == 6:
        v = ['Следишь за тем, чтобы белковой еды было больше, чем жирной, и в целом контролируешь свой рацион', 'Не следишь за рационом']
        return v[choice]
    if idx == 7:
        v = ['В твоем городе чистый воздух', 'Воздух в твоем городе слегка загрязнен', 'Воздух в твоем городе сильно загрязнен']
        return v[choice]
    return ''

@keep_typing
async def ask_habits_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.handle_start import HABIT_INTRO
    logger.info('Prompting user %s for habits intro', update.effective_user.username)
    keyboard = [
        [InlineKeyboardButton('Давай!', callback_data  = 'yes')],
        [InlineKeyboardButton('Не хочу', callback_data = 'no')]
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

    user = await get_user_data(update.effective_user.id)
    female = user.get('gender') == 'female'
    field = HABIT_FIELDS[idx]
    value = _habit_value(idx, choice, female)
    if value:
        await set_habbit(update.effective_user.id, field, value)

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
            caption    = 'Вот твой новый календарь с учетом твоего стиля жизни',
            parse_mode = 'Markdown'
        )
    os.remove(filename)

    def years_word(n: int) -> str:
        n = abs(n) % 100
        if 11 <= n <= 19:
            return 'лет'
        last_digit = n % 10
        if last_digit == 1:
            return 'год'
        if 2 <= last_digit <= 4:
            return 'года'
        return 'лет'
    
    await asyncio.sleep(8)
    years = expectation - base + 1
    sign = '+' if expectation - base >= 0 else ''
    await context.bot.send_message(
        chat_id    = update.effective_chat.id,
        text       = f'Твоя ожидаемая продолжительность жизни изменилась на {sign}{years} {years_word(years)}\n\nЭто не значит, что ты проживешь меньше или больше, но чаще всего твои привычки влияют на жизнь именно так',
        parse_mode = f'Markdown'
    )

    await asyncio.sleep(5)
    await ask_habit_effects(update, context)
    from handlers.handle_start import HABIT_EFFECTS
    return HABIT_EFFECTS

def _effects_keyboard(extra_cancel = False, female = False):
    rows = [
        [InlineKeyboardButton('Курение', callback_data = 'eff_smoking'), InlineKeyboardButton('Сон', callback_data = 'eff_sleep')],
        [InlineKeyboardButton('Алкоголь', callback_data = 'eff_alcohol'), InlineKeyboardButton('Спорт', callback_data = 'eff_sport')],
        [InlineKeyboardButton('Сладкое', callback_data = 'eff_sweet'), InlineKeyboardButton('Мясо', callback_data = 'eff_meat')],
        [InlineKeyboardButton('КБЖУ', callback_data = 'eff_kbju'), InlineKeyboardButton('Воздух', callback_data = 'eff_air')],
    ]
    if extra_cancel:
        rows.append([InlineKeyboardButton('Я передумала' if female else 'Я передумал', callback_data = 'cancel_effects')])
    return InlineKeyboardMarkup(rows)

def _more_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Конечно!', callback_data = 'more_yes')], [InlineKeyboardButton('Давай потом?', callback_data = 'more_no')]
    ])

@keep_typing
async def ask_habit_effects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = 'Хочешь узнать, как эти привычки влияют на тебя? Если да, выбери, про какую рассказать',
        reply_markup = _effects_keyboard()
    )

@keep_typing
async def habits_effects_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup = None)
    data = query.data

    if data.startswith('eff_'):
        await asyncio.sleep(5)
        text = EFFECTS_TEXTS.get(data, '')
        if text:
            await context.bot.send_message(chat_id = query.message.chat.id, text = text)
        await context.bot.send_message(chat_id = query.message.chat.id, text = 'Хочешь узнать про другие привычки?', reply_markup = _more_keyboard())
        from handlers.handle_start import HABIT_EFFECTS
        return HABIT_EFFECTS

    if data == 'more_yes':
        user = await get_user_data(update.effective_user.id)
        female = user.get('gender') == 'female'
        await context.bot.send_message(chat_id = query.message.chat.id, text = 'Тогда выбирай следующую тему — расскажу все, что знаю', reply_markup = _effects_keyboard(extra_cancel = True, female = female))
        from handlers.handle_start import HABIT_EFFECTS
        return HABIT_EFFECTS

    if data == 'more_no' or data == 'cancel_effects':
        from handlers.handle_start import finish_start
        return await finish_start(update, context)
