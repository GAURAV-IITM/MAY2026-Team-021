<template>
  <div class="app-layout app-layout--auth">
    <AuthNavbar />
    <main class="auth-layout__main">
      <div class="auth-layout__logo" aria-label="Smart Library App logo">Smart Library App</div>
      <section class="auth-layout__card">
        <slot>
          <RouterView />
        </slot>
      </section>
    </main>
    <Footer />
  </div>
</template>

<script setup>
import AuthNavbar from '../components/layout/AuthNavbar.vue'
import Footer from '../components/layout/Footer.vue'
import { RouterView } from 'vue-router'
</script>

<!--
src/layouts: Shared page frames for route groups.
TODO:
- Add centered auth styling and brand assets when the design system is finalized.
- Keep authentication pages separate from dashboard navigation and sidebars.
-->
