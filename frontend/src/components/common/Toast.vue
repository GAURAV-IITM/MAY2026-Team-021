<template>
  <div class="toast-region" aria-live="polite" aria-atomic="true">
    <section class="toast" :class="`toast--${type}`" role="status">
      <p class="text-label m-0">{{ label }}</p>
      <p class="text-small m-0">
        <slot>Toast message placeholder</slot>
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'info',
  },
})

const label = computed(() => {
  const labels = {
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Info',
  }

  return labels[props.type] || labels.info
})
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add toast queueing and timeout handling when application notifications are implemented.
-->
