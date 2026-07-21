<template>
  <section class="empty-state" aria-live="polite">
    <div class="empty-state__icon" aria-hidden="true">
      <slot name="icon"><Inbox :size="26" /></slot>
    </div>
    <h2 class="text-h5 m-0">
      <slot name="title">{{ title }}</slot>
    </h2>
    <p class="text-small m-0">
      <slot name="description">{{ description }}</slot>
    </p>
    <div v-if="$slots['primary-action'] || $slots['secondary-action']" class="flex items-center justify-center gap-2">
      <slot name="primary-action"></slot>
      <slot name="secondary-action"></slot>
    </div>
  </section>
</template>

<script setup>
import { Inbox } from '@lucide/vue'

defineProps({
  title: {
    type: String,
    default: 'Nothing here yet',
  },
  description: {
    type: String,
    default: 'Content will appear here when it is available.',
  },
})
</script>
