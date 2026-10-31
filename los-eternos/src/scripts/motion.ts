// Shared scroll motion for the whole site. Two jobs:
//   1. [data-reveal] elements get .is-in once, when they scroll into view.
//   2. [data-progress] elements get a --p custom property (0 → 1) tied to scroll, plus a
//      "scrollprogress" event so components can react (switch lights on, move a spotlight…).
//      data-progress="pin": progress while a tall section scrolls past its sticky stage.
//      data-progress="view": progress as the element's top travels from data-from to
//      data-to (fractions of the viewport height; defaults 0.9 → 0.3).
// It also writes --page-p on <html> for the header's progress line.
// Only runs under html.motion (no reduced motion); otherwise everything stays static.

import './odometer';
import './pointer';
import './cursor';

const root = document.documentElement;
const clamp = (n: number) => Math.min(1, Math.max(0, n));

if (root.classList.contains('motion')) {
  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      }
    },
    { rootMargin: '0px 0px -10% 0px', threshold: 0.12 },
  );
  document.querySelectorAll('[data-reveal]').forEach((el) => io.observe(el));

  const tracks = [...document.querySelectorAll<HTMLElement>('[data-progress]')];
  const last = new Map<HTMLElement, number>();
  let queued = false;

  const update = () => {
    queued = false;
    const vh = innerHeight;
    for (const el of tracks) {
      const r = el.getBoundingClientRect();
      let p: number;
      if (el.dataset.progress === 'pin') {
        p = -r.top / Math.max(1, r.height - vh);
      } else {
        const from = Number(el.dataset.from ?? 0.9);
        const to = Number(el.dataset.to ?? 0.3);
        p = (vh * from - r.top) / (vh * (from - to));
      }
      p = Math.round(clamp(p) * 10000) / 10000;
      if (last.get(el) === p) continue;
      last.set(el, p);
      el.style.setProperty('--p', String(p));
      el.dispatchEvent(new CustomEvent('scrollprogress', { detail: p }));
    }
    const max = Math.max(1, root.scrollHeight - vh);
    root.style.setProperty('--page-p', String(Math.round(clamp(scrollY / max) * 10000) / 10000));
  };

  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(update);
  };
  addEventListener('scroll', schedule, { passive: true });
  addEventListener('resize', schedule);
  // Components that change layout (e.g. pinning) ask for a fresh measurement.
  addEventListener('motion:refresh', schedule);
  schedule();
}
