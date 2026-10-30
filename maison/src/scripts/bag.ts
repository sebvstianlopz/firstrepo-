// The shopping bag, kept in localStorage so it survives page loads.
// If storage is blocked (private mode), it lives in memory until the page closes.

export interface BagItem {
  slug: string;
  name: string;
  color: string;
  size: string;
  price: number;
  image: string;
  qty: number;
}

const KEY = 'maison-bag';
let memory: BagItem[] = [];

export function readBag(): BagItem[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]');
  } catch {
    return memory;
  }
}

function write(items: BagItem[]) {
  memory = items;
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    /* kept in memory */
  }
  document.dispatchEvent(new CustomEvent('bag:change', { detail: items }));
}

export function addToBag(item: Omit<BagItem, 'qty'>) {
  const items = readBag();
  const line = items.find((i) => i.slug === item.slug && i.color === item.color && i.size === item.size);
  if (line) line.qty = Math.min(line.qty + 1, 5);
  else items.push({ ...item, qty: 1 });
  write(items);
}

export function setQty(index: number, qty: number) {
  const items = readBag();
  if (!items[index]) return;
  if (qty < 1) items.splice(index, 1);
  else items[index].qty = Math.min(qty, 5);
  write(items);
}

export const clearBag = () => write([]);
export const bagCount = (items = readBag()) => items.reduce((n, i) => n + i.qty, 0);
export const bagTotal = (items = readBag()) => items.reduce((n, i) => n + i.qty * i.price, 0);
