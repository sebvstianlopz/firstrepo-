// Odometer: digits roll up into place like a car's mileage counter.
// roll(el, text) shows `text` in el, rolling every digit from its previous value (or 0).
// Screen readers always get the plain text; the rolling copy is hidden from them.
// [data-odo] elements roll once when they scroll into view.
// Without html.motion (reduced motion) the text is simply set.

const motion = () => document.documentElement.classList.contains('motion');

export function roll(el: HTMLElement, text: string) {
  if (!motion()) {
    el.textContent = text;
    return;
  }
  // Previous digit values, read right to left so numbers of different length line up.
  const prev = [...el.querySelectorAll<HTMLElement>('.odo-d')].map((d) => Number(d.dataset.v)).reverse();
  const plain = document.createElement('span');
  plain.className = 'visually-hidden';
  plain.textContent = text;
  const shown = document.createElement('span');
  shown.className = 'odo';
  shown.setAttribute('aria-hidden', 'true');

  const chars = [...text];
  let fromRight = chars.filter((c) => /\d/.test(c)).length;
  chars.forEach((c) => {
    if (!/\d/.test(c)) {
      const s = document.createElement('span');
      s.textContent = c;
      shown.append(s);
      return;
    }
    fromRight--;
    const digit = document.createElement('span');
    digit.className = 'odo-d';
    digit.dataset.v = c;
    digit.style.setProperty('--d', String(prev[fromRight] ?? 0));
    digit.style.setProperty('--k', String(fromRight)); // the ones roll last, like a real counter
    const strip = document.createElement('span');
    strip.className = 'odo-strip';
    strip.textContent = '0123456789';
    digit.append(strip);
    shown.append(digit);
  });
  el.replaceChildren(plain, shown);
  // Next frame: roll each digit to its value.
  requestAnimationFrame(() =>
    requestAnimationFrame(() => shown.querySelectorAll<HTMLElement>('.odo-d').forEach((d) => d.style.setProperty('--d', d.dataset.v!))),
  );
}

if (motion()) {
  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const el = entry.target as HTMLElement;
        io.unobserve(el);
        roll(el, (el.textContent ?? '').replace(/\s+/g, ' ').trim());
      }
    },
    { threshold: 0.6 },
  );
  document.querySelectorAll('[data-odo]').forEach((el) => io.observe(el));
}
