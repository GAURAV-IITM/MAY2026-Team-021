import { createPinia } from 'pinia'

// src/plugins: Vue plugin setup helpers used by the application bootstrap.
export const pinia = createPinia()

export function setupPinia(app) {
  // TODO: Register Pinia plugins here when shared store behavior is needed.
  app.use(pinia)
}
