import { site, type Lang } from '../config/site';
import { path } from '../i18n';
import { vehicleFullName, type Vehicle } from './vehicles';

export function businessJsonLd(lang: Lang, origin: URL, vehicles: Vehicle[]) {
  const prices = vehicles.map((v) => v.data.priceDay).filter((p): p is number => !!p);
  return {
    '@context': 'https://schema.org',
    '@type': 'AutoRental',
    name: site.name,
    url: new URL(path(lang, 'home'), origin).href,
    telephone: `+${site.whatsapp}`,
    priceRange: prices.length ? `US$ ${Math.min(...prices)} – US$ ${Math.max(...prices)}` : undefined,
    address: { '@type': 'PostalAddress', addressLocality: 'Santo Domingo', addressCountry: 'DO' },
    areaServed: { '@type': 'Country', name: 'República Dominicana' },
    sameAs: [site.social.instagram],
  };
}

export function vehicleJsonLd(v: Vehicle, lang: Lang, origin: URL, imageUrl: string) {
  const offers = [];
  if (v.data.priceDay)
    offers.push({
      '@type': 'Offer',
      businessFunction: 'http://purl.org/goodrelations/v1#LeaseOut',
      priceSpecification: { '@type': 'UnitPriceSpecification', price: v.data.priceDay, priceCurrency: site.currency, unitCode: 'DAY' },
      availability: v.data.available ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
    });
  if (v.data.priceSale)
    offers.push({ '@type': 'Offer', price: v.data.priceSale, priceCurrency: site.currency });
  return {
    '@context': 'https://schema.org',
    '@type': 'Car',
    name: vehicleFullName(v, lang),
    ...(v.data.brand ? { brand: { '@type': 'Brand', name: v.data.brand } } : {}),
    ...(v.data.year ? { modelDate: String(v.data.year) } : {}),
    color: v.data.color,
    seatingCapacity: v.data.seats,
    image: imageUrl,
    url: new URL(path(lang, 'catalog', v.id), origin).href,
    offers,
  };
}
