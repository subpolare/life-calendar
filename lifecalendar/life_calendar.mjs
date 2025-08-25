// Дополнительные кружочки зеленым, а потерянные серым

import { createCanvas, registerFont } from 'canvas';
import crypto from 'crypto';
import path from 'path';
import fs from 'fs';

const logger = {
  _fmt(level, msg) {
    const ts = new Date().toISOString().replace('T', ' ').substring(0, 19);
    console.log(`${ts} ${level.toUpperCase()} JavaScript Life calendar: ${msg}`);
  },
  info(msg)  { this._fmt('info',  msg); },
  error(msg, err) {
    const full = err ? `${msg} ${err.stack || err}` : msg;
    this._fmt('error', full);
  }
};

process.on('uncaughtException', err => {
  logger.error('Unhandled exception', err);
});

process.on('unhandledRejection', err => {
  logger.error('Unhandled rejection', err);
});

const FONT_PATH = path.resolve('../fonts');
registerFont(path.join(FONT_PATH, 'Montserrat-Bold.ttf'   ), { family: 'Montserrat', weight: '900'});
registerFont(path.join(FONT_PATH, 'Montserrat-Black.ttf'  ), { family: 'Montserrat', weight: '700'});
registerFont(path.join(FONT_PATH, 'Montserrat-Regular.ttf'), { family: 'Montserrat', weight: '400'});

const CANVAS_W       = 1600;
const PADDING_X      = 120;
const PADDING_TOP    = 300;
const PADDING_BOTTOM = 60;
const ROW_HEIGHT     = 25;

const FINAL_W = 2160;
const FINAL_H = 3840;

const COLORS = {
  done:    '#D0783B',
  outline: '#b0b7d0',
  during:  '#EECE7B',
  text:    '#120C0B', 
  extra:   '#A8E6A1',
  missing: '#E5E7EB'
};

const TMP_DIR = path.resolve('../tmp');
if (!fs.existsSync(TMP_DIR)) fs.mkdirSync(TMP_DIR, { recursive: true });

export function createCalendar (birthday, opts = {}) {
  const {
    lifeExpectancy = 80,
    female         = true,
    event          = null,
    label          = '',
    transparent    = false,
    outfile        = path.join(TMP_DIR, `${crypto.randomBytes(8).toString('hex')}.png`)
  } = opts;

  logger.info('Creating calendar');

  const baseExpectancy = female ? 80 : 70;
  const rowsYears      = Math.max(baseExpectancy, lifeExpectancy);
  const canvasH        = PADDING_TOP + PADDING_BOTTOM + (rowsYears + 1) * ROW_HEIGHT;
  const canvas         = createCanvas(CANVAS_W, canvasH);
  const ctx            = canvas.getContext('2d');

  if (!transparent) {
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, CANVAS_W, canvasH);
  }

  const today      = new Date();
  const lifeWeeks  = Math.floor((today - birthday) / (7 * 24 * 3600 * 1000));
  const weekDX     = (CANVAS_W - PADDING_X * 2) / 52;

  let eventStartWeek = null, eventEndWeek = null;
  if (event) {
    let start, end;
    if (Array.isArray(event)) [start, end] = event;
    else { start = event; end = today; }
    const startWeeks = Math.floor((today - start) / (7 * 24 * 3600 * 1000));
    const endWeeks   = Math.floor((today - end)   / (7 * 24 * 3600 * 1000));
    eventStartWeek   = lifeWeeks - startWeeks;
    eventEndWeek     = lifeWeeks - endWeeks;
  }

  let weekNumber = 0;
  for (let y = 0; y < rowsYears + 1; y++) { 
    const yPix          = PADDING_TOP + y * ROW_HEIGHT + ROW_HEIGHT / 2;
    const isExtraZone   = lifeExpectancy > baseExpectancy && y >= baseExpectancy && y <= lifeExpectancy;
    const isMissingZone = lifeExpectancy < baseExpectancy && y >= lifeExpectancy && y <= baseExpectancy;

    for (let w = 0; w < 52; w++) {
      const x = PADDING_X + w * weekDX + weekDX / 2;
      weekNumber += 1;

      let fc = 'white';
      let ec = COLORS.outline;
      const isPast = (weekNumber <= lifeWeeks);
      if (isPast) fc = ec = COLORS.done;

      if (eventStartWeek !== null && weekNumber >= eventStartWeek && weekNumber <= eventEndWeek) {
        ec = COLORS.during;
        if (isPast) fc = COLORS.during;
      }

      if (!isPast) {
        if (isExtraZone) {
          ec = COLORS.extra;
        } else if (isMissingZone) {
          ec = COLORS.missing;
        }
      }

      ctx.lineWidth = 2.5;
      ctx.strokeStyle = ec;
      ctx.fillStyle   = fc;
      ctx.beginPath();
      ctx.arc(x, yPix, weekDX * 0.35, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
  }

  for (let y = 0; y < rowsYears + 1; y++) { 
    const yPix = PADDING_TOP + y * ROW_HEIGHT + ROW_HEIGHT / 2;
    ctx.fillStyle = COLORS.text;
    ctx.font = (y % 10 === 0 ? '900 18px' : '16px') + ' Montserrat';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${y}`, PADDING_X - 50, yPix);
  }

  ctx.textAlign = 'center';
  ctx.fillStyle = COLORS.text;
  ctx.font = 'bold 134px Montserrat';
  ctx.fillText('Календарь жизни', CANVAS_W / 2, PADDING_TOP / 2 - 60);
  ctx.font = 'bold 34px Montserrat';
  ctx.fillText('Время на Земле ограничено и очень важно. На что ты его потратишь?', CANVAS_W / 2, PADDING_TOP / 2 + 40);

  const arrowY = PADDING_TOP - 20;
  ctx.font = '900 24px Montserrat';
  const labelarrow = 'Недели жизни';
  const textW = ctx.measureText(labelarrow).width;
  
  const startX = PADDING_X + 5;
  const endX   = startX + textW + 50;
  
  ctx.strokeStyle = COLORS.text;
  ctx.lineWidth   = 3;
  ctx.beginPath();
  ctx.moveTo(startX, arrowY);
  ctx.lineTo(endX, arrowY);
  ctx.stroke();
  
  ctx.fillStyle = COLORS.text;
  ctx.beginPath();
  ctx.moveTo(endX, arrowY - 8);
  ctx.lineTo(endX, arrowY + 8);
  ctx.lineTo(endX + 14, arrowY);
  ctx.closePath();
  ctx.fill();
  
  ctx.textAlign = 'left';
  ctx.fillText(labelarrow, startX, arrowY - 20);

  if (eventStartWeek !== null && label) {
    const ageStart = eventStartWeek / 52;
    const ageEnd   = eventEndWeek   / 52;
    const midAge   = (ageStart + ageEnd) / 2;
    const yPix     = PADDING_TOP + midAge * ROW_HEIGHT;

    ctx.save();
    ctx.translate(CANVAS_W - PADDING_X / 3 - 50, yPix);
    ctx.rotate(Math.PI / 2);
    ctx.fillStyle = COLORS.during;
    ctx.font = 'bold 22px Montserrat';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label.toUpperCase(), 0, 0);
    ctx.restore();
  }

  const finalCanvas = createCanvas(FINAL_W, FINAL_H);
  const fctx = finalCanvas.getContext('2d');

  fctx.fillStyle = 'white';
  fctx.fillRect(0, 0, FINAL_W, FINAL_H);

  const srcW = CANVAS_W;
  const srcH = canvasH;

  const scale = Math.min(FINAL_W / srcW, FINAL_H / srcH);
  const drawW = Math.round(srcW * scale);
  const drawH = Math.round(srcH * scale);

  const offsetX = Math.floor((FINAL_W - drawW) / 2);
  const offsetY = Math.floor((FINAL_H - drawH) / 2);

  fctx.imageSmoothingEnabled = true;
  fctx.imageSmoothingQuality = 'high';

  fctx.drawImage(canvas, 0, 0, srcW, srcH, offsetX, offsetY, drawW, drawH);

  const outStream = fs.createWriteStream(outfile);
  outStream.on('error', err => logger.error('Error writing calendar', err));
  finalCanvas.createPNGStream().on('error', err => logger.error('Error generating PNG', err))
                              .pipe(outStream);
  outStream.on('finish', () => logger.info(`Calendar saved to ${outfile} (2160x3840)`));
  return outfile;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const birthday = new Date(2004, 0, 19);
    const event    = [new Date(2016, 0, 10), new Date(2026, 11, 31)];
    const label    = 'Образование';
    createCalendar(birthday, { lifeExpectancy: 80, event, label });
    logger.info('Sample calendar generated');
  } catch (err) {
    logger.error('Sample calendar generation failed', err);
  }
}