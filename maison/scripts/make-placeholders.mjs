// Draws a stand-in picture for every piece (and the house pictures) until real
// photographs arrive. Run with `npm run placeholders`. It only writes a file
// that is missing, so a real photo dropped in as 1.jpg is never overwritten.
// Pass --force to redraw everything.
import sharp from 'sharp';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const force = process.argv.includes('--force');
const W = 1200;
const H = 1500;
const BRASS = '#B8925A';

/** Darken (amt < 0) or lighten (amt > 0) a hex colour. */
function shade(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const ch = [n >> 16, (n >> 8) & 255, n & 255].map((c) =>
    Math.round(amt < 0 ? c * (1 + amt) : c + (255 - c) * amt),
  );
  return '#' + ch.map((c) => c.toString(16).padStart(2, '0')).join('');
}

/** Mirror a list of points across the vertical centre line. */
const mirror = (pts) => pts.map(([x, y]) => [W - x, y]);
const poly = (pts, fill) => `<polygon points="${pts.map((p) => p.join(',')).join(' ')}" fill="${fill}" stroke="${fill}" stroke-width="6" stroke-linejoin="round"/>`;
const pair = (pts, fill) => poly(pts, fill) + poly(mirror(pts), fill);
const floor = (cx, y, rx, ground) => `<ellipse cx="${cx}" cy="${y}" rx="${rx}" ry="${rx * 0.08}" fill="${shade(ground, -0.08)}"/>`;

// Each drawing receives the piece colour (c) and the ground (g) and returns SVG shapes.
const drawings = {
  coat(c) {
    const d = shade(c, -0.18);
    return [
      poly([[520, 220], [680, 220], [800, 270], [850, 330], [880, 1330], [320, 1330], [350, 330], [400, 270]], c),
      pair([[400, 270], [350, 330], [300, 760], [285, 1000], [370, 1010], [400, 760], [430, 420]], d),
      pair([[520, 220], [606, 540], [548, 580], [470, 300]], d),
      `<rect x="597" y="540" width="8" height="790" fill="${d}"/>`,
      `<rect x="346" y="770" width="508" height="44" fill="${d}"/>`,
      `<rect x="560" y="758" width="80" height="68" fill="none" stroke="${BRASS}" stroke-width="12"/>`,
      pair([[430, 960], [520, 960], [520, 980], [430, 980]], d),
    ].join('');
  },
  overcoat(c) {
    const d = shade(c, -0.2);
    return [
      poly([[520, 230], [680, 230], [810, 280], [850, 340], [860, 1250], [340, 1250], [350, 340], [390, 280]], c),
      pair([[390, 280], [350, 340], [305, 780], [295, 1010], [375, 1020], [405, 780], [430, 430]], d),
      pair([[520, 230], [600, 600], [560, 620], [450, 330], [500, 380], [470, 280]], d),
      `<rect x="597" y="600" width="8" height="650" fill="${d}"/>`,
      [700, 840, 980].map((y) => `<circle cx="640" cy="${y}" r="14" fill="${shade(c, -0.45)}"/>`).join(''),
      pair([[420, 900], [530, 900], [530, 930], [420, 930]], d),
    ].join('');
  },
  dress(c, g) {
    const d = shade(c, -0.16);
    const pleats = Array.from({ length: 10 }, (_, i) =>
      poly([[492 + i * 22, 640], [330 + i * 56, 1330], [358 + i * 56, 1330]], d),
    ).join('');
    return [
      pair([[500, 250], [440, 290], [430, 360], [470, 360]], d),
      poly([[500, 250], [700, 250], [740, 300], [715, 640], [485, 640], [460, 300]], c),
      `<path d="M535 250 Q600 345 665 250 Z" fill="${g}"/>`,
      poly([[485, 640], [715, 640], [890, 1330], [310, 1330]], c),
      pleats,
      `<rect x="480" y="622" width="240" height="30" fill="${shade(c, -0.3)}"/>`,
    ].join('');
  },
  knit(c, g) {
    const d = shade(c, -0.14);
    const rib = (x0, x1, y, h) =>
      Array.from({ length: Math.floor((x1 - x0) / 20) }, (_, i) =>
        `<rect x="${x0 + i * 20}" y="${y}" width="10" height="${h}" fill="${d}"/>`,
      ).join('');
    return [
      pair([[380, 340], [300, 520], [250, 930], [340, 950], [380, 600], [420, 420]], d),
      poly([[470, 300], [730, 300], [820, 340], [840, 1020], [360, 1020], [380, 340]], c),
      rib(370, 830, 950, 70),
      `<ellipse cx="600" cy="305" rx="92" ry="34" fill="${d}"/>`,
      `<ellipse cx="600" cy="298" rx="70" ry="22" fill="${g}"/>`,
    ].join('');
  },
  blouson(c) {
    const d = shade(c, -0.3);
    return [
      pair([[390, 330], [320, 420], [270, 820], [350, 840], [400, 560], [430, 400]], shade(c, -0.12)),
      poly([[490, 270], [710, 270], [810, 330], [830, 880], [370, 880], [390, 330]], c),
      `<rect x="370" y="860" width="460" height="60" fill="${d}"/>`,
      pair([[490, 270], [600, 360], [600, 400], [470, 330], [450, 290]], d),
      `<rect x="594" y="380" width="12" height="540" fill="${BRASS}"/>`,
      pair([[450, 600], [540, 560], [545, 575], [455, 615]], d),
    ].join('');
  },
  trousers(c) {
    const d = shade(c, -0.18);
    return [
      `<rect x="440" y="240" width="320" height="56" fill="${d}"/>`,
      poly([[440, 296], [760, 296], [795, 1360], [625, 1360], [600, 560], [575, 1360], [405, 1360]], c),
      pair([[520, 300], [530, 300], [495, 1360], [485, 1360]], d),
      [470, 560, 640, 730].map((x) => `<rect x="${x}" y="232" width="12" height="70" fill="${shade(c, -0.35)}"/>`).join(''),
    ].join('');
  },
  shirt(c) {
    const d = shade(c, -0.1);
    return [
      pair([[380, 300], [310, 480], [270, 1020], [350, 1040], [395, 620], [430, 410]], d),
      poly([[470, 260], [730, 260], [820, 300], [830, 1160], [370, 1160], [380, 300]], c),
      pair([[480, 250], [600, 290], [600, 330], [520, 380], [470, 280]], shade(c, -0.18)),
      `<rect x="584" y="300" width="32" height="860" fill="${d}"/>`,
      [420, 560, 700, 840, 980].map((y) => `<circle cx="600" cy="${y}" r="9" fill="${shade(c, -0.35)}"/>`).join(''),
    ].join('');
  },
  trunkBag(c, g) {
    const d = shade(c, -0.25);
    const corner = (x, y, sx, sy) =>
      poly([[x, y], [x + 70 * sx, y], [x + 70 * sx, y + 22 * sy], [x + 22 * sx, y + 22 * sy], [x + 22 * sx, y + 70 * sy], [x, y + 70 * sy]], BRASS);
    return [
      floor(600, 1060, 300, g),
      `<path d="M500 600 Q600 430 700 600" fill="none" stroke="${d}" stroke-width="30"/>`,
      `<rect x="370" y="590" width="460" height="460" fill="${c}"/>`,
      `<rect x="460" y="590" width="36" height="460" fill="${d}"/>`,
      `<rect x="704" y="590" width="36" height="460" fill="${d}"/>`,
      `<rect x="370" y="700" width="460" height="18" fill="${d}"/>`,
      `<rect x="566" y="680" width="68" height="84" fill="${BRASS}"/>`,
      `<circle cx="600" cy="712" r="10" fill="${shade(BRASS, -0.4)}"/>`,
      corner(370, 590, 1, 1), corner(830, 590, -1, 1), corner(370, 1050, 1, -1), corner(830, 1050, -1, -1),
    ].join('');
  },
  weekender(c, g) {
    const d = shade(c, -0.28);
    return [
      floor(600, 1080, 360, g),
      `<path d="M470 700 Q600 470 730 700" fill="none" stroke="${d}" stroke-width="30"/>`,
      `<path d="M260 840 Q260 660 600 660 Q940 660 940 840 L940 1070 L260 1070 Z" fill="${c}"/>`,
      `<path d="M260 840 Q260 660 400 668 L400 1070 L260 1070 Z" fill="${d}"/>`,
      `<path d="M940 840 Q940 660 800 668 L800 1070 L940 1070 Z" fill="${d}"/>`,
      `<rect x="400" y="662" width="400" height="14" fill="${BRASS}"/>`,
      `<rect x="572" y="760" width="56" height="64" fill="${BRASS}"/>`,
      `<path d="M582 760 Q600 720 618 760" fill="none" stroke="${BRASS}" stroke-width="10"/>`,
    ].join('');
  },
  tote(c, g) {
    const d = shade(c, -0.25);
    return [
      floor(600, 1130, 290, g),
      `<path d="M450 620 Q480 400 560 620" fill="none" stroke="${d}" stroke-width="26"/>`,
      `<path d="M640 620 Q720 400 750 620" fill="none" stroke="${d}" stroke-width="26"/>`,
      poly([[370, 610], [830, 610], [870, 1120], [330, 1120]], c),
      poly([[370, 610], [420, 610], [390, 1120], [330, 1120]], d),
      poly([[830, 610], [780, 610], [810, 1120], [870, 1120]], d),
      [455, 545, 655, 745].map((x) => `<circle cx="${x}" cy="640" r="11" fill="${BRASS}"/>`).join(''),
    ].join('');
  },
  scarf(c) {
    const d = shade(c, -0.22);
    const star = Array.from({ length: 16 }, (_, i) => {
      const r = i % 2 ? 70 : 210;
      const a = (Math.PI / 8) * i - Math.PI / 2;
      return [600 + r * Math.cos(a), 750 + r * Math.sin(a)];
    });
    return [
      `<g transform="rotate(-8 600 750)">`,
      `<rect x="310" y="460" width="580" height="580" fill="${c}"/>`,
      `<rect x="340" y="490" width="520" height="520" fill="none" stroke="${d}" stroke-width="22"/>`,
      `<circle cx="600" cy="750" r="230" fill="none" stroke="${BRASS}" stroke-width="10"/>`,
      poly(star, d),
      `<circle cx="600" cy="750" r="34" fill="${BRASS}"/>`,
      `</g>`,
    ].join('');
  },
  belt(c, g) {
    const d = shade(c, -0.2);
    return [
      `<circle cx="600" cy="780" r="290" fill="none" stroke="${c}" stroke-width="78"/>`,
      `<circle cx="600" cy="780" r="196" fill="none" stroke="${d}" stroke-width="78"/>`,
      `<rect x="520" y="430" width="160" height="110" fill="${g}"/>`,
      `<rect x="530" y="438" width="140" height="96" fill="none" stroke="${BRASS}" stroke-width="20"/>`,
      `<rect x="594" y="430" width="14" height="110" fill="${BRASS}"/>`,
    ].join('');
  },
  trunk(c, g) {
    const d = shade(c, -0.3);
    const slat = (y) => `<rect x="320" y="${y}" width="560" height="30" fill="${d}"/>`;
    const corner = (x, y, sx, sy) =>
      poly([[x, y], [x + 90 * sx, y], [x + 90 * sx, y + 26 * sy], [x + 26 * sx, y + 26 * sy], [x + 26 * sx, y + 90 * sy], [x, y + 90 * sy]], BRASS);
    return [
      floor(600, 1320, 340, g),
      `<rect x="320" y="300" width="560" height="1010" fill="${c}"/>`,
      slat(300), slat(560), slat(860), slat(1280),
      `<rect x="420" y="300" width="34" height="1010" fill="${d}"/>`,
      `<rect x="746" y="300" width="34" height="1010" fill="${d}"/>`,
      `<rect x="560" y="520" width="80" height="110" fill="${BRASS}"/>`,
      `<circle cx="600" cy="560" r="12" fill="${shade(BRASS, -0.4)}"/>`,
      `<rect x="880" y="740" width="26" height="160" fill="${d}"/>`,
      corner(320, 300, 1, 1), corner(880, 300, -1, 1), corner(320, 1310, 1, -1), corner(880, 1310, -1, -1),
    ].join('');
  },
};

// slug → drawing, colour, ground, the point the close-up (2.jpg) zooms into,
// and for small drawings a fit: [scale, the drawing's vertical centre] for 1.jpg.
const pieces = {
  'double-face-wool-coat': { draw: 'coat', c: '#B88A5E', g: '#E6DED3', alt: '#D7CBBB', zoom: [600, 790] },
  'pleated-silk-dress': { draw: 'dress', c: '#2B2A33', g: '#E9E4DD', alt: '#D9D2C8', zoom: [600, 900] },
  'cashmere-rib-knit': { draw: 'knit', c: '#D9CBB4', g: '#5A4636', alt: '#4A3A2D', zoom: [600, 980], fit: [1.15, 660] },
  'tailored-overcoat': { draw: 'overcoat', c: '#3A3F45', g: '#E4DED6', alt: '#D3CBC0', zoom: [560, 700] },
  'lambskin-blouson': { draw: 'blouson', c: '#4A2F22', g: '#E7E1D9', alt: '#D8CFC3', zoom: [600, 600], fit: [1.3, 595] },
  'pleated-wool-trousers': { draw: 'trousers', c: '#6B6258', g: '#EEE9E2', alt: '#DCD4C9', zoom: [600, 300] },
  'cotton-poplin-shirt': { draw: 'shirt', c: '#F3F0EA', g: '#3F4A52', alt: '#333D44', zoom: [580, 320], fit: [1.12, 705] },
  'trunk-shoulder-bag': { draw: 'trunkBag', c: '#6E4A2E', g: '#ECE6DE', alt: '#DDD3C6', zoom: [600, 700], fit: [1.2, 760] },
  'voyage-weekender-45': { draw: 'weekender', c: '#8A6A47', g: '#E9E3DB', alt: '#D9CFC2', zoom: [600, 780], fit: [1.2, 780] },
  'atelier-tote': { draw: 'tote', c: '#1F1D1B', g: '#E7E0D6', alt: '#D6CCBF', zoom: [600, 650], fit: [1.2, 770] },
  'silk-square-90': { draw: 'scarf', c: '#7A2E2A', g: '#EDE7DF', alt: '#DED5C9', zoom: [600, 750], fit: [1.15, 750] },
  'brass-buckle-belt': { draw: 'belt', c: '#3B2A20', g: '#E8E2DA', alt: '#D8CFC4', zoom: [600, 480], fit: [1.15, 760] },
};

// Pictures for the house's own pages.
const house = {
  trunk: { draw: 'trunk', c: '#6E4A2E', g: '#E4DCD1' },
  lock: { draw: 'trunk', c: '#6E4A2E', g: '#D6CBBE', zoom: [600, 575], scale: 3 },
  canvas: { draw: 'weekender', c: '#8A6A47', g: '#2E2620', zoom: [600, 790], scale: 2.4 },
  thread: { draw: 'coat', c: '#B88A5E', g: '#3A2E26', zoom: [600, 520], scale: 2.6 },
};

function svg({ draw, c, g, zoom, scale = 2, fit }) {
  const vw = W / (zoom ? scale : 1);
  const vh = H / (zoom ? scale : 1);
  const [cx, cy] = zoom ?? [W / 2, H / 2];
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="${cx - vw / 2} ${cy - vh / 2} ${vw} ${vh}">
    <rect x="-2000" y="-2000" width="6000" height="6000" fill="${g}"/>
    <g transform="${fit ? `translate(600 750) scale(${fit[0]}) translate(-600 -${fit[1]})` : ''}">${drawings[draw](c, g)}</g></svg>`;
}

async function render(file, spec) {
  if (existsSync(file) && !force) return;
  mkdirSync(dirname(file), { recursive: true });
  await sharp(Buffer.from(svg(spec))).jpeg({ quality: 86, mozjpeg: true }).toFile(file);
  console.log('drew', file.replace(root + '/', ''));
}

for (const [slug, p] of Object.entries(pieces)) {
  const dir = join(root, 'src/content/pieces', slug);
  await render(join(dir, '1.jpg'), { draw: p.draw, c: p.c, g: p.g, fit: p.fit });
  await render(join(dir, '2.jpg'), { draw: p.draw, c: p.c, g: p.alt, zoom: p.zoom });
}
for (const [name, spec] of Object.entries(house)) {
  await render(join(root, 'src/assets/house', `${name}.jpg`), spec);
}
