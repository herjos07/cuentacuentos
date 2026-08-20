import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://herjos.com',
  base: '/cuentacuentos',
  integrations: [sitemap()],
});
