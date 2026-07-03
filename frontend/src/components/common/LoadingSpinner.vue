<template>
  <div class="loading-spinner" aria-live="polite" role="status">
    <span class="loading-spinner__indicator" aria-hidden="true"></span>
    <span>{{ label }}</span>
  </div>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    default: 'Loading',
  },
})
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add page, button, skeleton, and card loader composition where needed.
-->
