<template>
  <footer class="app-footer">
    <span class="app-footer__brand"><LibraryBig :size="17" aria-hidden="true" /> Smart Library App</span>
    <span><BadgeCheck :size="16" aria-hidden="true" /> Library operations platform</span>
    <span><Copyright :size="16" aria-hidden="true" /> {{ currentYear }} Smart Library App</span>
    <nav aria-label="Footer links">
      <a href="mailto:support@smartlibrary.app"><LifeBuoy :size="16" aria-hidden="true" /> Support</a>
    </nav>
  </footer>
</template>

<script setup>
import { BadgeCheck, Copyright, LibraryBig, LifeBuoy } from '@lucide/vue'

const currentYear = new Date().getFullYear()
</script>
