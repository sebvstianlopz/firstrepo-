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
| Replace the home page hero photo | Overwrite `src/assets/hero.jpg` (landscape, at least 2400 × 1350 px, car on the right half) |
| Replace the car that drives across the hero | Overwrite `public/images/hero-car.webp` with a transparent side-view image of a car facing right (about 3:1). In `src/components/home/Hero.astro`, set `revealAt` to where the rear bumper sits, as a fraction of the image width |
| Change the WhatsApp number, hours, delivery points or Instagram | `src/config/site.ts` |
| Change any text on the site (ES and EN) | `src/i18n/index.ts` |

Each `data.yaml` is checked when the site builds. A typo (an unknown category or a
missing price) stops the build with a message naming the file.

## How it's built

Astro renders every page to static HTML. The one interactive exception is the home hero,
a React island (`ScrollFlyIn`, framer-motion) that moves the car with the scroll and wipes
the headline in behind it.

The project follows the shadcn layout so more shadcn/21st.dev components can be dropped in:

- `components.json`: shadcn config (`@/components/ui`, `@/lib/utils`)
- `src/components/ui/`: React components copied from shadcn or 21st.dev. They import
  each other through the `@/components/ui/...` alias, and the shadcn CLI installs into this
  folder, so keeping them here makes copy-pasted components work without editing imports
- `src/lib/utils.ts`: the `cn()` class helper those components expect
- `src/styles/tailwind.css`: Tailwind v4, generated only from `src/components/ui` and
  without its reset, so it can't restyle the Astro pages

To add a shadcn component: `npx shadcn@latest add <name>`, then use it in an `.astro` file
with a `client:*` directive (for example `client:visible`).

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
