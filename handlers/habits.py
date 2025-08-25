from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from utils.dbtools import set_expectation, get_user_data, set_habbit
from lifecalendar.bridge import create_calendar
from utils.typing_task import keep_typing
from telegram.constants import ChatAction
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
    'eff_smoking' : 'В сигаретах есть никотин, смолы, угарный газ и формальдегид — они попадают в кровь и разрушают легкие, сердце и сосуды.\n\nОт никотина твое сердце бьется быстрее, сосуды сужаются, а угарный газ блокирует кислород в крови. Из-за этого органы хуже снабжаются кровью, и твоя продуктивность падает, а органы быстрее стареют.\n\nСами легкие покрываются черными смолами изнутри. Клетки пытаются залечить это, делятся и умирают. Все это приводит к мутациям в их ДНК. Из-за этого растет вероятность рака легких.\n\n*Все это приводит к тому, что жизнь сокращается в среднем на 10–15 лет.* Кому-то везет, и ты наверняка знаешь стариков с сигаретой, но большая часть не доживает даже до 70 лет. К сожалению, это ошибка выжившего.\n\nДержи [научную статью об этом](https://www.nature.com/articles/nrc1423?error=cookies_not_supported&code=f4d77f1e-01c4-4145-ac3c-d46d7273c96a#:~:text=Smokers%20die%20an%20average%2010,cigarette%20smoking%20in%20this%20cohort). Она из престижного научного журнала nature reviews cancer, так что ей можно доверять.',
    'eff_sleep'   : 'Недостаток и избыток сна нарушают работу всех систем организма. Когда ты спишь меньше 6 часов или больше 9, твой мозг не успевает очищаться от токсинов — накапливаются бета-амилоиды, которые вызывают деменцию.\n\nТвой иммунитет падает почти в два раза — лимфоциты работают хуже, и ты чаще болеешь. Гормон стресса кортизол повышается и разрушает сосуды. Инсулин перестает нормально работать, растет риск диабета.\n\nПри недосыпе клетки сердца изнашиваются быстрее из-за постоянного высокого давления. При пересыпе замедляется обмен веществ, органы получают меньше кислорода.\n\nМозг начинает хуже контролировать аппетит — вырабатывается больше грелина (гормона голода) и меньше лептина (гормона насыщения). Ты набираешь вес, что дает нагрузку на сердце.\n\nВсе это сокращает жизнь в среднем на 5 лет. Оптимальный сон — 7-8 часов, когда организм успевает восстановиться, но не замедляется.\n\nВот [научная статья](https://www.nature.com/articles/srep21480#:~:text=sleep%20duration%20were%20independent%20predictors,cause%20mortality%2C) из престижного научного журнала scientific reports, ей можно доверять. ',
    'eff_alcohol' : 'На языке химии алкоголь — это этанол. Молекула, которую твоя печень превращает в ацетальдегид, токсичное вещество, повреждающее клетки. Даже малые дозы запускают воспаление во всем организме — повышается уровень цитокинов, которые разрушают ткани.\n\nТвоя печень работает на износ, пытаясь нейтрализовать яд. Ее клетки погибают и замещаются рубцовой тканью — так развивается цирроз. Мозг тоже страдает: этанол разрушает нейроны и нарушает связи между ними, ухудшая память и координацию.\n\nАлкоголь повышает давление, заставляя сердце биться сильнее. Он нарушает сердечный ритм и повреждает сердечную мышцу. В желудке этанол разъедает слизистую, вызывая язвы и повышая риск рака. А еще Даже умеренное потребление подавляет иммунитет — макрофаги и Т-лимфоциты работают хуже.\n\nПолный отказ от алкоголя дает бонусные 7 лет жизни. Печень начинает восстанавливаться уже через несколько недель, а риск рака и болезней сердца падает год за годом.\n\nПро это написано много научных статей, но конкретные числа я брала из [авторитетной научной статьи](https://www.nature.com/articles/s41598-021-00728-2?error=cookies_not_supported&code=4d5d9dfc-fe61-4208-b6b0-e720ef53be25#:~:text=The%20ability%20of%20regular%20physical,close%20to%20their%20actual%20elimination) из крупного журнала scientific reports. ',
    'eff_sport'   : 'Без движения твои мышцы теряют до 5% массы каждые 10 дней — белки разрушаются быстрее, чем восстанавливаются. Сердце становится слабее, прокачивает меньше крови, органы получают меньше кислорода и питательных веществ.\n\nКости без нагрузки теряют кальций и становятся хрупкими — остеобласты работают хуже остеокластов. Метаболизм замедляется, инсулин хуже усваивает глюкозу, растет риск диабета.\n\nСосуды теряют эластичность, повышается давление. Лимфатическая система плохо очищает организм от токсинов без мышечных сокращений. Мозг получает меньше нейротрофического фактора BDNF — ухудшается память и настроение.\n\nРегулярный спорт запускает обратные процессы: укрепляются митохондрии в клетках, растет капиллярная сеть, усиливается иммунитет. Выделяются эндорфины и серотонин — естественные антидепрессанты.\n\nОтсутствие спорта забирает 3 года жизни, а регулярные тренировки добавляют 6 лет. Даже 30 минут ходьбы в день кардинально меняют биохимию организма.\n\n[Вот, что об этом пишут](https://www.nature.com/articles/s41598-021-00728-2?error=cookies_not_supported&code=4d5d9dfc-fe61-4208-b6b0-e720ef53be25#:~:text=The%20ability%20of%20regular%20physical,close%20to%20their%20actual%20elimination) в крупном научном журнале scientific reports.',
    'eff_sweet'   : 'Сахар — это глюкоза и фруктоза, которые резко поднимают уровень инсулина в крови. При постоянных скачках клетки перестают реагировать на инсулин — развивается резистентность, ведущая к диабету. Фруктоза перерабатывается только печенью и превращается в жир — развивается жировая болезнь печени.\n\nИзбыток глюкозы запускает гликацию — сахар "склеивается" с белками, образуя конечные продукты гликации. Они накапливаются в сосудах и органах, разрушая коллаген. Сосуды становятся жесткими, развивается атеросклероз. Хроническое воспаление от избытка сахара повышает уровень С-реактивного белка, который повреждает артерии.\n\nОтказ от сахара дает 5 лет жизни. Инсулиновая чувствительность восстанавливается через несколько недель, воспаление спадает, печень очищается от жира. Сосуды становятся эластичнее, а риск диабета и болезней сердца падает.\n\n[Вот статья об этом](https://www.nature.com/articles/s43016-023-00868-w.pdf#:~:text=non,nuts%20and%20fruits%20and%20less) из одного из лучших научных журналов о еде nature food.',
    'eff_meat'    : 'Колбасы и сосиски содержат нитриты и нитраты — они превращаются в нитрозамины, которые повреждают ДНК и вызывают рак кишечника. Соль в огромных количествах повышает давление и нагружает почки. Насыщенные жиры забивают артерии холестериновыми бляшками.\n\nПри копчении и жарке образуются канцерогены — бензопирен и гетероциклические амины. Они накапливаются в организме и запускают мутации в клетках. Консерванты нарушают микрофлору кишечника, ослабляя иммунитет.\n\nПереработанное мясо относится к первой группе канцерогенов — как табак и асбест. Отказ от колбас и сосисок дает 5 лет жизни и здоровый кишечник.\n\nОб этом написано много научных статей, но приведу две: [одну из крутого научного журнала о еде nature food](https://www.nature.com/articles/s43016-021-00343-4) и [вторую из крупного журнала о гормонах](nature reviews endocrinology). Если хочешь что-то попроще, [вот понятная статья в The Conversation](https://theconversation.com/individual-dietary-choices-can-add-or-take-away-minutes-hours-and-years-of-life-166022). ',
    'eff_kbju'    : 'Белок строит и восстанавливает все ткани организма — мышцы, кости, иммунные клетки. Аминокислоты из белка нужны для синтеза ферментов и гормонов. Мало жира означает меньше холестерина в артериях и легче работу сердца.\n\nОрехи содержат омега-3 жирные кислоты, которые снижают воспаление и укрепляют сосуды. Магний и витамин Е в орехах защищают клетки от окисления. Клетчатка питает полезные бактерии в кишечнике. Так что если нет аллергии, это отличный лайфхак по продлению жизни.\n\nПравильная диета с высоким белком, низким жиром и горстью орехов в день добавляет 5 лет жизни. Сосуды остаются чистыми, мышцы крепкими, а воспаление минимальным.\n\nМожешь почитать про это в [крупном научном журнале nature food](https://www.nature.com/articles/s43016-023-00868-w?error=cookies_not_supported&code=a42a67d3-f332-479f-b7ad-9a6ce7306a8f#:~:text=Estimated%20gains%20from%20simulated%20sustained,Correspondingly%2C%20estimated%20gains%20from%20sustained). ',
    'eff_air'     : 'Загрязненный воздух содержит PM2.5 — мелкие частицы, которые проникают прямо в кровь через легкие. Они вызывают воспаление сосудов, повышают давление и риск инфарктов. Диоксид азота и озон разрушают легочную ткань и ослабляют иммунитет.\n\nЧистый воздух дает органам больше кислорода, снижает нагрузку на сердце и легкие. Меньше воспаления — здоровее сосуды и крепче иммунитет. Переезд в экологически чистое место добавляет 2 года жизни. Можешь почитать про это в [крупном научном журнале scientific reports](https://www.nature.com/articles/s41598-024-60786-0?error=cookies_not_supported&code=36cb07d9-a525-4104-8f61-0a4fae0432e0#:~:text=contributes%20to%20an%20extensive%20range,one%20year%20and%20eight%20months5).',
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
    keyboard = [[
        InlineKeyboardButton('Давай!', callback_data  = 'yes'),
        InlineKeyboardButton('Не хочу', callback_data = 'no')
    ]]

    await context.bot.send_message(
        chat_id      = update.effective_chat.id,
        text         = '*Хочешь пройти небольшой опрос из 8 вопросов?* Он поможет узнать, сколько клеточек именно в твоем календаре, а не в среднем по России',
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
    await context.bot.send_chat_action(
        chat_id = update.effective_chat.id, 
        action  = ChatAction.TYPING
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
        [InlineKeyboardButton('Конечно!', callback_data = 'more_yes'), InlineKeyboardButton('Давай потом?', callback_data = 'more_no')]
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
            await context.bot.send_message(
                chat_id = query.message.chat.id, 
                text    = text, 
                parse_mode   = 'Markdown'
            )
            await context.bot.send_chat_action(
                chat_id = update.effective_chat.id, 
                action  = ChatAction.TYPING
            )
            await asyncio.sleep(3)
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
