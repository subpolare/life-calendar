from handlers.habits import HABIT_FIELDS, QUESTIONS, _habit_value, EFFECTS_TEXTS, _effects_keyboard, _more_keyboard
from utils.dbtools import get_user_data, get_habits_list, set_habit, set_expectation, get_expectation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ChatAction
from utils.typing_task import keep_typing
import logging, asyncio

logger = logging.getLogger(__name__) 

HABITS_WANT, HABITS_DECIDE, HABITS_PICK, HABITS_ASK, HABBITS_EFFECTS, HABITS_EFFECTS_DECIDE = range(6)

E2I = {
    'eff_smoking' : 0,
    'eff_sleep'   : 1,
    'eff_alcohol' : 5,
    'eff_sport'   : 3,
    'eff_sweet'   : 4,
    'eff_meat'    : 2,
    'eff_kbju'    : 6,
    'eff_air'     : 7,
}

def _yesno_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Да', callback_data = 'habits_yes')],
        [InlineKeyboardButton('Нет', callback_data = 'habits_no')],
    ])

def _decide_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Хочу поменять кое-что одно', callback_data = 'habits_one')],
        [InlineKeyboardButton('Хочу заново ответить на вопросы', callback_data = 'habits_retake')],
        [InlineKeyboardButton('Хочу узнать про их влияние', callback_data = 'habits_science')],
        [InlineKeyboardButton('Ничего не меняем', callback_data = 'habits_none')],
    ])

def _pick_keyboard(female = False):
    rows = [
        [InlineKeyboardButton('Курение', callback_data = 'eff_smoking'), InlineKeyboardButton('Сон', callback_data = 'eff_sleep')],
        [InlineKeyboardButton('Алкоголь', callback_data = 'eff_alcohol'), InlineKeyboardButton('Спорт', callback_data = 'eff_sport')],
        [InlineKeyboardButton('Сладкое', callback_data = 'eff_sweet'), InlineKeyboardButton('Мясо', callback_data = 'eff_meat')],
        [InlineKeyboardButton('КБЖУ', callback_data = 'eff_kbju'), InlineKeyboardButton('Воздух', callback_data = 'eff_air')],
        [InlineKeyboardButton('Я передумала', callback_data = 'habits_cancel')],
    ]
    return InlineKeyboardMarkup(rows)

def _genderize(text: str, female: bool) -> str:
    return text.replace('Бросил(а)', 'Бросила' if female else 'Бросил')

def _question(idx: int, female: bool):
    q = QUESTIONS[idx]
    text = q['text'] if isinstance(q, dict) else q[0]
    raw_opts = q['options'] if isinstance(q, dict) else q[1]
    labels = []
    for o in raw_opts:
        s = o[0] if isinstance(o, (list, tuple)) else o
        labels.append(_genderize(s, female))
    return text, labels

def _opts_keyboard(opts: list[str], allow_cancel = False, female = False):
    rows = [[InlineKeyboardButton(o, callback_data = f'habopt_{i}')] for i, o in enumerate(opts)]
    if allow_cancel:
        rows.append([InlineKeyboardButton('Не хочу отвечать', callback_data = 'habopt_cancel')])
    return InlineKeyboardMarkup(rows)

def _format_list(values: list[str], female: bool, expectation: int | None = None):
    tail = 'а' if female else ''
    lines = [f'Вот, про какие привычки ты мне рассказывал{tail}:\n']

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

    for habbit in values:
        lines.append(f'_~ {habbit}_')
    if expectation:
        lines.append('')
        lines.append(f'*Твоя ожидаемая продолжительность жизни: {expectation} {years_word(int(expectation))}.* Хочешь что-то поменять?')
    return '\n'.join(lines)

async def _recalc_expectation(update: Update):
    user_id = update.effective_user.id
    user = await get_user_data(user_id)
    female = user.get('gender') == 'female'
    values = await get_habits_list(user_id)

    delta = 0
    for i, v in enumerate(values):
        q = QUESTIONS[i]
        if isinstance(q, dict):
            raw_opts = list(q.get('options') or q.get('opts') or [])
        else:
            raw_opts = list(q[1])
        _, labels = _question(i, female)
        if v in labels:
            idx = labels.index(v)
            opt = raw_opts[idx]
            w = opt[1] if isinstance(opt, (list, tuple)) and len(opt) > 1 else 0
            delta += w

    base = 81 if female else 71
    new_exp = max(55, base + delta)
    old_exp = await get_expectation(update.effective_user.id)
    await set_expectation(user_id, new_exp)

    name = update.effective_user.username or update.effective_user.full_name or 'unknown'
    if not old_exp:
        diff = new_exp - old_exp
        sign = '+' if diff >= 0 else ''
        logger.info(f'{name}: life expectancy changed {sign}{diff} -> {new_exp}')
    return new_exp 

@keep_typing
async def handle_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_data(update.effective_user.id)
    female = user.get('gender') == 'female'
    values = await get_habits_list(update.effective_user.id)
    if not values:
        await update.message.reply_text('Хочешь ответить на вопросы про привычки? Я посчитаю твою личную длину календаря.', reply_markup = _yesno_keyboard())
        return HABITS_WANT
    
    exp = await get_expectation(update.effective_user.id)
    await update.message.reply_text(
        _format_list(values, female, exp), 
        reply_markup = _decide_keyboard(), 
        parse_mode   = 'Markdown')
    return HABITS_DECIDE

@keep_typing
async def habits_want_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup = None)
    if query.data == 'habits_no':
        return ConversationHandler.END
    user = await get_user_data(update.effective_user.id)
    female = user.get('gender') == 'female'
    context.user_data['hab_mode'] = 'retake'
    context.user_data['hab_idx'] = 0
    text, opts = _question(0, female)
    await query.message.reply_text(text, reply_markup = _opts_keyboard(opts))
    return HABITS_ASK

@keep_typing
async def habits_decide_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)

    if query.data == 'habits_retake':
        user = await get_user_data(update.effective_user.id)
        female = user.get('gender') == 'female'
        context.user_data['hab_mode'] = 'retake'
        context.user_data['hab_idx'] = 0
        text, opts = _question(0, female)
        await query.message.reply_text(text, reply_markup = _opts_keyboard(opts))
        return HABITS_ASK
    
    if query.data == 'habits_one':
        user = await get_user_data(update.effective_user.id)
        female = user.get('gender') == 'female'
        await query.message.reply_text('Что именно ты хочешь поменять?', reply_markup = _pick_keyboard(female = female))
        return HABITS_PICK
    
    if query.data == 'habits_science': 
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Про какую привычку мне рассказать?',
            reply_markup = _effects_keyboard()
        )
        return HABBITS_EFFECTS
    
    if query.data == 'habits_none':
        await _recalc_expectation(update)
        return ConversationHandler.END
    return HABITS_DECIDE

@keep_typing
async def habits_pick_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)

    if query.data == 'habits_cancel':
        user = await get_user_data(update.effective_user.id)
        female = user.get('gender') == 'female'
        values = await get_habits_list(update.effective_user.id)

        exp = await get_expectation(update.effective_user.id)
        await query.message.reply_text(
            _format_list(values, female, exp),
            reply_markup = _decide_keyboard()
        )
        return HABITS_DECIDE
    
    if query.data in E2I:
        context.user_data['hab_mode'] = 'single'
        context.user_data['hab_idx'] = E2I[query.data]
        user = await get_user_data(update.effective_user.id)
        female = user.get('gender') == 'female'
        text, opts = _question(context.user_data['hab_idx'], female)
        await query.message.reply_text(text, reply_markup = _opts_keyboard(opts, allow_cancel = True, female = female))
        return HABITS_ASK
    
    return HABITS_PICK

@keep_typing
async def habits_one_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
    data = query.data

    if data == 'habopt_cancel':
        user = await get_user_data(update.effective_user.id)
        female = user.get('gender') == 'female'
        values = await get_habits_list(update.effective_user.id)
        
        exp = await get_expectation(update.effective_user.id)
        await query.message.reply_text(
            _format_list(values, female, exp), 
            reply_markup = _decide_keyboard()
        )
        return HABITS_DECIDE
    
    if not data.startswith('habopt_'):
        return HABITS_ASK
    
    choice = int(data.split('_', 1)[1])
    user = await get_user_data(update.effective_user.id)
    female = user.get('gender') == 'female'
    idx = context.user_data.get('hab_idx', 0)
    text, opts = _question(idx, female)

    if 0 <= choice < len(opts):
        value = _habit_value(idx, choice, female)
        await set_habit(update.effective_user.id, HABIT_FIELDS[idx], value)

    if context.user_data.get('hab_mode') == 'retake':
        idx += 1
        if idx < len(HABIT_FIELDS):
            context.user_data['hab_idx'] = idx
            text, opts = _question(idx, female)
            await query.message.reply_text(text, reply_markup = _opts_keyboard(opts))
            return HABITS_ASK

    new_exp = await _recalc_expectation(update)
    values = await get_habits_list(update.effective_user.id)

    await query.message.reply_text(
        _format_list(values, female, new_exp),
        reply_markup = _decide_keyboard(),
        parse_mode = 'Markdown'
    )
    return HABITS_DECIDE

@keep_typing
async def habits_effects_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
    await asyncio.sleep(5)
    text = EFFECTS_TEXTS.get(query.data, '')
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
    return HABITS_EFFECTS_DECIDE 

# Почему-то не работает... 

@keep_typing
async def habits_decide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    answer = query.data

    if answer == 'more_yes':
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Про какую привычку мне рассказать?',
            reply_markup = _effects_keyboard()
        )
        return HABBITS_EFFECTS
    
    if answer == 'more_no': 
        await context.bot.delete_message(chat_id = query.message.chat.id, message_id = query.message.message_id)
        await asyncio.sleep(3)
        await context.bot.send_message(
            chat_id     = update.effective_chat.id,
            text        = 'Буду ждать, пока ты вернешься! Нажми /habits, если захочешь почитать про другие привычки' , 
            parse_mode  = 'Markdown'
        )
        return ConversationHandler.END 