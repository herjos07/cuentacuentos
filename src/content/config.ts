import { z, defineCollection } from 'astro:content';

const cuentosCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.union([z.string(), z.date()]),
    category: z.string(),
  }),
});

export const collections = {
  'cuentos': cuentosCollection,
};
