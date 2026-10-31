// Everything about the house that is not a piece lives here.
// SAMPLE: delivery times, exchange rates and the advisor address are stand-ins.

export const site = {
  name: 'Louis Vuitton',
  season: 'Autumn–Winter 2026',
  advisorEmail: 'advisor@example.com',
  disclaimer: 'Design study, not affiliated with or endorsed by Louis Vuitton. Illustrations stand in for photography.',
  returnsDays: 30,
  /** SAMPLE: the season's story, shown on the home page. */
  collection: {
    name: 'New Horizons',
    scribble: 'A/W 2026',
    intro:
      'A collection for the moment of leaving: coats cut to be lived in, bags built like the trunks that started the house, and pieces meant to be packed, unpacked and worn again somewhere new.',
  },
  address: ['00 Rue de l’Exemple', '75001 Paris', 'France'], // SAMPLE
  social: {
    instagram: 'https://instagram.com/',
    youtube: 'https://youtube.com/',
    x: 'https://x.com/',
  },
} as const;

/** Prices are stored in US dollars and converted with these rates for display. */
export const currencies = {
  USD: { rate: 1, step: 50 },
  EUR: { rate: 0.92, step: 50 },
  GBP: { rate: 0.79, step: 50 },
  JPY: { rate: 150, step: 1000 },
  KRW: { rate: 1350, step: 10000 },
  CNY: { rate: 7.2, step: 100 },
  AED: { rate: 3.67, step: 50 },
  AUD: { rate: 1.52, step: 50 },
} as const;

export type Currency = keyof typeof currencies;

export interface City {
  id: string;
  name: string;
  country: string;
  currency: Currency;
  /** Business days from the Paris atelier to the client's door. */
  days: number;
}

export const cities: City[] = [
  { id: 'paris', name: 'Paris', country: 'France', currency: 'EUR', days: 1 },
  { id: 'milan', name: 'Milan', country: 'Italy', currency: 'EUR', days: 2 },
  { id: 'london', name: 'London', country: 'United Kingdom', currency: 'GBP', days: 2 },
  { id: 'new-york', name: 'New York', country: 'United States', currency: 'USD', days: 2 },
  { id: 'los-angeles', name: 'Los Angeles', country: 'United States', currency: 'USD', days: 3 },
  { id: 'santo-domingo', name: 'Santo Domingo', country: 'Dominican Republic', currency: 'USD', days: 4 },
  { id: 'dubai', name: 'Dubai', country: 'United Arab Emirates', currency: 'AED', days: 3 },
  { id: 'tokyo', name: 'Tokyo', country: 'Japan', currency: 'JPY', days: 3 },
  { id: 'seoul', name: 'Seoul', country: 'South Korea', currency: 'KRW', days: 3 },
  { id: 'shanghai', name: 'Shanghai', country: 'China', currency: 'CNY', days: 3 },
  { id: 'sydney', name: 'Sydney', country: 'Australia', currency: 'AUD', days: 4 },
];

export const defaultCity = cities.find((c) => c.id === 'new-york')!;

export const categories = {
  women: 'Women',
  men: 'Men',
  'leather-goods': 'Leather Goods',
  accessories: 'Accessories',
} as const;

export type Category = keyof typeof categories;

/** Resolve a path inside the site, honouring the configured base. */
export function url(path = ''): string {
  return import.meta.env.BASE_URL.replace(/\/$/, '') + '/' + path.replace(/^\//, '');
}

/** Price formatting shared by the server render and the browser. */
export function formatPrice(usd: number, currency: Currency = 'USD'): string {
  const { rate, step } = currencies[currency];
  const value = Math.round((usd * rate) / step) * step;
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(value);
}
