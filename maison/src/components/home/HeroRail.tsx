import * as React from "react";
import { createPortal } from "react-dom";
import ClothingRailHero, { type GarmentKind, type RailGarment } from "@/components/ui/product-rail-gallery";
import { cities, defaultCity, formatPrice, url, type City } from "@/config/site";

export interface RailPiece {
  id: string;
  name: string;
  kind: GarmentKind;
  colors: { name: string; hex: string }[];
  description: string;
  details: string[];
  /** In US dollars; shown on the hang tag in the visitor's currency. */
  price: number;
  image?: string;
  backImage?: string;
  sideImage?: string;
}

interface Props {
  pieces: RailPiece[];
  eyebrow: string;
  heading: string;
  caption: string;
}

/** One hanger on the rail, and the piece it sells. */
interface Hanger {
  key: string;
  piece: RailPiece;
  colour: { name: string; hex: string };
}

/** The delivery city chosen elsewhere on the page (scripts/city.ts keeps it in localStorage). */
function useCity(): City {
  const [city, setCity] = React.useState(defaultCity);
  React.useEffect(() => {
    try {
      const saved = cities.find((c) => c.id === localStorage.getItem("maison-city"));
      if (saved) setCity(saved);
    } catch {
      /* storage blocked: keep the default */
    }
    const onChange = (event: Event) => setCity((event as CustomEvent<City>).detail);
    document.addEventListener("city:change", onChange);
    return () => document.removeEventListener("city:change", onChange);
  }, []);
  return city;
}

/**
 * A piece with its own photographs hangs once. A drawn piece hangs once per
 * colourway, first colours first, so the rail reads like a full rack.
 */
function hang(pieces: RailPiece[]): Hanger[] {
  const rounds = Math.max(...pieces.map((p) => (p.image ? 1 : p.colors.length)));
  const out: Hanger[] = [];
  for (let round = 0; round < rounds; round++) {
    for (const piece of pieces) {
      const colour = piece.colors[round];
      if (!colour || (piece.image && round > 0)) continue;
      out.push({ key: `${piece.id}-${round}`, piece, colour });
    }
  }
  return out;
}

export default function HeroRail({ pieces, eyebrow, heading, caption }: Props) {
  const city = useCity();
  const [open, setOpen] = React.useState(null as number | null);
  const hangers = React.useMemo(() => hang(pieces), [pieces]);

  const items = React.useMemo<RailGarment[]>(
    () =>
      hangers.map(({ key, piece, colour }) => ({
        id: key,
        name: `${piece.name} · ${colour.name}`,
        kind: piece.kind,
        color: colour.hex,
        description: piece.description,
        details: piece.details,
        tag: formatPrice(piece.price, city.currency),
        image: piece.image,
        backImage: piece.backImage,
        sideImage: piece.sideImage,
      })),
    [hangers, city],
  );

  const lifted = open === null ? null : hangers[open];

  return (
    <>
      <ClothingRailHero
        items={items}
        eyebrow={eyebrow}
        heading={heading}
        caption={caption}
        hanger="wood"
        autoplay
        onOpenChange={setOpen}
        action={
          // Links are resolved in the browser so they also work in the portable build.
          <a href={url("collection/")} className="btn btn-paper">
            Shop the collection
          </a>
        }
      />
      {/* While a piece is lifted off the rail, the way to buy it sits above the close-up. */}
      {lifted &&
        createPortal(
          <a
            key={lifted.key}
            href={url(`collection/${lifted.piece.id}/`)}
            className="btn btn-paper fixed bottom-[calc(24px+env(safe-area-inset-bottom,0px))] left-1/2 z-[60] -translate-x-1/2 animate-in fade-in slide-in-from-bottom-2 duration-200 ease-out motion-reduce:slide-in-from-bottom-0"
          >
            Shop this piece · {formatPrice(lifted.piece.price, city.currency)}
          </a>,
          document.body,
        )}
    </>
  );
}
