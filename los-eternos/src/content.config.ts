import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const text = z.object({ es: z.string(), en: z.string() });

// One folder per vehicle: src/content/vehicles/<slug>/data.yaml + its photos.
const vehicles = defineCollection({
  loader: glob({
    pattern: '*/data.yaml',
    base: './src/content/vehicles',
    generateId: ({ entry }) => entry.split('/')[0],
  }),
  schema: ({ image }) =>
    z
      .object({
        brand: z.string().optional(),
        // A plain model name, or a translated one for generic entries ("SUV compacto").
        model: z.union([z.string(), text]),
        color: z.enum(['blanco', 'negro', 'gris', 'plata', 'rojo', 'azul', 'azul-oscuro', 'lima']),
        year: z.number().int().optional(),
        category: z.enum(['compacto', 'suv', 'lujo', 'todoterreno', 'pickup', 'sedan', 'van']),
        mode: z.enum(['rent', 'sale', 'both']).default('rent'),
        priceDay: z.number().positive().optional(),
        priceSale: z.number().positive().optional(),
        seats: z.number().int().positive(),
        transmission: z.enum(['automatica', 'manual']).optional(),
        fuel: z.enum(['gasolina', 'diesel', 'hibrido', 'electrico']).optional(),
        highlights: z.array(text).max(4).default([]),
        description: text.optional(),
        /** True while the photo is a stand-in illustration. */
        photoPending: z.boolean().default(false),
        photos: z.array(image()).min(1),
        featured: z.boolean().default(false),
        available: z.boolean().default(true),
        order: z.number().default(100),
      })
      .refine((v) => v.mode === 'sale' || v.priceDay, {
        message: 'Vehicles for rent need priceDay',
      })
      .refine((v) => v.mode === 'rent' || v.priceSale, {
        message: 'Vehicles for sale need priceSale',
      }),
});

export const collections = { vehicles };
