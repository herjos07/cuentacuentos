import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://herjos.com', // <--- Asegúrate de incluir la URL base aquí
  base: '/cuentacuentos',     // Tu subruta del proyecto
  integrations: [sitemap()],
});
