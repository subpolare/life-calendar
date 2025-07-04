function yearToColor(year) {
  if (year <= 12) return '#2acdf1';
  if (year <= 19) return '#f87a40';
  if (year <= 34) return '#ff4fe8';
  if (year <= 49) return '#1af041';
  if (year <= 79) return '#f5aa1f';
  if (year <= 100) return '#db61b0';
  return '#000000';
}

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
    const color = yearToColor(year);
    for (let week = 0; week < weeksInYear; week++) {
      const circle = document.createElement('span');
      circle.className = 'circle';
      circle.style.borderColor = color;
      if (year * weeksInYear + week < livedWeeks) {
        circle.style.backgroundColor = color + '66';
      }
      row.appendChild(circle);
    }
    container.appendChild(row);
  }
});
