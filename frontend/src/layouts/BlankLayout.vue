<template>
  <RouterView />
</template>

<script setup>
import { RouterView } from 'vue-router'
</script>

<!--
src/layouts: Shared page frames for route groups.
TODO:
- Use this layout for 404, maintenance, privacy policy, terms, and landing pages.
- Keep this layout free of navbar, sidebar, and footer chrome.
-->
