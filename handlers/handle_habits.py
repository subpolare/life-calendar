
# Не пересчитан expectancy !!! Надо поправить 

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from utils.dbtools import get_user_data, get_habits_list, set_habit
from telegram.ext import ContextTypes, ConversationHandler
from handlers.habits import HABIT_FIELDS, QUESTIONS
from utils.typing_task import keep_typing

HABITS_WANT, HABITS_DECIDE, HABITS_PICK, HABITS_ASK = range(4)

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
        [InlineKeyboardButton('Ничего не меняем', callback_data = 'habits_none')],
    ])

def _pick_keyboard(female = False):
    rows = [
        [InlineKeyboardButton('Курение', callback_data = 'eff_smoking'), InlineKeyboardButton('Сон', callback_data = 'eff_sleep')],
        [InlineKeyboardButton('Алкоголь', callback_data = 'eff_alcohol'), InlineKeyboardButton('Спорт', callback_data = 'eff_sport')],
        [InlineKeyboardButton('Сладкое', callback_data = 'eff_sweet'), InlineKeyboardButton('Мясо', callback_data = 'eff_meat')],
        [InlineKeyboardButton('КБЖУ', callback_data = 'eff_kbju'), InlineKeyboardButton('Воздух', callback_data = 'eff_air')],
        [InlineKeyboardButton('Я передумала' if female else 'Я передумал', callback_data = 'habits_cancel')],
    ]
    return InlineKeyboardMarkup(rows)

def _genderize(text: str, female: bool) -> str:
    return text.replace('Бросил(а)', 'Бросила' if female else 'Бросил')

def _question(idx: int, female: bool):
    q = QUESTIONS[idx]
    if isinstance(q, dict):
        text = str(q.get('text') or q.get('q') or '')
        opts = list(q.get('options') or q.get('opts') or [])
    else:
        text = str(q[0])
        opts = list(q[1])
    text = _genderize(text, female)
    opts = [_genderize(o, female) for o in opts]
    return text, opts

def _opts_keyboard(opts: list[str], allow_cancel = False, female = False):
    rows = [[InlineKeyboardButton(o, callback_data = f'habopt_{i}')] for i, o in enumerate(opts)]
    if allow_cancel:
        rows.append([InlineKeyboardButton('Я передумала' if female else 'Я передумал', callback_data = 'habopt_cancel')])
    return InlineKeyboardMarkup(rows)

def _format_list(values: list[str], female: bool):
    tail = 'а' if female else ''
    lines = [f'Вот, про какие привычки ты мне рассказывал{tail}:\n']
    for i, v in enumerate(values, 1):
        lines.append(f'_~ {v}_')
    lines.append('')
    lines.append('Хочешь что-то поменять?')
    return '\n'.join(lines)

@keep_typing
async def handle_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_data(update.effective_user.id)
    female = user.get('gender') == 'female'
    values = await get_habits_list(update.effective_user.id)
    if not values:
        await update.message.reply_text('Хочешь ответить на вопросы про привычки? Я посчитаю твою личную длину календаря.', reply_markup = _yesno_keyboard())
        return HABITS_WANT
    await update.message.reply_text(_format_list(values, female), reply_markup = _decide_keyboard(), parse_mode = 'Markdown')
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
    await query.edit_message_reply_markup(reply_markup = None)
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
    if query.data == 'habits_none':
        return ConversationHandler.END
    return HABITS_DECIDE

@keep_typing
async def habits_pick_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup = None)
    if query.data == 'habits_cancel':
        user = await get_user_data(update.effective_user.id)
        female = user.get('gender') == 'female'
        values = await get_habits_list(update.effective_user.id)
        await query.message.reply_text(_format_list(values, female), reply_markup = _decide_keyboard())
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
    await query.edit_message_reply_markup(reply_markup = None)
    data = query.data
    if data == 'habopt_cancel':
        user = await get_user_data(update.effective_user.id)
        female = user.get('gender') == 'female'
        values = await get_habits_list(update.effective_user.id)
        await query.message.reply_text(_format_list(values, female), reply_markup = _decide_keyboard())
        return HABITS_DECIDE
    if not data.startswith('habopt_'):
        return HABITS_ASK
    choice = int(data.split('_', 1)[1])
    user = await get_user_data(update.effective_user.id)
    female = user.get('gender') == 'female'
    idx = context.user_data.get('hab_idx', 0)
    text, opts = _question(idx, female)
    if 0 <= choice < len(opts):
        await set_habit(update.effective_user.id, HABIT_FIELDS[idx], opts[choice])
    if context.user_data.get('hab_mode') == 'retake':
        idx += 1
        if idx < len(HABIT_FIELDS):
            context.user_data['hab_idx'] = idx
            text, opts = _question(idx, female)
            await query.message.reply_text(text, reply_markup = _opts_keyboard(opts))
            return HABITS_ASK
    values = await get_habits_list(update.effective_user.id)
    await query.message.reply_text(_format_list(values, female), reply_markup = _decide_keyboard())
    return HABITS_DECIDE