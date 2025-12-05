import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // Forward these specific paths to your backend
      '/chat': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/upload': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/list-all-files': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/delete_files': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      }
    }
  }
})