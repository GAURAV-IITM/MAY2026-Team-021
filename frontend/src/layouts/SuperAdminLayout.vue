<template>
  <div class="app-layout app-layout--superadmin">
    <SuperAdminNavbar />
    <SuperAdminSidebar />
    <main class="app-layout__main">
      <slot>
        <RouterView />
      </slot>
    </main>
    <Footer />
  </div>
</template>

<script setup>
import SuperAdminNavbar from '../components/layout/SuperAdminNavbar.vue'
import SuperAdminSidebar from '../components/layout/SuperAdminSidebar.vue'
import Footer from '../components/layout/Footer.vue'
import { RouterView } from 'vue-router'
</script>

<!--
src/layouts: Shared page frames for route groups.
TODO:
- Add platform-level navigation for Super Admin workflows.
-->
