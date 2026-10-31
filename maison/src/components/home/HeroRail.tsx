import * as React from "react";
import { createPortal } from "react-dom";
import ClothingRailHero, { type GarmentKind, type RailGarment } from "@/components/ui/product-rail-gallery";
import { cities, defaultCity, formatPrice, url, type City } from "@/config/site";

export interface RailPiece {
  id: string;
  name: string;
  kind: GarmentKind;
  color: string;
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
  heading: string;
  caption: string;
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

export default function HeroRail({ pieces, heading, caption }: Props) {
  const city = useCity();
  const [open, setOpen] = React.useState(null as number | null);

  const items = React.useMemo<RailGarment[]>(
    () =>
      pieces.map((p) => ({
        id: p.id,
        name: p.name,
        kind: p.kind,
        color: p.color,
        description: p.description,
        details: p.details,
        tag: formatPrice(p.price, city.currency),
        image: p.image,
        backImage: p.backImage,
        sideImage: p.sideImage,
      })),
    [pieces, city],
  );

  const piece = open === null ? null : pieces[open];

  return (
    <>
      <ClothingRailHero
        items={items}
        heading={heading}
        caption={caption}
        hanger="matte"
        autoplay
        onOpenChange={setOpen}
        action={
          // Links are resolved in the browser so they also work in the portable build.
          <a href={url("collection/")} className="btn">
            Shop the collection
          </a>
        }
      />
      {/* While a piece is lifted off the rail, the way to buy it sits above the close-up. */}
      {piece &&
        createPortal(
          <a
            key={piece.id}
            href={url(`collection/${piece.id}/`)}
            className="btn fixed bottom-[calc(24px+env(safe-area-inset-bottom,0px))] left-1/2 z-[60] -translate-x-1/2 animate-in fade-in slide-in-from-bottom-2 duration-200 ease-out motion-reduce:slide-in-from-bottom-0"
          >
            Shop this piece · {formatPrice(piece.price, city.currency)}
          </a>,
          document.body,
        )}
    </>
  );
}
