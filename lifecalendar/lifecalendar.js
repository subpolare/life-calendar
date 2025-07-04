// Compute color per life stage with Russian labels
const STAGE_COLORS = [
  '#A3A380', // раннее детство
  '#C0B887', // школьные годы
  '#D7CE93', // высшее образование
  '#E8D9B5', // взрослая жизнь
  '#EFEBCE', // средний возраст
  '#D8A48F', // пожилой возраст
  '#BB8588'  // возраст долгожителей
];

function getBirthDate() {
  const params = new URLSearchParams(window.location.search);
  const y = params.get('year');
  const m = params.get('month');
  const d = params.get('day');
  if (y && m && d) {
    return new Date(Number(y), Number(m) - 1, Number(d));
  }
  // Change birthdate here if needed
  return new Date('2004-01-19');
}

function weeksSince(date) {
  const seconds = (Date.now() - date.getTime()) / 1000;
  return Math.round(seconds / (60 * 60 * 24 * 7));
}

const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const YEAR_MS = 365.25 * 24 * 60 * 60 * 1000;

function stageForDate(date, birth) {
  const baseY = birth.getFullYear();
  const earlyEnd = new Date(baseY + 7, 8, 1);            // 1 Sep after 7th bday
  const schoolEnd = new Date(baseY + 18, 5, 20);         // 20 Jun after 18th
  const uniStart = new Date(baseY + 19, 8, 1);           // 1 Sep after 19th
  const uniEnd = new Date(baseY + 24, 5, 20);            // 20 Jun after 24th
  const adultEnd = new Date(baseY + 45, birth.getMonth(), birth.getDate());
  const midEnd = new Date(baseY + 59, birth.getMonth(), birth.getDate());
  const seniorEnd = new Date(baseY + 89, birth.getMonth(), birth.getDate());

  if (date < earlyEnd) return 0;                         // 0-6
  if (date >= earlyEnd && date <= schoolEnd) return 1;   // 7-18
  if (date >= uniStart && date <= uniEnd) return 2;      // 19-24
  if (date < adultEnd) return 3;                         // 25-45
  if (date < midEnd) return 4;                           // 46-59
  if (date < seniorEnd) return 5;                        // 60-89
  return 6;                                              // 90-100
}

function colorForStage(stage, lived) {
  const c = STAGE_COLORS[stage] || '#000000';
  if (lived) return c;
  // add low opacity for future weeks
  return c + '33';
}

document.addEventListener('DOMContentLoaded', () => {
  const birthDate = getBirthDate();
  const livedWeeks = weeksSince(birthDate);
  const container = document.getElementById('calendar');
  const weeksInYear = 52;

  for (let year = 0; year <= 100; year++) {
    const row = document.createElement('div');
    row.className = 'year-row';
    const label = document.createElement('div');
    label.className = 'year-label';
    label.textContent = year;
    row.appendChild(label);
    for (let week = 0; week < weeksInYear; week++) {
      const index = year * weeksInYear + week;
      const date = new Date(birthDate.getTime() + index * WEEK_MS);
      const stage = stageForDate(date, birthDate);
      const lived = index < livedWeeks;
      const circle = document.createElement('span');
      circle.className = 'circle';
      const color = colorForStage(stage, lived);
      circle.style.borderColor = color;
      if (lived) {
        circle.style.backgroundColor = color;
      }
      row.appendChild(circle);
    }
    container.appendChild(row);
  }
});
