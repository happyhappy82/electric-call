import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    keyword: z.string(),
    service: z.string().default('전기공사'),
    region: z.string().optional(),
    publishedAt: z.string().optional(),
  }),
});

export const collections = { blog };
