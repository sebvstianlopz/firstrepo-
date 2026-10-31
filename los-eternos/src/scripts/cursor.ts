// Custom cursor: a thin red ring with a glowing center, for mouse and trackpad users only
// (no touch, no reduced motion). The dot tracks the pointer exactly; the ring trails it a
// touch and opens up over anything clickable, turning warm white over red buttons so it
// stays visible. Text fields keep the native cursor so typing feels normal.

const root = document.documentElement;

if (root.classList.contains('motion') && matchMedia('(hover: hover) and (pointer: fine)').matches) {
  const CLICKABLE = 'a[href], button, summary, label, select, [role="button"]';
  const NATIVE = 'input:not([type="radio"]):not([type="checkbox"]), textarea, [contenteditable]';
  const ON_RED = '.btn-primary';

  const el = document.createElement('div');
  el.className = 'cursor';
  el.setAttribute('aria-hidden', 'true');
  el.innerHTML = '<span class="cursor-ring"></span><span class="cursor-dot"></span>';
  document.body.append(el);
  const ring = el.firstElementChild as HTMLElement;
  const dot = el.lastElementChild as HTMLElement;

  let x = 0;
  let y = 0;
  let rx = 0;
  let ry = 0;
  let raf = 0;
  // `translate` rather than `transform`, so the hover `scale` in CSS doesn't scale the position too.
  const place = (node: HTMLElement, px: number, py: number) => {
    node.style.translate = `${px}px ${py}px`;
  };
  const show = (px: number, py: number) => {
    x = rx = px;
    y = ry = py;
    place(dot, x, y);
    place(ring, rx, ry);
    el.classList.add('is-on');
    root.classList.add('has-cursor');
  };
  // The ring eases toward the pointer and stops ticking once it has caught up.
  const tick = () => {
    rx += (x - rx) * 0.25;
    ry += (y - ry) * 0.25;
    place(ring, rx, ry);
    raf = Math.abs(x - rx) + Math.abs(y - ry) > 0.2 ? requestAnimationFrame(tick) : 0;
  };

  // Carry the position across page changes, so the cursor is there before the first move.
  try {
    const saved = JSON.parse(sessionStorage.getItem('le:cursor') ?? 'null');
    if (saved) show(saved[0], saved[1]);
  } catch {}
  addEventListener('pagehide', () => {
    try {
      if (el.classList.contains('is-on')) sessionStorage.setItem('le:cursor', JSON.stringify([x, y]));
    } catch {}
  });

  addEventListener(
    'pointermove',
    (e) => {
      if (e.pointerType !== 'mouse') return;
      if (!el.classList.contains('is-on')) show(e.clientX, e.clientY);
      x = e.clientX;
      y = e.clientY;
      place(dot, x, y);
      const target = e.target instanceof Element ? e.target : null;
      const hit = target?.closest(CLICKABLE);
      el.classList.toggle('is-native', !!target?.closest(NATIVE));
      el.classList.toggle('is-hover', !!hit);
      el.classList.toggle('is-light', !!hit?.closest(ON_RED));
      if (!raf) raf = requestAnimationFrame(tick);
    },
    { passive: true },
  );
  addEventListener('pointerdown', () => el.classList.add('is-down'));
  addEventListener('pointerup', () => el.classList.remove('is-down'));
  // Leaving the window hides it; the next move brings it back.
  root.addEventListener('mouseleave', () => {
    el.classList.remove('is-on');
    try {
      sessionStorage.removeItem('le:cursor');
    } catch {}
  });
}
