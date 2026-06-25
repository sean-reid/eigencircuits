const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTHS_LONG = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

function pad(n: number): string {
  return n.toString().padStart(2, '0');
}

/** "2026-06-24" -> "Wed, 24 Jun 2026". */
export function formatDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  return `${WEEKDAYS[d.getUTCDay()]}, ${pad(d.getUTCDate())} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

/** "2026-06-24T13:25:59Z" -> "Wed, 24 Jun 2026 13:25:59 UTC". */
export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  const day = `${WEEKDAYS[d.getUTCDay()]}, ${pad(d.getUTCDate())} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
  return `${day} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`;
}

/** "2026-05" -> "May 2026". */
export function formatMonth(period: string): string {
  const [y, m] = period.split('-');
  const idx = Number(m) - 1;
  const name = idx >= 0 && idx < 12 ? MONTHS_LONG[idx] : period;
  return `${name} ${y}`;
}

export function downloadTex(id: string, tex: string): void {
  download(`eiGen-${id}.tex`, new Blob([tex], { type: 'text/x-tex' }));
}

function download(name: string, blob: Blob): void {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}
