import { getCollection, type CollectionEntry } from 'astro:content';

export type Piece = CollectionEntry<'pieces'>;

/** Every piece, in the house's own order. */
export async function getPieces(): Promise<Piece[]> {
  const all = await getCollection('pieces');
  return all.sort((a, b) => a.data.order - b.data.order);
}
