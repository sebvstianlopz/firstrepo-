// Turns a product photo on a light, plain background into a rail cut-out:
// the background is removed (flood fill from the edges), the garment is cropped,
// scaled to a fixed width and placed at the top of the rail's 200 × 310 canvas,
// so a piece's front, back and side all line up as it turns.
//
//   npm run rail-photo -- <piece-slug> <front|back|side> <photo>
//
// Writes src/assets/rail/<piece-slug>/<face>.png, which the home page rail picks up.
import sharp from 'sharp';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const [slug, face, input] = process.argv.slice(2);
if (!slug || !['front', 'back', 'side'].includes(face) || !input) {
  console.error('Usage: npm run rail-photo -- <piece-slug> <front|back|side> <photo>');
  process.exit(1);
}

const CANVAS_W = 1000;
const CANVAS_H = 1550; // 200 × 310
const GARMENT_W = face === 'side' ? 300 : 880;
const TOP = 24;

const { data, info } = await sharp(input).removeAlpha().raw().toBuffer({ resolveWithObject: true });
const { width: w, height: h } = info;

// Background: light and nearly colourless, reached from the edges without crossing the garment.
const isBg = (i) => {
  const r = data[i * 3], g = data[i * 3 + 1], b = data[i * 3 + 2];
  return Math.min(r, g, b) >= 178 && Math.max(r, g, b) - Math.min(r, g, b) <= 20;
};
const bg = new Uint8Array(w * h);

/** Flood from the seeds through pixels that pass `test`; returns the pixels reached. */
function flood(seeds, test, mark) {
  const stack = [...seeds];
  const reached = [];
  while (stack.length) {
    const i = stack.pop();
    if (mark[i] || !test(i)) continue;
    mark[i] = 1;
    reached.push(i);
    const x = i % w;
    if (x > 0) stack.push(i - 1);
    if (x < w - 1) stack.push(i + 1);
    if (i >= w) stack.push(i - w);
    if (i < w * (h - 1)) stack.push(i + w);
  }
  return reached;
}

const edges = [];
for (let x = 0; x < w; x++) edges.push(x, (h - 1) * w + x);
for (let y = 0; y < h; y++) edges.push(y * w, y * w + w - 1);
flood(edges, isBg, bg);

// Background caught between a sleeve and the body never touches the edge. Clear any large
// patch that is near-white and colourless; fabric highlights and woven checks are smaller or tinted.
const isBlank = (i) => {
  const r = data[i * 3], g = data[i * 3 + 1], b = data[i * 3 + 2];
  return Math.min(r, g, b) >= 232 && Math.max(r, g, b) - Math.min(r, g, b) <= 10;
};
const seen = new Uint8Array(w * h);
for (let i = 0; i < w * h; i++) {
  if (bg[i] || seen[i] || !isBlank(i)) continue;
  const patch = flood([i], (j) => !bg[j] && isBlank(j), seen);
  if (patch.length > w * h * 0.002) for (const j of patch) bg[j] = 1;
}

// Alpha with a slightly softened edge, and the garment's bounding box.
const alpha = Buffer.alloc(w * h);
let [x0, y0, x1, y1] = [w, h, 0, 0];
for (let i = 0; i < w * h; i++) {
  if (bg[i]) continue;
  alpha[i] = 255;
  const x = i % w, y = (i - x) / w;
  if (x < x0) x0 = x;
  if (x > x1) x1 = x;
  if (y < y0) y0 = y;
  if (y > y1) y1 = y;
}
const soft = await sharp(alpha, { raw: { width: w, height: h, channels: 1 } }).blur(0.8).extractChannel(0).raw().toBuffer();

// Attach the mask first: sharp crops and resizes before it joins channels within one pipeline.
const rgba = await sharp(data, { raw: { width: w, height: h, channels: 3 } })
  .joinChannel(soft, { raw: { width: w, height: h, channels: 1 } })
  .png()
  .toBuffer();
const cut = await sharp(rgba)
  .extract({ left: x0, top: y0, width: x1 - x0 + 1, height: y1 - y0 + 1 })
  .resize({ width: GARMENT_W })
  .png()
  .toBuffer({ resolveWithObject: true });

if (TOP + cut.info.height > CANVAS_H) {
  console.error(`The garment is too tall for the canvas once scaled (${cut.info.height}px). Crop the photo closer.`);
  process.exit(1);
}

const out = join(dirname(fileURLToPath(import.meta.url)), '..', 'src/assets/rail', slug, `${face}.png`);
mkdirSync(dirname(out), { recursive: true });
await sharp({ create: { width: CANVAS_W, height: CANVAS_H, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
  .composite([{ input: cut.data, left: Math.round((CANVAS_W - GARMENT_W) / 2), top: TOP }])
  .png({ compressionLevel: 9 })
  .toFile(out);
console.log('wrote', out.replace(/^.*\/maison\//, ''));
