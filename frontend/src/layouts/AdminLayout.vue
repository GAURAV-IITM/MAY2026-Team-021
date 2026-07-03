<template>
  <div
    class="app-layout app-layout--dashboard app-layout--admin"
    :class="{ 'is-sidebar-collapsed': isSidebarCollapsed, 'is-sidebar-open': isSidebarOpen }"
  >
    <AdminNavbar
      :is-sidebar-collapsed="isSidebarCollapsed"
      :is-sidebar-open="isSidebarOpen"
      @toggle-sidebar="toggleSidebar"
    />
    <AdminSidebar
      :is-collapsed="isSidebarCollapsed"
      :is-open="isSidebarOpen"
      @close="closeSidebar"
    />
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
import { ref } from 'vue'
import { RouterView } from 'vue-router'

const isSidebarCollapsed = ref(false)
const isSidebarOpen = ref(false)

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  isSidebarOpen.value = !isSidebarOpen.value
}

function closeSidebar() {
  isSidebarOpen.value = false
}
</script>

<!--
src/layouts: Shared page frames for route groups.
TODO:
- Add admin navigation, tenant context, and role-aware layout behavior.
- Tenant validation will be reflected in this shell after route guards provide tenant context.
-->
