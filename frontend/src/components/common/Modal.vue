<template>
  <div v-if="isOpen" class="modal-backdrop" role="presentation" @click.self="$emit('close')">
    <section class="modal" role="dialog" aria-modal="true" :aria-labelledby="titleId" tabindex="-1">
      <header class="modal__header">
        <h2 :id="titleId" class="text-h5 m-0">
          <slot name="title">{{ title }}</slot>
        </h2>
        <button
          class="btn btn--ghost btn--icon"
          type="button"
          aria-label="Close modal"
          @click="$emit('close')"
        >
          x
        </button>
      </header>

      <div class="modal__body">
        <slot>Modal content placeholder</slot>
      </div>

      <footer class="modal__footer">
        <slot name="footer">
          <button class="btn btn--secondary" type="button" @click="$emit('close')">Cancel</button>
          <button class="btn btn--primary" type="button">Confirm</button>
        </slot>
      </footer>
    </section>
  </div>
</template>

<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    default: true,
  },
  title: {
    type: String,
    default: 'Modal Title',
  },
  titleId: {
    type: String,
    default: 'modal-title',
  },
})

defineEmits(['close'])
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add focus trapping and Escape-key handling when modal orchestration is implemented.
-->
