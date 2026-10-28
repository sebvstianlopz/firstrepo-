import { getCollection, type CollectionEntry } from 'astro:content';
import { t } from '../i18n';
import type { Lang } from '../config/site';

export type Vehicle = CollectionEntry<'vehicles'>;
export type Category = Vehicle['data']['category'];

export async function getVehicles(): Promise<Vehicle[]> {
  const all = await getCollection('vehicles');
  return all.sort((a, b) => a.data.order - b.data.order || a.id.localeCompare(b.id));
}

const model = (v: Vehicle, lang: Lang) => (typeof v.data.model === 'string' ? v.data.model : v.data.model[lang]);

/** Brand and model separately, so the brand can be kept on one line. */
export const nameParts = (v: Vehicle, lang: Lang) => ({ brand: v.data.brand, model: model(v, lang) });

/** "Toyota Highlander" — the name shown as a title. */
export const vehicleName = (v: Vehicle, lang: Lang) => [v.data.brand, model(v, lang)].filter(Boolean).join(' ');

/** "Toyota Highlander blanco" / "white Toyota Highlander" — unambiguous, for alt text and WhatsApp messages. */
export function vehicleFullName(v: Vehicle, lang: Lang) {
  const color = t(lang).color[v.data.color];
  const parts = lang === 'es' ? [vehicleName(v, lang), color] : [color, vehicleName(v, lang)];
  return [...parts, v.data.year].filter(Boolean).join(' ');
}

export const forRent = (v: Vehicle) => v.data.mode !== 'sale';
export const forSale = (v: Vehicle) => v.data.mode !== 'rent';

export const colorHex: Record<Vehicle['data']['color'], string> = {
  blanco: '#f4f5f3',
  negro: '#1b1f21',
  gris: '#6c7376',
  plata: '#b9bfc1',
  rojo: '#8c2020',
  azul: '#2b4c7e',
  'azul-oscuro': '#1d2c47',
  lima: '#b7d133',
};

/** Categories in display order, each with its vehicle count, lowest day price and a cover vehicle. */
export function categorySummary(all: Vehicle[]) {
  const order: Category[] = ['compacto', 'suv', 'todoterreno', 'lujo', 'pickup', 'van', 'sedan'];
  return order
    .map((category) => {
      const list = all.filter((v) => v.data.category === category && v.data.available);
      const prices = list.map((v) => v.data.priceDay).filter((p): p is number => !!p);
      const cover = list.find((v) => !v.data.photoPending) ?? list[0];
      return { category, count: list.length, from: prices.length ? Math.min(...prices) : undefined, cover };
    })
    .filter((c) => c.count > 0);
}

/** Vehicles to suggest at the bottom of a vehicle page: same category, then closest price. */
export function related(current: Vehicle, all: Vehicle[], n = 3): Vehicle[] {
  const price = current.data.priceDay ?? current.data.priceSale ?? 0;
  const score = (v: Vehicle) =>
    (v.data.category === current.data.category ? 1000 : 0) +
    (v.data.photoPending ? 0 : 100) -
    Math.min(99, Math.abs((v.data.priceDay ?? v.data.priceSale ?? 0) - price) / 5);
  return all
    .filter((v) => v.id !== current.id && v.data.available)
    .sort((a, b) => score(b) - score(a) || a.data.order - b.data.order)
    .slice(0, n);
}
