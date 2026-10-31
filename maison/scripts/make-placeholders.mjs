// Fills every image slot that has no picture yet with a flat grey stand-in
// labelled with its role and ideal size. Run with `npm run placeholders`.
// It never overwrites a file that exists, so real photos are always safe.
// Pass --force to redraw every stand-in (real photos included, so use with care).
import sharp from 'sharp';
import { existsSync, mkdirSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const force = process.argv.includes('--force');

const escape = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

function svg(w, h, lines) {
  const size = Math.round(w / 42);
  const text = lines
    .map((l, i) => `<text x="50%" y="${h / 2 + (i - (lines.length - 1) / 2) * size * 1.6}" text-anchor="middle" dominant-baseline="middle">${escape(l)}</text>`)
    .join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
    <rect width="100%" height="100%" fill="#F4F4F4"/>
    <g font-family="Helvetica, Arial, sans-serif" font-size="${size}" font-weight="600" letter-spacing="1" fill="#A3A3A3">${text}</g>
  </svg>`;
}

async function slot(file, w, h, lines) {
  if (existsSync(file) && !force) return;
  mkdirSync(dirname(file), { recursive: true });
  const img = sharp(Buffer.from(svg(w, h, lines)));
  await (file.endsWith('.png') ? img.png({ compressionLevel: 9 }) : img.jpeg({ quality: 82 })).toFile(file);
  console.log('stand-in', file.replace(root + '/', ''));
}

// The campaign pictures on the home page.
const campaign = join(root, 'src/assets/campaign');
await slot(join(campaign, 'hero.jpg'), 2400, 1600, ['HERO CAMPAIGN PHOTO', 'LANDSCAPE 3:2 · 2400 × 1600']);
await slot(join(campaign, 'editorial-large.jpg'), 1600, 2000, ['EDITORIAL · LARGE', 'PORTRAIT 4:5 · 1600 × 2000']);
await slot(join(campaign, 'editorial-small.jpg'), 1200, 1600, ['EDITORIAL · SMALL', 'PORTRAIT 3:4 · 1200 × 1600']);

// Two cut-outs per piece: the front, then the back or a detail.
const pieces = join(root, 'src/content/pieces');
for (const slug of readdirSync(pieces)) {
  const yaml = readFileSync(join(pieces, slug, 'data.yaml'), 'utf8');
  const name = (yaml.match(/^name:\s*(.+)$/m)?.[1] ?? slug).toUpperCase();
  await slot(join(pieces, slug, '1.png'), 1600, 1600, [name, 'FRONT CUT-OUT · 1:1 · 1600 × 1600']);
  await slot(join(pieces, slug, '2.png'), 1600, 1600, [name, 'BACK OR DETAIL · 1:1 · 1600 × 1600']);
}
