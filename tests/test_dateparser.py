import pytest
from datetime import date
from utils.dateparser import parse_dates

BIRTH = date(2000, 1, 1)

def test_parse_dd_mm_yyyy():
    assert parse_dates('13.08.1992', BIRTH) == date(1992, 8, 13)

def test_parse_dd_mm_yy():
    assert parse_dates('13.08.92', BIRTH) == date(1992, 8, 13)

def test_parse_month_text():
    assert parse_dates('13 August 1992', BIRTH) == date(1992, 8, 13)

def test_parse_month_only():
    assert parse_dates('August 1992', BIRTH) == date(1992, 8, 1)

def test_parse_russian_month():
    assert parse_dates('13 января 1992', BIRTH) == date(1992, 1, 13)

def test_parse_year_only():
    assert parse_dates('2010', BIRTH) == date(2010, 1, 1)

def test_parse_year_range():
    start, end = parse_dates('2010 2012', BIRTH)
    assert start == date(2010, 1, 1)
    assert end == date(2012, 12, 31)

def test_parse_age():
    assert parse_dates('18', BIRTH) == date(2018, 1, 1)

def test_parse_age_half():
    assert parse_dates('18 and a half', BIRTH) == date(2018, 7, 1)

def test_parse_age_range():
    start, end = parse_dates('15-16', BIRTH)
    assert start == date(2015, 1, 7)
    assert end == date(2016, 12, 31)

def test_invalid_decimal_raises():
    with pytest.raises(ValueError):
        parse_dates('18.7', BIRTH)

def test_parse_russian_age_range():
    start, end = parse_dates('С 13 до 23 лет', BIRTH)
    assert start == date(2013, 1, 7)
    assert end == date(2023, 12, 31)

def test_parse_russian_age_half_dot():
    assert parse_dates('С 16.5 лет', BIRTH) == date(2016, 7, 1)

def test_parse_russian_age_half_comma():
    assert parse_dates('С 16,5 лет', BIRTH) == date(2016, 7, 1)

def test_parse_russian_age_half_range():
    start, end = parse_dates('С 16,5 до 17 лет', BIRTH)
    assert start == date(2016, 7, 7)
    assert end == date(2017, 12, 31)

def test_parse_month_range_russian():
    start, end = parse_dates('С мая 2024 до декабря 2024', BIRTH)
    assert start == date(2024, 5, 1)
    assert end == date(2024, 12, 1)

def test_parse_full_date_range():
    start, end = parse_dates('С 19.01.2004 до 17.03.2021', BIRTH)
    assert start == date(2004, 1, 19)
    assert end == date(2021, 3, 17)
