// Turns dist/ into dist-portable/: the same site with every link relative,
// so it works from any folder or host path (no server-side index.html needed).
// Fonts are embedded as data URIs so they load wherever the pages are served.
// Run after `npm run build` with `npm run build:portable`.
import { cpSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = join(root, 'dist');
const out = join(root, 'dist-portable');
rmSync(out, { recursive: true, force: true });
cpSync(src, out, { recursive: true });

const walk = (dir) => readdirSync(dir).flatMap((f) => (statSync(join(dir, f)).isDirectory() ? walk(join(dir, f)) : [join(dir, f)]));

/** A root-relative URL, rewritten for a page `prefix` away from the root. */
function rewrite(u, prefix) {
  if (!u.startsWith('/') || u.startsWith('//')) return u;
  const [, path, rest = ''] = u.match(/^\/([^?#]*)(.*)$/);
  const isPage = path === '' || path.endsWith('/');
  return prefix + path + (isPage ? 'index.html' : '') + rest;
}

const fonts = new Map();
const embed = (name) => {
  if (!fonts.has(name)) fonts.set(name, `data:font/woff2;base64,${readFileSync(join(out, 'assets', name)).toString('base64')}`);
  return fonts.get(name);
};

for (const file of walk(out).filter((f) => f.endsWith('.html'))) {
  const depth = relative(out, dirname(file)).split(sep).filter(Boolean).length;
  const prefix = depth ? '../'.repeat(depth) : './';
  let html = readFileSync(file, 'utf8');
  html = html.replace('<html lang="en"', `<html lang="en" data-base="${prefix}"`);
  html = html.replace(/\b(href|src|action|data-image)="([^"]*)"/g, (_, a, u) => `${a}="${rewrite(u, prefix)}"`);
  html = html.replace(/\bsrcset="([^"]*)"/g, (_, set) => `srcset="${set.split(',').map((part) => part.trim().replace(/^\S+/, (u) => rewrite(u, prefix))).join(', ')}"`);
  html = html.replace(/url\((['"]?)\/assets\/([^)'"]+\.woff2)\1\)/g, (_m, _q, name) => `url(${embed(name)})`);
  html = html.replace(/url\((['"]?)\/assets\//g, `url($1${prefix}assets/`);
  html = html.replace(/(["'])\/assets\//g, `$1${prefix}assets/`);
  writeFileSync(file, html);
}
// The fonts now live inside the pages.
for (const name of fonts.keys()) rmSync(join(out, 'assets', name));
console.log('portable site in', relative(root, out));
