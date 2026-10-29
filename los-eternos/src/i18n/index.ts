import type { Lang } from '../config/site';

const routes = {
  home: { es: '', en: 'en/' },
  catalog: { es: 'catalogo/', en: 'en/catalog/' },
  services: { es: 'servicios/', en: 'en/services/' },
  about: { es: 'nosotros/', en: 'en/about/' },
} as const;

export type RouteKey = keyof typeof routes;

const base = import.meta.env.BASE_URL.replace(/\/?$/, '/');

/** Internal URL for a page, with the deploy base path and a trailing slash. */
export function path(lang: Lang, key: RouteKey, slug?: string): string {
  return base + routes[key][lang] + (slug ? `${slug}/` : '');
}

export const asset = (p: string) => base + p.replace(/^\//, '');

const es = {
  langName: 'Español',
  switchTo: 'English',
  skip: 'Saltar al contenido',
  nav: { catalog: 'Catálogo', services: 'Servicios', about: 'Nosotros', book: 'Reservar' },
  mode: { rent: 'Alquiler', sale: 'Venta', all: 'Todos' },
  category: { compacto: 'SUV compacto', suv: 'SUV familiar', lujo: 'Lujo', todoterreno: 'Todoterreno', pickup: 'Camioneta', sedan: 'Sedán', van: 'Van' },
  categoryArticle: { compacto: 'un SUV compacto', suv: 'un SUV familiar', lujo: 'un vehículo de lujo', todoterreno: 'un todoterreno', pickup: 'una camioneta', sedan: 'un sedán', van: 'una van', any: 'un vehículo' },
  color: { blanco: 'blanco', negro: 'negro', gris: 'gris', plata: 'plateado', rojo: 'rojo', azul: 'azul', 'azul-oscuro': 'azul oscuro', lima: 'verde lima' },
  transmission: { automatica: 'Automática', manual: 'Manual' },
  fuel: { gasolina: 'Gasolina', diesel: 'Diésel', hibrido: 'Híbrido', electrico: 'Eléctrico' },
  seats: (n: number) => `${n} asientos`,
  perDay: '/día',
  from: 'Desde',
  hero: {
    title: ['La isla', 'es tuya'],
    sub: 'Más de 50 vehículos listos en República Dominicana. Elige el tuyo, escríbenos por WhatsApp y te lo entregamos donde llegues.',
    categoryLabel: 'Tipo',
    cityLabel: 'Ciudad',
    cta: 'Ver vehículos',
    scroll: 'Desliza',
    cue: 'Desliza para descubrir',
  },
  browse: {
    title: 'Encuentra el tuyo',
    text: 'Desde un SUV compacto para la ciudad hasta un todoterreno para la montaña.',
    count: (n: number) => (n === 1 ? '1 vehículo' : `${n} vehículos`),
  },
  featured: { title: 'Destacados', all: 'Ver todo el catálogo' },
  steps: {
    title: 'Reservar toma tres pasos',
    items: [
      { t: 'Elige tu vehículo', d: 'Explora el catálogo y abre el que te guste para ver fotos, detalles y precio.' },
      { t: 'Escríbenos por WhatsApp', d: 'El mensaje se arma solo con el vehículo y tus fechas. Te confirmamos disponibilidad en minutos.' },
      { t: 'Recíbelo listo', d: 'Limpio, con tanque lleno y en el lugar que elegiste. Sin filas ni mostradores.' },
    ],
  },
  trust: {
    title: 'Lo que puedes esperar de nosotros',
    items: [
      { icon: 'shield', t: 'Seguro incluido', d: 'Todos los alquileres incluyen seguro básico. Te explicamos la cobertura antes de firmar.' },
      { icon: 'tag', t: 'El precio que ves', d: 'Te damos el total antes de reservar. Sin cargos que aparecen al final.' },
      { icon: 'pin', t: 'Entrega donde estés', d: 'Aeropuertos de Santo Domingo, Punta Cana y Santiago, o directo a tu hotel.' },
      { icon: 'chat', t: 'Una persona real', d: 'Te atiende nuestro equipo por WhatsApp, antes, durante y después de tu viaje.' },
    ],
  },
  faq: {
    title: 'Preguntas frecuentes',
    items: [
      { q: '¿Qué necesito para alquilar?', a: 'Licencia de conducir vigente, pasaporte o cédula, y una tarjeta de crédito para el depósito. La edad mínima es 21 años.' },
      { q: '¿Pueden entregarme el vehículo en el aeropuerto?', a: 'Sí. Te esperamos en SDQ, PUJ o STI con el vehículo listo, y también lo entregamos en hoteles.' },
      { q: '¿Cómo pago?', a: 'Aceptamos tarjeta, transferencia y efectivo en dólares o pesos dominicanos. Te enviamos los detalles por WhatsApp.' },
      { q: '¿Puedo alquilar por semanas o meses?', a: 'Sí. Escríbenos por WhatsApp con tus fechas y te enviamos el precio para estadías largas.' },
    ],
  },
  closing: { title: '¿Ya tienes fecha?', text: 'Cuéntanos cuándo y dónde. Te respondemos en minutos con disponibilidad y precio final.' },
  wa: { book: 'Reservar por WhatsApp', visit: 'Agendar visita por WhatsApp', write: 'Escríbenos por WhatsApp' },
  catalog: {
    title: 'Catálogo',
    intro: 'Todos nuestros vehículos, con precio claro. Abre uno para reservarlo por WhatsApp.',
    count: (n: number) => (n === 1 ? '1 vehículo' : `${n} vehículos`),
    filters: 'Filtros',
    categoryAll: 'Todos los tipos',
    seatsAny: 'Cualquier capacidad',
    seatsMin: (n: number) => `${n} o más asientos`,
    transAny: 'Cualquier transmisión',
    sort: 'Ordenar',
    sortOptions: { recommended: 'Recomendados', priceAsc: 'Precio: menor a mayor', priceDesc: 'Precio: mayor a menor', newest: 'Más nuevos' },
    clear: 'Quitar filtros',
    emptyTitle: 'Ningún vehículo coincide con estos filtros',
    emptyText: 'Quita algún filtro, o escríbenos y te ayudamos a encontrar el que buscas.',
  },
  vehicle: {
    back: 'Catálogo',
    specs: 'Detalles',
    highlights: 'Lo que lo hace especial',
    year: 'Año',
    more: 'También te puede interesar',
    photo: (i: number, n: number) => `Foto ${i} de ${n}`,
    photoPending: 'Foto real próximamente. Pídela por WhatsApp y te la enviamos.',
    color: 'Color',
    category: 'Tipo',
    seatsLabel: 'Asientos',
    unavailable: 'Este vehículo no está disponible ahora. Escríbenos y te sugerimos uno parecido.',
  },
  booking: {
    rentTab: 'Alquilar',
    saleTab: 'Comprar',
    pickup: 'Recogida',
    return: 'Devolución',
    where: 'Lugar de entrega',
    days: (n: number) => (n === 1 ? '1 día' : `${n} días`),
    estimate: 'Precio estimado. Te confirmamos el total por WhatsApp.',
    pickDates: 'Elige tus fechas para ver el total.',
    visitDate: '¿Qué día quieres verlo?',
    visitHint: 'Opcional. Te confirmamos la hora por WhatsApp.',
    salePrice: 'Precio de venta',
  },
  services: {
    title: 'Servicios',
    intro: 'Todo lo que hacemos para que tu único trabajo sea disfrutar el camino.',
    items: [
      { t: 'Alquiler por días, semanas o meses', d: 'Tarifas más bajas mientras más tiempo lo uses. Pregúntanos por alquileres mensuales.' },
      { t: 'Entrega en aeropuerto y hotel', d: 'Te esperamos al salir del vuelo en SDQ, PUJ o STI, o lo llevamos a tu hotel.' },
      { t: 'Asistencia en carretera', d: 'Si algo pasa en el camino, nos escribes y lo resolvemos.' },
    ],
    reqTitle: 'Requisitos para alquilar',
    req: ['Licencia de conducir vigente (local o internacional)', 'Pasaporte o cédula', 'Tarjeta de crédito para el depósito', 'Edad mínima: 21 años'],
  },
  about: {
    title: 'Nosotros',
    lead: 'Somos Los Eternos, una empresa dominicana de alquiler de vehículos.',
    body: 'Creemos que un viaje empieza a salir bien desde el primer mensaje. Por eso respondemos rápido, entregamos a tiempo y te decimos el precio completo desde el principio.',
    contact: 'Contacto',
    hours: 'Horario',
    whereTitle: 'Dónde estamos',
    openMap: 'Abrir en Google Maps',
  },
  notFound: { title: 'Esta página no existe', text: 'Puede que el enlace haya cambiado. Vuelve al catálogo para seguir explorando.', cta: 'Ir al catálogo' },
  footer: { tagline: 'Alquiler de vehículos en República Dominicana.', rights: 'Todos los derechos reservados.' },
  meta: {
    homeTitle: 'Los Eternos | Alquiler de vehículos en República Dominicana',
    homeDesc: 'Alquila tu vehículo en República Dominicana: más de 50 SUV, todoterrenos y vehículos de lujo. Entrega en aeropuertos y hoteles. Reserva en minutos por WhatsApp.',
    catalogDesc: 'Explora todos los vehículos de Los Eternos con su precio por día. Reserva por WhatsApp.',
    servicesDesc: 'Alquiler por días, semanas o meses, entrega en aeropuerto y hotel, y asistencia en carretera.',
    aboutDesc: 'Conoce a Los Eternos, alquiler de vehículos en República Dominicana.',
  },
};

export type Dict = typeof es;

const en: Dict = {
  langName: 'English',
  switchTo: 'Español',
  skip: 'Skip to content',
  nav: { catalog: 'Catalog', services: 'Services', about: 'About', book: 'Book' },
  mode: { rent: 'For rent', sale: 'For sale', all: 'All' },
  category: { compacto: 'Compact SUV', suv: 'Family SUV', lujo: 'Luxury', todoterreno: 'Off-road', pickup: 'Pickup', sedan: 'Sedan', van: 'Van' },
  categoryArticle: { compacto: 'a compact SUV', suv: 'a family SUV', lujo: 'a luxury car', todoterreno: 'an off-roader', pickup: 'a pickup', sedan: 'a sedan', van: 'a van', any: 'a car' },
  color: { blanco: 'white', negro: 'black', gris: 'gray', plata: 'silver', rojo: 'red', azul: 'blue', 'azul-oscuro': 'dark blue', lima: 'lime green' },
  transmission: { automatica: 'Automatic', manual: 'Manual' },
  fuel: { gasolina: 'Gasoline', diesel: 'Diesel', hibrido: 'Hybrid', electrico: 'Electric' },
  seats: (n: number) => `${n} seats`,
  perDay: '/day',
  from: 'From',
  hero: {
    title: ['The island', 'is yours'],
    sub: 'More than 50 vehicles ready in the Dominican Republic. Pick yours, message us on WhatsApp and we’ll deliver it wherever you land.',
    categoryLabel: 'Type',
    cityLabel: 'City',
    cta: 'See vehicles',
    scroll: 'Scroll',
    cue: 'Scroll to discover',
  },
  browse: {
    title: 'Find yours',
    text: 'From a compact SUV for the city to an off-roader for the mountains.',
    count: (n: number) => (n === 1 ? '1 vehicle' : `${n} vehicles`),
  },
  featured: { title: 'Highlights', all: 'See the full catalog' },
  steps: {
    title: 'Booking takes three steps',
    items: [
      { t: 'Pick your vehicle', d: 'Browse the catalog and open any vehicle to see photos, details and price.' },
      { t: 'Message us on WhatsApp', d: 'The message writes itself with the vehicle and your dates. We confirm availability within minutes.' },
      { t: 'Get it ready to go', d: 'Clean, full tank, at the place you chose. No lines, no counters.' },
    ],
  },
  trust: {
    title: 'What you can expect from us',
    items: [
      { icon: 'shield', t: 'Insurance included', d: 'Every rental includes basic insurance. We explain the coverage before you sign.' },
      { icon: 'tag', t: 'The price you see', d: 'You get the total before you book. No charges showing up at the end.' },
      { icon: 'pin', t: 'Delivered where you are', d: 'Santo Domingo, Punta Cana and Santiago airports, or straight to your hotel.' },
      { icon: 'chat', t: 'A real person', d: 'Our team helps you on WhatsApp before, during and after your trip.' },
    ],
  },
  faq: {
    title: 'Frequently asked questions',
    items: [
      { q: 'What do I need to rent?', a: 'A valid driver’s license, passport or national ID, and a credit card for the deposit. Minimum age is 21.' },
      { q: 'Can you deliver the vehicle at the airport?', a: 'Yes. We meet you at SDQ, PUJ or STI with the vehicle ready, and we also deliver to hotels.' },
      { q: 'How do I pay?', a: 'We accept card, bank transfer and cash in US dollars or Dominican pesos. We send the details on WhatsApp.' },
      { q: 'Can I rent by the week or month?', a: 'Yes. Message us on WhatsApp with your dates and we’ll send you the price for longer stays.' },
    ],
  },
  closing: { title: 'Already have a date?', text: 'Tell us when and where. We reply within minutes with availability and the final price.' },
  wa: { book: 'Book on WhatsApp', visit: 'Schedule a viewing on WhatsApp', write: 'Message us on WhatsApp' },
  catalog: {
    title: 'Catalog',
    intro: 'All our vehicles, with clear prices. Open one to book it on WhatsApp.',
    count: (n: number) => (n === 1 ? '1 vehicle' : `${n} vehicles`),
    filters: 'Filters',
    categoryAll: 'All types',
    seatsAny: 'Any capacity',
    seatsMin: (n: number) => `${n}+ seats`,
    transAny: 'Any transmission',
    sort: 'Sort',
    sortOptions: { recommended: 'Recommended', priceAsc: 'Price: low to high', priceDesc: 'Price: high to low', newest: 'Newest' },
    clear: 'Clear filters',
    emptyTitle: 'No vehicles match these filters',
    emptyText: 'Remove a filter, or message us and we’ll help you find what you’re looking for.',
  },
  vehicle: {
    back: 'Catalog',
    specs: 'Details',
    highlights: 'What makes it special',
    year: 'Year',
    more: 'You might also like',
    photo: (i: number, n: number) => `Photo ${i} of ${n}`,
    photoPending: 'Real photo coming soon. Ask on WhatsApp and we’ll send it.',
    color: 'Color',
    category: 'Type',
    seatsLabel: 'Seats',
    unavailable: 'This vehicle isn’t available right now. Message us and we’ll suggest a similar one.',
  },
  booking: {
    rentTab: 'Rent',
    saleTab: 'Buy',
    pickup: 'Pick-up',
    return: 'Return',
    where: 'Delivery point',
    days: (n: number) => (n === 1 ? '1 day' : `${n} days`),
    estimate: 'Estimated price. We confirm the total on WhatsApp.',
    pickDates: 'Choose your dates to see the total.',
    visitDate: 'Which day would you like to see it?',
    visitHint: 'Optional. We confirm the time on WhatsApp.',
    salePrice: 'Sale price',
  },
  services: {
    title: 'Services',
    intro: 'Everything we do so your only job is enjoying the road.',
    items: [
      { t: 'Daily, weekly or monthly rentals', d: 'Lower rates the longer you keep it. Ask us about monthly rentals.' },
      { t: 'Airport and hotel delivery', d: 'We meet you off your flight at SDQ, PUJ or STI, or bring it to your hotel.' },
      { t: 'Roadside assistance', d: 'If something happens on the road, message us and we’ll sort it out.' },
    ],
    reqTitle: 'Rental requirements',
    req: ['Valid driver’s license (local or international)', 'Passport or national ID', 'Credit card for the deposit', 'Minimum age: 21'],
  },
  about: {
    title: 'About us',
    lead: 'We are Los Eternos, a Dominican car rental company.',
    body: 'We believe a trip starts going well from the first message. That’s why we reply fast, deliver on time and tell you the full price from the start.',
    contact: 'Contact',
    hours: 'Hours',
    whereTitle: 'Where we are',
    openMap: 'Open in Google Maps',
  },
  notFound: { title: 'This page doesn’t exist', text: 'The link may have changed. Head back to the catalog to keep exploring.', cta: 'Go to the catalog' },
  footer: { tagline: 'Car rentals in the Dominican Republic.', rights: 'All rights reserved.' },
  meta: {
    homeTitle: 'Los Eternos | Car rentals in the Dominican Republic',
    homeDesc: 'Rent your vehicle in the Dominican Republic: 50+ SUVs, off-roaders and luxury cars. Airport and hotel delivery. Book in minutes on WhatsApp.',
    catalogDesc: 'Browse every Los Eternos vehicle with its daily price. Book on WhatsApp.',
    servicesDesc: 'Daily, weekly or monthly rentals, airport and hotel delivery, and roadside assistance.',
    aboutDesc: 'Meet Los Eternos, car rentals in the Dominican Republic.',
  },
};

export const dict: Record<Lang, Dict> = { es, en };
export const t = (lang: Lang) => dict[lang];

export function formatPrice(amount: number, lang: Lang, currency = 'USD'): string {
  const n = new Intl.NumberFormat(lang === 'es' ? 'es-DO' : 'en-US', { maximumFractionDigits: 0 }).format(amount);
  return currency === 'USD' ? `US$ ${n}` : `RD$ ${n}`;
}
