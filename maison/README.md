# Maison Vael: a concept storefront

A practice project: a clean, streetwear-editorial storefront whose one job is to get a visitor to open a piece and add it to the bag.

> Maison Vael is a fictional house made for a design study. The pictures are grey stand-ins until real ones are
> added, and checkout is a demo that never asks for card details.

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
| `/` | Edge-to-edge `MAISON VAEL` title, the campaign photo with the red season scribble, a featured bento with price pills, an editorial split, then new arrivals |
| `/collection/` | Every piece, with category tabs, a **Saved ♥** tab, sorting, and pagination past 12 pieces. Tabs are kept in the URL, e.g. `?c=men` |
| `/collection/<piece>/` | Cut-out pictures, colour and size, **Add to bag**, a heart to save it, details, and "Complete the look" |
| `/checkout/` | Contact and delivery form plus the order summary. Payment is switched off |
| `/checkout/confirmation/` | The order a client would see after placing it |

The **Deliver to** picker (in the hero, header, menu and checkout) switches every price to that city's currency and
updates the delivery promise everywhere. The bag and the saved pieces live in `localStorage`.

## Adding your pictures

Every slot shows a grey stand-in that names itself and its ideal size. Replace a slot by saving your file under the
same name, then delete the piece's `photoPending: true` line.

| Slot | File | Ideal size |
|---|---|---|
| Link-preview image | `src/assets/campaign/hero.jpg` | Landscape 3:2, 2400 × 1600 |
| Editorial, large | `src/assets/campaign/editorial-large.jpg` | Portrait 4:5, 1600 × 2000 |
| Editorial, small | `src/assets/campaign/editorial-small.jpg` | Portrait 3:4, 1200 × 1600 |
| A piece, front | `src/content/pieces/<piece>/1.png` | Square 1:1, 1600 × 1600, cut-out on white or transparent |
| A piece, back or detail | `src/content/pieces/<piece>/2.png` | Same as the front |

To use `.jpg` for a piece instead, change its `photos:` line in `data.yaml` to match.

### The home page rail

The hero is a clothing rail (`src/components/ui/product-rail-gallery.tsx`, a React component). A piece hangs on it
when its `data.yaml` has a `rail:` line, e.g. `rail: { kind: coat }`. Until it has photos, the rail draws it as that
`kind` (`tee`, `knit`, `hoodie`, `shirt`, `jacket` or `coat`), once per colour.

To hang a photo instead, take a picture of the garment on a plain, light background and run:

```bash
npm run rail-photo -- <piece-folder-name> front path/to/front.jpg
npm run rail-photo -- <piece-folder-name> back  path/to/back.jpg    # optional
npm run rail-photo -- <piece-folder-name> side  path/to/side.jpg    # optional
```

It removes the background, scales the garment and saves it to `src/assets/rail/<piece>/`, where the rail picks it up.

## Everyday changes

| I want to… | Edit |
|---|---|
| Change a name, price, colour, sizes or text | `src/content/pieces/<piece>/data.yaml` |
| Add a piece | Copy any piece folder, rename it (the folder name becomes the URL), edit `data.yaml`, run `npm run placeholders` |
| Show a piece on the home page | `featured: true` (bento) or `isNew: true` (new arrivals) |
| Change the season name, scribble or intro | `collection` in `src/config/site.ts` |
| Change cities, delivery days, exchange rates, address, socials or the advisor email | `src/config/site.ts` |

## How it's built

- `src/styles/global.css`: tokens (white, black, signal red `#e10600`), Archivo with its width axis for type, Reenie Beanie for the scribble, buttons, pills, the product grid, and entrance motion.
- `src/components/PageTitle.astro`: titles that size themselves to fill the page edge to edge.
- `src/components/ui/`: React components in the shadcn layout (`components.json` at the root), styled with Tailwind
  through the shadcn colour names mapped in `global.css`. `src/components/home/HeroRail.tsx` feeds the rail from the collection.
- `src/scripts/city.ts`, `bag.ts` and `saved.ts`: the delivery city, the bag and the wishlist.
- Motion follows a few rules: strong ease-out curves, UI motion under 300ms, a slight press-in on everything tappable, hover effects only on mouse devices, and reduced motion keeps the fades but drops the movement.
- Mobile: no tap flash, safe-area padding for notched phones, 16px fields so iOS doesn't zoom, and a swipeable gallery with a bottom buy bar.

## Sample content to replace before using this for real

Delivery days per city, exchange rates, the address, social links, `advisor@example.com`, the season copy, the piece
names, descriptions and prices, and every picture.
