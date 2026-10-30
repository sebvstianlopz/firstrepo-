// Parts of each [data-reveal] block rise in turn the first time it enters view.

const io = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('is-in');
      io.unobserve(entry.target);
    }
  },
  { rootMargin: '0px 0px -12% 0px' },
);

document.querySelectorAll<HTMLElement>('[data-reveal]').forEach((block) => {
  [...block.children].forEach((child, i) => (child as HTMLElement).style.setProperty('--i', String(i)));
  io.observe(block);
});
