<template>
  <div class="app-layout app-layout--admin">
    <AdminNavbar />
    <AdminSidebar />
    <main class="app-layout__main">
      <slot>
        <RouterView />
      </slot>
    </main>
    <Footer />
  </div>
</template>

<script setup>
import AdminNavbar from '../components/layout/AdminNavbar.vue'
import AdminSidebar from '../components/layout/AdminSidebar.vue'
import Footer from '../components/layout/Footer.vue'
import { RouterView } from 'vue-router'
</script>

<!--
src/layouts: Shared page frames for route groups.
TODO:
- Add admin navigation, tenant context, and role-aware layout behavior.
- Tenant validation will be reflected in this shell after route guards provide tenant context.
-->
