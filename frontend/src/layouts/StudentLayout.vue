<template>
  <div
    class="app-layout app-layout--dashboard app-layout--student"
    :class="{ 'is-sidebar-collapsed': isSidebarCollapsed, 'is-sidebar-open': isSidebarOpen }"
  >
    <StudentNavbar
      :is-sidebar-collapsed="isSidebarCollapsed"
      :is-sidebar-open="isSidebarOpen"
      @toggle-sidebar="toggleSidebar"
    />
    <StudentSidebar
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
import StudentNavbar from '../components/layout/StudentNavbar.vue'
import StudentSidebar from '../components/layout/StudentSidebar.vue'
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
- Add student navigation and account-specific layout behavior.
-->
