<template>
  <div class="app-layout app-layout--superadmin">
    <Navbar />
    <Sidebar />
    <main class="app-layout__main">
      <slot>
        <RouterView />
      </slot>
    </main>
    <Footer />
  </div>
</template>

<script setup>
import Navbar from '../components/layout/Navbar.vue'
import Sidebar from '../components/layout/Sidebar.vue'
import Footer from '../components/layout/Footer.vue'
import { RouterView } from 'vue-router'
</script>

<!--
src/layouts: Shared page frames for route groups.
TODO:
- Add platform-level navigation for Super Admin workflows.
-->
