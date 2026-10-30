# Maison: a Louis Vuitton concept storefront

A practice project: a calm, minimal storefront whose one job is to get a visitor to open a piece and add it to the bag.

> Design study, not affiliated with or endorsed by Louis Vuitton. The wordmark is plain type, the pictures are drawn
> stand-ins, and checkout is a demo that never asks for card details.

Built with [Astro](https://astro.build) as a static site. No server, no database. It is a separate project from
`los-eternos/` and does not touch it or its deploy.

## Run it

```bash
cd maison
npm install
npm run dev        # http://localhost:4321
npm run build      # static site in dist/
npm run check      # types and content schema
```

## Pages

| Page | What it does |
|---|---|
| `/` | The name as a monument, the season's pieces, the house's story, new arrivals, a shop index, then a call to the collection |
| `/collection/` | Every piece, with category filters (kept in the URL, e.g. `?c=men`) and sorting |
| `/collection/<piece>/` | Pictures, colour and size, **Add to bag**, details, and "Complete the look" |
| `/checkout/` | Contact and delivery form plus the order summary. Payment is switched off |
| `/checkout/confirmation/` | The order a client would see after placing it |

The **Deliver to** picker (in the hero, header, menu and checkout) is the site's one live element. Choosing a city
switches every price to its currency and updates the delivery promise everywhere. The bag lives in `localStorage`.

## Everyday changes

| I want to… | Edit |
|---|---|
| Change a name, price, sizes or text | `src/content/pieces/<piece>/data.yaml` |
| Use a real photo | Overwrite `1.jpg` (front) and `2.jpg` (detail) in the piece's folder (portrait 4:5, at least 1200 × 1500 px), then delete the `photoPending: true` line |
| Add a piece | Copy any piece folder, rename it (the folder name becomes the URL) and edit `data.yaml` |
| Show a piece on the home page | `featured: true` (season band) or `isNew: true` (new arrivals) |
| Change cities, delivery days, exchange rates or the advisor email | `src/config/site.ts` |
| Replace the house pictures on the home page | `src/assets/house/*.jpg` |
| Redraw the stand-in pictures | `npm run placeholders -- --force` (without `--force` it only fills in missing files, so real photos are never overwritten) |

## How it's built

- `src/styles/global.css`: colour and type tokens (Jost + Cormorant Garamond), the one button, frames, entrance motion
- `src/scripts/city.ts`: the delivery city, currency conversion and delivery promise
- `src/scripts/bag.ts`: the bag store; `src/components/BagDrawer.astro` renders it
- All motion respects `prefers-reduced-motion`, and every page reads fine without JavaScript (prices then show in USD)

## Sample content to replace before using this for real

Delivery days per city, exchange rates, the piece names, descriptions and prices, `advisor@example.com`, and every
picture (all are drawings made by `scripts/make-placeholders.mjs`).
