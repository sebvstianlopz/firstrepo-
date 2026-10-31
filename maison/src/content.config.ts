import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// One folder per piece: src/content/pieces/<slug>/data.yaml + its pictures.
const pieces = defineCollection({
  loader: glob({
    pattern: '*/data.yaml',
    base: './src/content/pieces',
    generateId: ({ entry }) => entry.split('/')[0],
  }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      category: z.enum(['women', 'men', 'leather-goods', 'accessories']),
      /** In US dollars; other currencies are converted on display. */
      price: z.number().positive(),
      colors: z.array(z.object({ name: z.string(), hex: z.string().regex(/^#[0-9a-fA-F]{6}$/) })).min(1),
      /** Leave out for one-size pieces. */
      sizes: z.array(z.string()).default([]),
      description: z.string(),
      details: z.array(z.string()).default([]),
      care: z.string().optional(),
      /** True while the pictures are drawn stand-ins. */
      photoPending: z.boolean().default(false),
      photos: z.array(image()).min(1),
      /** Hang this piece on the home page rail, drawn as `kind` until cut-outs exist. */
      rail: z
        .object({
          kind: z.enum(['tee', 'knit', 'hoodie', 'shirt', 'jacket', 'coat']),
          /** Cut-outs on a shared 200 × 310 portrait canvas, transparent background. */
          image: image().optional(),
          back: image().optional(),
          side: image().optional(),
        })
        .optional(),
      featured: z.boolean().default(false),
      isNew: z.boolean().default(false),
      order: z.number().default(100),
    }),
});

export const collections = { pieces };
