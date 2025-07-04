from __future__ import annotations

import bisect
import numpy as np
from typing import NamedTuple
from collections import defaultdict
from datetime import date, timedelta

from matplotlib.font_manager import fontManager
import matplotlib.pyplot as plt

fontManager.addfont('fonts/Montserrat-Black.ttf')
fontManager.addfont('fonts/Montserrat-Regular.ttf')
plt.rcParams['font.family'] = 'Montserrat'
plt.rcParams['font.weight'] = 'regular'

TITLE_FONT = {
    'family': 'Montserrat',
    'weight': 'black',
    'size': plt.rcParams.get('font.size', 12) * 4.4
}

SUBTITLE_FONT = {
    'family': 'Montserrat',
    'weight': 'black',
    'size': plt.rcParams.get('font.size', 12) * 1.115
}

BLACK_FONT = {
    'family': 'Montserrat',
    'weight': 'bold',
    'size': plt.rcParams.get('font.size', 12) * 0.6
}

TEXT_FONT = {
    'family': 'Montserrat',
    'weight': 'regular',
    'size': plt.rcParams.get('font.size', 12) * 0.6
}

def create_calendar(birthday, life: list[LifeStage], fname: str = 'calendar-of-life.png', h = 13, w = 9):
    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize = (w, h))
    ax.set_axis_off()
    plt.text(6.5, 9.55, 'Календарь жизни', ha = 'center', **TITLE_FONT) 
    plt.text(6.5, 9.25, 'Время на Земле ограничено и очень важно. На что ты его потратишь?', ha = 'center', **SUBTITLE_FONT)

    days_per_week = 365.25 / 52
    weeks_of_life = (date.today() - birthday).days // 7 
    weeks_of_life_past = np.cumsum([(b.date - a.date).days / days_per_week for a, b in zip(life, life[1:])])

    facecolors = {e.stage: e.color for e in life[1:]}
    facecolors['future'] = 'white'
    edgecolors = {e.stage: e.color for e in life[1:]} 
    edgecolors['future'] = 'k' 
    
    data = defaultdict(list)
    week_num = 0
    weeks = np.linspace(0, h, 52)
    years = np.linspace(w, 0, 80)

    for year in years:
        for week in weeks:
            week_num += 1 
            if week_num > weeks_of_life: 
                stage = 'future' 
            else: 
                index = bisect.bisect_left(weeks_of_life_past, week_num) + 1
                stage = life[index].stage
            data[stage].append((week, year)) 

    for k, v in data.items():
        ax.scatter(*zip(*v), edgecolors=edgecolors[k], facecolor=facecolors[k], label=k)

    for i, year in enumerate(years):
        if (i + 1) % 10 == 0 or i == 0:
            ax.text(
                -0.4,
                year,
                f'{i + 1}',
                horizontalalignment='center',
                verticalalignment='center',
                **BLACK_FONT
            )
        else: 
            ax.text(
                -0.4,
                year,
                f'{i + 1}',
                horizontalalignment='center',
                verticalalignment='center',
                **TEXT_FONT
            )

    plt.savefig(fname, dpi = 300)

class LifeStage(NamedTuple):
    stage: str
    date: date
    color: str | None = None

if __name__ == '__main__':
    birthday = date(2004, 1, 19)
    life = [
        LifeStage('Рождение', birthday),
        LifeStage('Раннее детство', birthday + timedelta(days = 6 * 365.25),  'C0'),
        LifeStage('Школьные годы', birthday + timedelta(days = 17 * 365.25), 'C1'),
        LifeStage('Университет', birthday + timedelta(days = 24 * 365.25), 'C2'),
        LifeStage('Взрослая жизнь', birthday + timedelta(days = 64 * 365.25), 'C4'),
        LifeStage('Старость', birthday + timedelta(days = 99 * 365.25), 'C5'),
    ]
    create_calendar(birthday, life, fname = 'calendar-of-life.png')