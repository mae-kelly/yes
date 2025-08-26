import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

console.log('🔍 vite.config.mjs: Loading configuration...');

export default defineConfig({
  plugins: [
    svelte({
      onwarn: (warning, handler) => {
        console.log('⚠️ Svelte warning:', warning.message);
        handler(warning);
      }
    })
  ],
  
  // Enhanced logging
  logLevel: 'info',
  
  optimizeDeps: {
    force: true,
    include: ['svelte']
  },
  
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: undefined
      }
    }
  },
  
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        configure: (proxy, options) => {
          console.log('🔍 Proxy configured for /api -> localhost:5000');
        }
      }
    }
  },
  
  // Additional debugging
  define: {
    __DEV__: true
  }
})

console.log('✅ vite.config.mjs: Configuration exported');