// The visitor's delivery city sets the currency and the delivery promise on
// every page. Prices are rendered in USD on the server; this rewrites them.
import { cities, defaultCity, formatPrice, type City } from '../config/site';

const KEY = 'maison-city';

export function getCity(): City {
  try {
    const id = localStorage.getItem(KEY);
    return cities.find((c) => c.id === id) ?? defaultCity;
  } catch {
    return defaultCity;
  }
}

export function setCity(id: string) {
  try {
    localStorage.setItem(KEY, id);
  } catch {
    /* private mode: the choice lasts for this page only */
  }
  applyCity();
}

export const price = (usd: number) => formatPrice(usd, getCity().currency);

export function applyCity(root: ParentNode = document) {
  const city = getCity();
  root.querySelectorAll<HTMLElement>('[data-usd]').forEach((el) => {
    el.textContent = formatPrice(Number(el.dataset.usd), city.currency);
  });
  root.querySelectorAll<HTMLElement>('[data-city-name]').forEach((el) => (el.textContent = city.name));
  root.querySelectorAll<HTMLElement>('[data-city-currency]').forEach((el) => (el.textContent = city.currency));
  root.querySelectorAll<HTMLElement>('[data-city-days]').forEach((el) => {
    el.textContent = city.days === 1 ? 'tomorrow' : `in ${city.days} days`;
  });
  root.querySelectorAll<HTMLSelectElement>('select[data-city-select]').forEach((s) => (s.value = city.id));
  document.dispatchEvent(new CustomEvent('city:change', { detail: city }));
}

document.addEventListener('change', (e) => {
  const t = e.target as HTMLElement;
  if (t instanceof HTMLSelectElement && t.hasAttribute('data-city-select')) setCity(t.value);
});
