# Los Eternos — website

Bilingual (ES/EN) catalog site for Los Eternos car rentals in the Dominican Republic.
Every "Reservar" button opens WhatsApp with a ready-made message: the car, the dates,
the delivery point and a link back to the car's page.

Built with [Astro](https://astro.build) as a static site. No server, no database.

## Everyday changes

| I want to… | Edit |
|---|---|
| Change a price, name or seat count | `src/content/vehicles/<car>/data.yaml` |
| Replace a placeholder photo | Put the real photo in the car's folder as `1.jpg`, then delete the `photoPending: true` line |
| Add more photos to a car | Add `2.jpg`, `3.jpg`… to its folder and list them: `photos: [./1.jpg, ./2.jpg, ./3.jpg]` |
| Add a car | Copy any car folder, rename it (the folder name becomes the URL) and edit `data.yaml` |
| Hide a car without deleting it | Add `available: false` |
| Show a car on the home page | Add `featured: true` |
| Offer a car for sale | Add `mode: sale` (or `both`) and `priceSale: 25000`. The catalog's sale filter and the car's Buy tab appear automatically |
| Change the WhatsApp number, hours, delivery points or Instagram | `src/config/site.ts` |
| Change any text on the site (ES and EN) | `src/i18n/index.ts` |

Each `data.yaml` is checked when the site builds. A typo (an unknown category or a
missing price) stops the build with a message naming the file.

## Run it locally

```sh
cd los-eternos
npm install
npm run dev      # http://localhost:4321/firstrepo-/
npm run build    # outputs dist/
```

## Publishing

`.github/workflows/los-eternos-pages.yml` builds and publishes to GitHub Pages on every
push to `main` that touches this folder. One-time setup: in the repository on GitHub, go to
**Settings → Pages → Build and deployment → Source** and choose **GitHub Actions**.

The site then lives at `https://sebvstianlopz.github.io/firstrepo-/`. For a custom domain,
set `SITE_URL=https://your-domain` and `BASE_PATH=/` in the workflow's build step.
