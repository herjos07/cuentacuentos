import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://herjos.com',
  base: '/cuentacuentos',
  integrations: [] // Dejar vacío para eliminar la integración conflictiva
});
