<template>
  <header class="app-navbar student-navbar">
    <div class="app-navbar__brand">
      <button
        class="app-navbar__menu-button"
        type="button"
        :aria-expanded="String(isSidebarOpen)"
        aria-controls="student-sidebar"
        aria-label="Toggle student sidebar"
        @click="$emit('toggleSidebar')"
      >
        <Menu :size="20" aria-hidden="true" />
      </button>
      <span class="app-navbar__logo"><LibraryBig :size="19" aria-hidden="true" /> Smart Library App</span>
    </div>

    <div class="app-navbar__page">
      <p class="app-navbar__breadcrumb">Student / {{ pageTitle }}</p>
      <h1>{{ pageTitle }}</h1>
    </div>

    <div class="app-navbar__actions" aria-label="Student toolbar">
      <label class="app-navbar__search">
        <span class="sr-only">Search</span>
        <Search :size="17" aria-hidden="true" />
        <input type="search" placeholder="Search" />
      </label>
      <button class="app-navbar__icon-button" type="button" aria-label="Notifications" title="Notifications">
        <Bell :size="19" aria-hidden="true" />
      </button>
      <span class="app-navbar__role">{{ roleLabel }}</span>
      <button class="app-navbar__profile" type="button">
        <UserRound :size="17" aria-hidden="true" /> {{ currentUserName }}
      </button>
      <button class="app-navbar__logout" type="button" @click="handleLogout">
        <LogOut :size="17" aria-hidden="true" /> Logout
      </button>
    </div>
  </header>
</template>

<script setup>
import { Bell, LibraryBig, LogOut, Menu, Search, UserRound } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../../stores/authStore'

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
  isSidebarOpen: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggleSidebar'])

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { currentUser, currentRole } = storeToRefs(authStore)

const pageTitle = computed(() => route.meta.title || 'Dashboard')
const currentUserName = computed(() => currentUser.value?.name || 'Student User')
const roleLabel = computed(() => currentUser.value?.roleLabel || currentRole.value || 'Student')

async function handleLogout() {
  await authStore.logout()
  await router.push({ name: 'login' })
}
</script>

<!--
TODO: Add student account navigation after authentication is implemented.
-->
