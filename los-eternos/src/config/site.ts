// Everything about the business that is not a vehicle lives here.
// SAMPLE: replace the locations and links with the real ones.

export type Lang = 'es' | 'en';

export interface Location {
  id: string;
  city: string;
  label: Record<Lang, string>;
}

export const site = {
  name: 'Los Eternos',
  // WhatsApp number in international format, digits only (1 + area code + number).
  whatsapp: '18094240374',
  phoneDisplay: '+1 (809) 424-0374',
  currency: 'USD',
  address: 'Santo Domingo, República Dominicana',
  mapsUrl: 'https://maps.google.com/?q=Santo+Domingo,+Rep%C3%BAblica+Dominicana',
  hours: {
    es: 'Todos los días, de 7:00 a. m. a 10:00 p. m.',
    en: 'Every day, 7:00 am to 10:00 pm',
  },
  social: {
    instagram: 'https://instagram.com/',
  },
  locations: [
    { id: 'sdq', city: 'Santo Domingo', label: { es: 'Aeropuerto Las Américas (SDQ)', en: 'Las Américas Airport (SDQ)' } },
    { id: 'sdo', city: 'Santo Domingo', label: { es: 'Nuestra oficina en Santo Domingo', en: 'Our Santo Domingo office' } },
    { id: 'puj', city: 'Punta Cana', label: { es: 'Aeropuerto de Punta Cana (PUJ)', en: 'Punta Cana Airport (PUJ)' } },
    { id: 'pcj', city: 'Punta Cana', label: { es: 'Tu hotel en Punta Cana', en: 'Your hotel in Punta Cana' } },
    { id: 'sti', city: 'Santiago', label: { es: 'Aeropuerto del Cibao (STI)', en: 'Cibao Airport (STI)' } },
  ] satisfies Location[],
} as const;

export const cities = [...new Set(site.locations.map((l) => l.city))];
