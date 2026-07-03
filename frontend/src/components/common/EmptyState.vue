<template>
  <section class="empty-state" aria-live="polite">
    <div class="empty-state__icon" aria-hidden="true">
      <slot name="icon">i</slot>
    </div>
    <h2 class="text-h5 m-0">
      <slot name="title">{{ title }}</slot>
    </h2>
    <p class="text-small m-0">
      <slot name="description">{{ description }}</slot>
    </p>
    <div class="flex items-center justify-center gap-2">
      <slot name="primary-action">
        <button class="btn btn--primary" type="button">Primary Action</button>
      </slot>
      <slot name="secondary-action">
        <button class="btn btn--secondary" type="button">Secondary Action</button>
      </slot>
    </div>
  </section>
</template>

<script setup>
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

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add title, description, action slot, and illustration support.
-->
