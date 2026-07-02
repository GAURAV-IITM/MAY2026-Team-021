<template>
  <div class="app-layout app-layout--student">
    <StudentNavbar />
    <StudentSidebar />
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
import { RouterView } from 'vue-router'
</script>

<!--
src/layouts: Shared page frames for route groups.
TODO:
- Add student navigation and account-specific layout behavior.
-->
