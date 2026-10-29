// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

// GitHub Pages serves this repo at /firstrepo-/. With a custom domain,
// build with BASE_PATH=/ and SITE_URL=https://your-domain.
const site = process.env.SITE_URL ?? 'https://sebvstianlopz.github.io';
const base = process.env.BASE_PATH ?? '/firstrepo-';

export default defineConfig({
  site,
  base,
  trailingSlash: 'always',
  build: { inlineStylesheets: 'always' },
  vite: { plugins: [tailwindcss()] },
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  integrations: [
    react(),
    sitemap({
      i18n: { defaultLocale: 'es', locales: { es: 'es-DO', en: 'en-US' } },
    }),
  ],
});
