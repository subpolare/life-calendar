from __future__ import annotations

import bisect
import numpy as np
from PIL import Image
from typing import NamedTuple
from datetime import date, timedelta

from matplotlib.font_manager import fontManager
from matplotlib.patches import FancyArrowPatch
import matplotlib.pyplot as plt

# ———————————————————————————————————————— FONT SETTINGS ————————————————————————————————————————

fontManager.addfont('fonts/Montserrat-Bold.ttf')
fontManager.addfont('fonts/Montserrat-Black.ttf')
fontManager.addfont('fonts/Montserrat-Regular.ttf')
plt.rcParams['font.family'] = 'Montserrat'
plt.rcParams['font.weight'] = 'regular'

TITLE_FONT =    {'family': 'Montserrat', 'weight': 'black',   'size': plt.rcParams.get('font.size', 12) * 4.4}
SUBTITLE_FONT = {'family': 'Montserrat', 'weight': 'black',   'size': plt.rcParams.get('font.size', 12) * 1.115}
BLACK_FONT =    {'family': 'Montserrat', 'weight': 'black',   'size': plt.rcParams.get('font.size', 12) * 0.6}
BOLD_FONT =     {'family': 'Montserrat', 'weight': 'bold',    'size': plt.rcParams.get('font.size', 12) * 0.6}
TEXT_FONT =     {'family': 'Montserrat', 'weight': 'regular', 'size': plt.rcParams.get('font.size', 12) * 0.6}

# ———————————————————————————————————————— CALENDAR RENDERING ————————————————————————————————————————

def create_calendar(birthday, life: list[LifeStage], fname, h = 13, w = 9):
    plt.rcParams.update(plt.rcParamsDefault)
    fig, ax = plt.subplots(figsize = (w, h))
    ax.set_axis_off()

    # Rendering circles in a calendar

    days_per_week = 365.25 / 52
    weeks_of_life = (date.today() - birthday).days // 7 
    weeks_of_life_past = np.cumsum([(b.date - a.date).days / days_per_week for a, b in zip(life, life[1:])])

    week_num = 0
    X, Y = [], []
    FC, EC = [], []
    facecolors = {e.stage : e.color for e in life[1:]}
    edgecolors = {e.stage : e.color for e in life[1:]} 
    weeks = np.linspace(0, h, 52)
    years = np.linspace(w, 0, 81)

    for year in years:
        for week in weeks:
            week_num += 1
            stage = life[bisect.bisect_left(weeks_of_life_past, week_num) + 1].stage
            X.append(week)
            Y.append(year)
            FC.append(facecolors[stage] if week_num <= weeks_of_life else 'white')
            EC.append(edgecolors[stage])

    ax.scatter(X, Y, facecolors = FC, edgecolors = EC)

    # Adding design elements

    plt.text(6.3, 10, 'Календарь жизни', ha = 'center', va = 'center', **TITLE_FONT) 
    plt.text(6.3, 9.6, 'Время на Земле ограничено и очень важно. На что ты его потратишь?', ha = 'center', va = 'center', **SUBTITLE_FONT)

    # The right arrow 
    # arrow = FancyArrowPatch(
    #     posA = (14, 9.07), posB = (14, 7.9),
    #     arrowstyle = '-|>', connectionstyle = 'arc3, rad = 0',
    #     mutation_scale = 10, linewidth = 1,
    #     color = 'k', capstyle = 'round'
    # )
    # plt.gca().add_patch(arrow)
    # plt.text(13.8, 8.165, 'ЖИЗНЕННЫЙ ЭТАП', ha = 'center', **BLACK_FONT, rotation = 270) 

    # The left arrow 
    arrow = FancyArrowPatch(
        posA = (-0.95, 9.07), posB = (-0.95, 8.4),
        arrowstyle = '-|>', connectionstyle = 'arc3, rad = 0',
        mutation_scale = 10, linewidth = 1,
        color = 'k', capstyle = 'round'
    )
    plt.gca().add_patch(arrow)
    plt.text(-0.8, 8.63, 'ВОЗРАСТ', ha = 'center', **BOLD_FONT, rotation = 270) 

    # Upper arrow
    arrow = FancyArrowPatch(
        posA = (-0.12, 9.18), posB = (3.5, 9.18),
        arrowstyle = '-|>', connectionstyle = 'arc3, rad = 0',
        mutation_scale = 10, linewidth = 1,
        color = 'k', capstyle = 'round'
    )
    plt.gca().add_patch(arrow)
    plt.text(0.8, 9.23, 'НЕДЕЛИ В ГОДУ', ha = 'center', **BOLD_FONT) 

    # Stages of life
    plt.text(13.4, 8.53, 'РАННЕЕ\nДЕТСТВО', ha = 'center', **BLACK_FONT, rotation = 270, color = 'C0') 
    plt.text(13.4, 7.28, 'ШКОЛЬНЫЕ ГОДЫ',   ha = 'center', **BLACK_FONT, rotation = 270, color = 'C1') 
    plt.text(13.4, 6.38, 'УНИВЕРСИТЕТ',     ha = 'center', **BLACK_FONT, rotation = 270, color = 'C2') 
    plt.text(13.4, 3.60, 'ВЗРОСЛАЯ ЖИЗНЬ',  ha = 'center', **BLACK_FONT, rotation = 270, color = 'C3')
    plt.text(13.4, 0.70, 'СТАРОСТЬ',        ha = 'center', **BLACK_FONT, rotation = 270, color = 'C4') 

    # Numbering of years
    for i, year in enumerate(years):
        if (i) % 10 == 0 or i == 0:
            ax.text(-0.4, year, f'{i}', horizontalalignment='center', verticalalignment='center', **BOLD_FONT)
        else: 
            ax.text(-0.4, year, f'{i}', horizontalalignment='center', verticalalignment='center', **TEXT_FONT)

    # Image postprocessing
    plt.savefig(fname, dpi = 600)
    img = Image.open(fname)
    cropped = img.crop((700, 350, img.width - 440, img.height - 1000))
    cropped.save(fname, dpi = (600, 600))

# ———————————————————————————————————————— INITIALIZING ————————————————————————————————————————

class LifeStage(NamedTuple):
    stage: str
    date:  date
    color: str | None = None

def calendar(birthday, filename):
    life = [
        LifeStage('Рождение', birthday),
        LifeStage('Раннее детство', birthday + timedelta(days = 6 * 365.25 + 7),  'C0'),
        LifeStage('Школьные годы', birthday + timedelta(days = 18 * 365.25 + 7), 'C1'),
        LifeStage('Университет', birthday + timedelta(days = 24 * 365.25 + 7), 'C2'),
        LifeStage('Взрослая жизнь', birthday + timedelta(days = 64 * 365.25), 'C3'),
        LifeStage('Старость', birthday + timedelta(days = 99 * 365.25), 'C4'),
    ]
    create_calendar(birthday, life, fname = filename)

if __name__ == '__main__':

    birthday = date(2004, 1, 19)
    filename = 'calendar-of-life.png'
    
    calendar(birthday, filename)