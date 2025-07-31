"""Bridge to the Node-based life calendar generator."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import json
import subprocess
from typing import Optional, Tuple, Union


ROOT = Path(__file__).resolve().parents[1]
CALENDAR_DIR = ROOT / "calendar"


def create_calendar(
    birthday: date,
    fname: str,
    female: bool = True,
    transparent: bool = False,
    event: Union[Tuple[date, date], date, None] = None,
    label: Optional[str] = None,
) -> str:
    """Render a life calendar image via the Node implementation.

    Args:
        birthday: User birth date.
        fname: Output filename.
        female: Use female life expectancy (80) or male (70).
        transparent: Whether the background should be transparent.
        event: A single date or ``(start, end)`` tuple to highlight.
        label: Optional label for the highlighted event.

    Returns:
        Path to the generated image file.
    """

    life_expectancy = 80 if female else 70

    opts: dict[str, object] = {
        "outfile": str(Path(fname).resolve()),
        "lifeExpectancy": life_expectancy,
        "transparent": transparent,
    }
    if event:
        if isinstance(event, tuple):
            opts["event"] = [d.isoformat() for d in event]
        else:
            opts["event"] = event.isoformat()
    if label:
        opts["label"] = label

    js = (
        "import { createCalendar } from './life_calendar.mjs';"
        f"const birthday = new Date('{birthday.isoformat()}');"
        f"const opts = {json.dumps(opts)};"
        "createCalendar(birthday, opts);"
    )

    subprocess.run(
        ["node", "--input-type=module", "-e", js],
        cwd=CALENDAR_DIR,
        check=True,
    )

    return fname

