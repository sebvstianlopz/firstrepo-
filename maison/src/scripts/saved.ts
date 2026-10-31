// Saved pieces (the wishlist), kept in localStorage like the bag.
// Every [data-heart] button on the page stays in sync through this module.

const KEY = 'maison-saved';
let memory: string[] = [];

export function readSaved(): string[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]');
  } catch {
    return memory;
  }
}

function write(slugs: string[]) {
  memory = slugs;
  try {
    localStorage.setItem(KEY, JSON.stringify(slugs));
  } catch {
    /* kept in memory */
  }
  document.dispatchEvent(new CustomEvent('saved:change', { detail: slugs }));
}

export const isSaved = (slug: string) => readSaved().includes(slug);
export const savedCount = () => readSaved().length;

export function toggleSaved(slug: string): boolean {
  const slugs = readSaved();
  const on = !slugs.includes(slug);
  write(on ? [...slugs, slug] : slugs.filter((s) => s !== slug));
  return on;
}

const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');

function sync() {
  const slugs = readSaved();
  document.querySelectorAll<HTMLButtonElement>('[data-heart]').forEach((btn) => {
    btn.setAttribute('aria-pressed', String(slugs.includes(btn.dataset.heart!)));
  });
  document.querySelectorAll<HTMLElement>('[data-saved-count]').forEach((el) => {
    el.textContent = String(slugs.length);
    el.hidden = slugs.length === 0;
  });
}

document.addEventListener('click', (e) => {
  const btn = (e.target as HTMLElement).closest<HTMLButtonElement>('[data-heart]');
  if (!btn) return;
  e.preventDefault();
  const on = toggleSaved(btn.dataset.heart!);
  // A small pop when saving confirms the tap; un-saving stays quiet.
  if (on && !reduceMotion.matches) {
    btn.querySelector('svg')?.animate(
      [{ transform: 'scale(1)' }, { transform: 'scale(1.28)' }, { transform: 'scale(1)' }],
      { duration: 320, easing: 'cubic-bezier(0.23, 1, 0.32, 1)' },
    );
  }
});

document.addEventListener('saved:change', sync);
addEventListener('storage', sync);
sync();
