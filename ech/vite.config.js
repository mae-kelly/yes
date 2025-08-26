import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  root: './',
  server: {
    port: 3000,
    host: true,
    hmr: {
      overlay: false
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: './index.html',
      output: {
        manualChunks: {
          vendor: ['svelte']
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': './'
    }
  },
  optimizeDeps: {
    include: ['svelte']
  }
})