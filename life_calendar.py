from __future__ import annotations

import numpy as np
from PIL import Image
import secrets, warnings
from datetime import date
warnings.filterwarnings('ignore')

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

def create_calendar(birthday, fname, female = True, h = 13, w = 9, transparent = False, event = None, label = None):
    plt.rcParams.update(plt.rcParamsDefault)
    _, ax = plt.subplots(figsize = (w, h))
    ax.set_axis_off()

    if event:
        try: 
            start, end = event  
        except: 
            start = event 
            end   = date.today()
        start_weeks = (date.today() - start).days // 7 
        end_weeks   = (date.today() - end).days // 7 

    week_number = 0
    X, Y, FC, EC = [], [], [], []
    life_weeks = (date.today() - birthday).days // 7 

    weeks = np.linspace(0, h, 52)
    if female: 
        years = np.linspace(w, 0, 81)
    else: 
        years = np.linspace(w, 0, 71)

    for year in years:
        for week in weeks:
            week_number += 1
            X.append(week)
            Y.append(year)
            
            if not event: 
                if week_number <= life_weeks: 
                    facecolor = '#D0783B' 
                    edgecolor = '#D0783B' 
                else: 
                    facecolor = '#FFFFFF' 
                    edgecolor = '#b0b7d0' 
            else:
                if week_number <= life_weeks:
                    facecolor = "#D0783B"
                    edgecolor = '#D0783B' 
                else:
                    facecolor = '#FFFFFF'
                    edgecolor = '#b0b7d0'

                in_event = (life_weeks - start_weeks) <= week_number <= (life_weeks - end_weeks)

                if in_event:
                    edgecolor = '#EECE7B'
                    if week_number <= life_weeks:
                        facecolor = '#EECE7B'

            FC.append(facecolor)
            EC.append(edgecolor)

    ax.scatter(X, Y, facecolors = FC, edgecolors = EC)

    if event: 
        yellow = [
            y for y, fc, ec in zip(Y, FC, EC)
            if fc.lower() == '#eece7b' or ec.lower() == '#eece7b'
        ]
        y = np.mean(yellow)
        plt.text(13.4, y, label, ha = 'center', va = 'center', **BLACK_FONT, rotation = 270, color = '#EECE7B') 

    color = "#120C0B"
    plt.text(6.3, 10,  'Календарь жизни', ha = 'center', va = 'center', **TITLE_FONT, color = color) 
    plt.text(6.3, 9.6, 'Время на Земле ограничено и очень важно. На что ты его потратишь?', ha = 'center', va = 'center', **SUBTITLE_FONT, color = color)

    # The left arrow 
    arrow = FancyArrowPatch(
        posA = (-0.95, 9.07), posB = (-0.95, 8.4),
        arrowstyle = '-|>', connectionstyle = 'arc3, rad = 0',
        mutation_scale = 10, linewidth = 1,
        color = color, capstyle = 'round'
    )
    plt.gca().add_patch(arrow)
    plt.text(-0.8, 8.63, 'ВОЗРАСТ', ha = 'center', **BOLD_FONT, rotation = 270, color = color) 

    # Upper arrow
    arrow = FancyArrowPatch(
        posA = (-0.12, 9.18), posB = (3.5, 9.18),
        arrowstyle = '-|>', connectionstyle = 'arc3, rad = 0',
        mutation_scale = 10, linewidth = 1,
        color = color, capstyle = 'round'
    )
    plt.gca().add_patch(arrow)
    plt.text(0.8, 9.23, 'НЕДЕЛИ В ГОДУ', ha = 'center', **BOLD_FONT, color = color) 

    # Numbering of years
    for i, year in enumerate(years):
        if (i) % 10 == 0 or i == 0:
            ax.text(-0.4, year, f'{i}', horizontalalignment = 'center', verticalalignment = 'center', **BOLD_FONT, color = color)
        else: 
            ax.text(-0.4, year, f'{i}', horizontalalignment = 'center', verticalalignment = 'center', **TEXT_FONT, color = color)

    # Image postprocessing
    plt.savefig(fname, dpi = 600, transparent = transparent)
    img = Image.open(fname)
    cropped = img.crop((700, 350, img.width - 440, img.height - 1000))
    cropped.save(fname, dpi = (600, 600))

if __name__ == '__main__':
    birthday = date(2004, 1, 19)
    filename = f'tmp/{secrets.token_hex(8)}.png'
    event = (date(2016, 1, 7), date(2016, 12, 31))
    label = 'Школа' 
    transparent = False
    female = True 
    
    create_calendar(birthday, fname = filename, female = female, transparent = transparent, event = event, label = label)