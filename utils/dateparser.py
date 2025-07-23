from __future__ import annotations

import re
from datetime import date

_MONTH_ALIASES = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,

    'янв': 1, 'январь': 1, 'января': 1,
    'фев': 2, 'февраль': 2, 'февраля': 2,
    'мар': 3, 'март': 3, 'марта': 3,
    'апр': 4, 'апрель': 4, 'апреля': 4,
    'май': 5, 'мая': 5,
    'июн': 6, 'июнь': 6, 'июня': 6,
    'июл': 7, 'июль': 7, 'июля': 7,
    'авг': 8, 'август': 8, 'августа': 8,
    'сен': 9, 'сент': 9, 'сентябрь': 9, 'сентября': 9,
    'окт': 10, 'октябрь': 10, 'октября': 10,
    'ноя': 11, 'ноябрь': 11, 'ноября': 11,
    'дек': 12, 'декабрь': 12, 'декабря': 12,
}

_MONTH_WORDS = list(_MONTH_ALIASES.keys())

_MONTH_RE = re.compile('|'.join(re.escape(m) for m in _MONTH_WORDS), re.IGNORECASE)
_DECIMAL_RE = re.compile(r'\b\d+\.\d+(?!\.)')
_MONTH_TEXT_DATE_RE = re.compile(
    r'(?:\b(\d{1,2})\s+)?(' + '|'.join(re.escape(m) for m in sorted(_MONTH_WORDS, key = len, reverse = True)) + r')\s+(\d{2,4})',
    re.IGNORECASE
)
__all__ = ['parse_dates']

def _contains_decimal_age(text: str) -> bool:
    return bool(_DECIMAL_RE.search(text))

def _parse_month_text(text: str):
    dates = []
    for day, month_word, year in _MONTH_TEXT_DATE_RE.findall(text):
        key = month_word.lower().replace('ё', 'е')
        key = key[:3] if key[:3] in _MONTH_ALIASES else key
        month = _MONTH_ALIASES.get(key)
        if not month:
            continue
        year = int(year)
        if year < 100:
            year += 2000 if year < 50 else 1900
        d = int(day) if day else 1
        try:
            dates.append(date(year, month, d))
        except ValueError:
            continue
    return dates
  
def parse_dates(text: str, birth: date):
    if _contains_decimal_age(text):
        raise ValueError('Некорректный формат даты или возраста')
    dates = []
    for d, m, y in re.findall(r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b', text):
        year = int(y)
        if year < 100:
            year += 2000 if year < 50 else 1900
        try:
            dates.append(date(year, int(m), int(d)))
        except ValueError:
            continue
    if not dates:
        dates = _parse_month_text(text)

    if not dates:
        try:
            numbers = list(map(int, re.findall(r'\d+', text)))
            if len(numbers) == 1:
                return date(
                    birth.year + numbers[0] + ((birth.month, birth.day) > (8, 31)),
                    1,
                    1,
                )
            elif len(numbers) == 2:
                start, end = sorted(numbers)
                start = date(
                    birth.year + start + ((birth.month, birth.day) > (8, 31)),
                    1,
                    7,
                )
                end = date(
                    birth.year + end + ((birth.month, birth.day) > (8, 31)),
                    12,
                    31,
                )
                return start, end
        except Exception:
            pass

    if not dates or len(dates) > 2:
        raise ValueError('Не найдено ни одной корректной даты')

    return tuple(dates) if len(dates) == 2 else dates[0]

    
