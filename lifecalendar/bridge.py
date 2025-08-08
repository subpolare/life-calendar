from __future__ import annotations

import subprocess, json
from pathlib import Path
from datetime import date
from typing import Optional, Tuple, Union

ROOT = Path(__file__).resolve().parents[1]
CALENDAR_DIR = ROOT / 'lifecalendar'

def create_calendar(
    birthday: date, fname: str, female: bool = True, transparent: bool = False, expectation = None, 
    event: Union[Tuple[date, date], date, None] = None, label: Optional[str] = None
) -> str:

    if not expectation: 
        expectation = 80 if female else 70

    if event:
        if isinstance(event, tuple):
            start, end = event
            event_js = f'[new Date("{start.isoformat()}"), new Date("{end.isoformat()}")]'
        else:
            event_js = f'new Date("{event.isoformat()}")'
    else:
        event_js = 'null'

    js = '\n'.join([
        'import { createCalendar } from "./life_calendar.mjs";'
        f'const birthday = new Date("{birthday.isoformat()}");'
        'const opts={',
        f'\tlifeExpectancy:{expectation},',
        f'\tevent:{event_js},',
        f'\tlabel: {json.dumps(label) if label is not None else "null"},',
        f'\toutfile:{json.dumps(str(Path(fname).resolve()))},',
        '};',
        'createCalendar(birthday, opts);'
    ])

    subprocess.run(
        ['node', '--input-type=module', '-e', js],
        cwd   = CALENDAR_DIR,
        check = True,
    )

    return fname