import { z, defineCollection } from 'astro:content';

const cuentosCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.union([z.string(), z.date()]),
    category: z.string(),
    summary: z.string().optional(),
  }),
});

export const collections = {
  'cuentos': cuentosCollection,
};
