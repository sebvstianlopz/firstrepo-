// The one place every "book" button gets its WhatsApp link from.
// Runs both at build time (default links that work without JavaScript)
// and in the browser (links updated as visitors pick dates and places).
import { site, type Lang } from '../config/site';

export type Intent =
  | { kind: 'general' }
  | { kind: 'rent'; car: string; from?: string; to?: string; days?: number; place?: string; url?: string }
  | { kind: 'sale'; car: string; price?: string; visit?: string; url?: string };

const fmtDate = (iso: string, lang: Lang) =>
  new Intl.DateTimeFormat(lang === 'es' ? 'es-DO' : 'en-US', { day: 'numeric', month: 'long', timeZone: 'UTC' })
    .format(new Date(`${iso}T00:00:00Z`));

export function waMessage(intent: Intent, lang: Lang): string {
  const es = lang === 'es';
  const hi = es ? `Hola, ${site.name} 👋` : `Hi, ${site.name} 👋`;
  const parts: string[] = [hi];

  if (intent.kind === 'general') {
    parts.push(es ? 'Quisiera reservar un vehículo.' : 'I’d like to book a vehicle.');
  } else if (intent.kind === 'rent') {
    let line = es ? `Me interesa alquilar el ${intent.car}` : `I’d like to rent the ${intent.car}`;
    if (intent.from && intent.to) {
      const span = es
        ? ` del ${fmtDate(intent.from, lang)} al ${fmtDate(intent.to, lang)}`
        : ` from ${fmtDate(intent.from, lang)} to ${fmtDate(intent.to, lang)}`;
      const days = intent.days ? (es ? ` (${intent.days} días)` : ` (${intent.days} days)`) : '';
      line += span + days;
    }
    if (intent.place) line += es ? `, con entrega en ${intent.place}` : `, delivered to ${intent.place}`;
    parts.push(`${line}. ${es ? '¿Está disponible?' : 'Is it available?'}`);
    if (intent.url) parts.push(intent.url);
  } else {
    let line = es ? `Me interesa comprar el ${intent.car}` : `I’m interested in buying the ${intent.car}`;
    if (intent.price) line += ` (${intent.price})`;
    line += '.';
    if (intent.visit) {
      line += es
        ? ` Me gustaría verlo el ${fmtDate(intent.visit, lang)}.`
        : ` I’d like to see it on ${fmtDate(intent.visit, lang)}.`;
    }
    parts.push(`${line} ${es ? '¿Está disponible?' : 'Is it available?'}`);
    if (intent.url) parts.push(intent.url);
  }
  return parts.join('\n');
}

export const waLink = (intent: Intent, lang: Lang) =>
  `https://wa.me/${site.whatsapp}?text=${encodeURIComponent(waMessage(intent, lang))}`;
