// @ts-check
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://jeongicall.site',
  markdown: {
    shikiConfig: { theme: 'github-light' },
  },
});
