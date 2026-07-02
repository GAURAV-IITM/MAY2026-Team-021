import { createApp } from 'vue'

import App from './App.vue'
import { pinia } from './plugins/pinia'
import router from './router'

import './styles/variables.css'
import './styles/theme.css'
import './styles/global.css'

// src/main.js: Application bootstrap for Vue, Pinia, Vue Router, and global styles.
// TODO: Add app-level plugin registration here as project integrations grow.
const app = createApp(App)

app.use(pinia)
app.use(router)

app.mount('#app')
