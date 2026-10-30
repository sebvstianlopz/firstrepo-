// Cursor details, only on devices that hover and under html.motion:
//   [data-spot]   gets --mx/--my (cursor position inside it) for a following spotlight.
//   [data-magnet] leans up to 6px toward the cursor (--tx/--ty), and back on leave.
//   [data-lean]   gets --lx/--ly (-1 → 1) so its photo can lean the other way.

if (document.documentElement.classList.contains('motion') && matchMedia('(hover: hover)').matches) {
  const local = (el: HTMLElement, e: PointerEvent) => {
    const r = el.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top, w: r.width, h: r.height };
  };

  document.querySelectorAll<HTMLElement>('[data-spot]').forEach((el) => {
    el.addEventListener('pointermove', (e) => {
      const { x, y } = local(el, e);
      el.style.setProperty('--mx', `${x}px`);
      el.style.setProperty('--my', `${y}px`);
    });
    el.addEventListener('pointerleave', () => {
      el.style.removeProperty('--mx');
      el.style.removeProperty('--my');
    });
  });

  document.querySelectorAll<HTMLElement>('[data-magnet]').forEach((el) => {
    el.addEventListener('pointermove', (e) => {
      const { x, y, w, h } = local(el, e);
      el.style.setProperty('--tx', `${((x / w - 0.5) * 12).toFixed(1)}px`);
      el.style.setProperty('--ty', `${((y / h - 0.5) * 10).toFixed(1)}px`);
    });
    el.addEventListener('pointerleave', () => {
      el.style.removeProperty('--tx');
      el.style.removeProperty('--ty');
    });
  });

  document.querySelectorAll<HTMLElement>('[data-lean]').forEach((el) => {
    el.addEventListener('pointermove', (e) => {
      const { x, y, w, h } = local(el, e);
      el.style.setProperty('--lx', ((x / w) * 2 - 1).toFixed(3));
      el.style.setProperty('--ly', ((y / h) * 2 - 1).toFixed(3));
    });
    el.addEventListener('pointerleave', () => {
      el.style.removeProperty('--lx');
      el.style.removeProperty('--ly');
    });
  });
}
