from __future__ import annotations

import re
from datetime import date

# month names in english and russian to detect textual months
_MONTH_WORDS = [
    'january', 'february', 'march', 'april', 'may', 'june', 'july',
    'august', 'september', 'october', 'november', 'december',
    'январ', 'феврал', 'март', 'апрел', 'май', 'июн', 'июл',
    'август', 'сентябр', 'октябр', 'ноябр', 'декабр'
]

_MONTH_RE = re.compile(r'(?:' + '|'.join(_MONTH_WORDS) + r')', re.IGNORECASE)
_DECIMAL_RE = re.compile(r'\b\d+\.\d+(?!\.)')

__all__ = ['parse_dates']

def _contains_text_month(text: str) -> bool:
    return bool(_MONTH_RE.search(text))

def _contains_decimal_age(text: str) -> bool:
    return bool(_DECIMAL_RE.search(text))

def parse_dates(text: str, birth: date):
    """Parse ages or explicit dates from user input.

    Parameters
    ----------
    text: str
        User provided message.
    birth: date
        Birth date to convert ages into real dates.

    Returns
    -------
    date | tuple[date, date]
        Parsed date or a tuple of two dates.

    Raises
    ------
    ValueError
        If text doesn't contain a valid date specification or contains
        textual months or fractional ages.
    """

    if _contains_text_month(text) or _contains_decimal_age(text):
        raise ValueError('Некорректный формат даты или возраста')

    # first try to parse as ages
    try:
        numbers = list(map(int, re.findall(r'\d+', text)))
        if len(numbers) == 1:
            return date(birth.year + numbers[0] + ((birth.month, birth.day) > (8, 31)), 1, 1)
        elif len(numbers) == 2:
            start, end = sorted(numbers)
            start = date(birth.year + start + ((birth.month, birth.day) > (8, 31)), 1, 7)
            end = date(birth.year + end + ((birth.month, birth.day) > (8, 31)), 12, 31)
            return start, end
        else:
            raise ValueError
    except Exception:
        pass

    # try to parse explicit dates
    dates = []
    for d, m, y in re.findall(r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b', text):
        year = int(y)
        if year < 100:
            year += 2000 if year < 50 else 1900
        try:
            dates.append(date(year, int(m), int(d)))
        except ValueError:
            continue

    if not dates or len(dates) > 2:
        raise ValueError('Не найдено ни одной корректной даты')

    return tuple(dates) if len(dates) == 2 else dates[0]

