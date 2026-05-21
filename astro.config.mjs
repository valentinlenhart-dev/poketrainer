import { defineConfig } from 'astro/config';
import preact from '@astrojs/preact';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://pokenom.fr',
  output: 'static',
  integrations: [
    preact({ compat: true }),
    sitemap({
      changefreq: 'weekly',
      priority: 0.7,
    }),
  ],
  build: {
    inlineStylesheets: 'auto',
  },
  vite: {
    json: {
      stringify: true,
    },
    resolve: {
      alias: {
        'react': 'preact/compat',
        'react-dom': 'preact/compat',
      },
    },
    optimizeDeps: {
      include: ['preact', 'preact/hooks', 'preact/compat'],
    },
  },
});
