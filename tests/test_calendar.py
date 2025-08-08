from pathlib import Path
from datetime import date
import secrets, pytest, shutil
from lifecalendar.bridge import create_calendar

def test_create_calendar_creates_file(tmp_path: Path):
    if shutil.which('node') is None:
        pytest.skip('Node.js не установлен')

    out = tmp_path / f'{secrets.token_hex(8)}.png'

    create_calendar(
        birthday        = date(2004, 1, 19),
        fname           = str(out),
        life_expectancy = 100,
        event           = (date(2011, 9, 1), date(2028, 6, 22)),
        label           = 'Образование',
    )

    assert out.exists(), 'Файл не создан'
    assert out.stat().st_size > 0, 'Файл пустой'
