import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite configuration for the Vue 3 frontend.
// TODO: Add aliases, environment handling, and build tuning as the app grows.
export default defineConfig({
  plugins: [vue()],
})
