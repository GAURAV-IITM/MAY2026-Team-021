<template>
  <section
    class="modal confirm-dialog"
    role="dialog"
    aria-modal="true"
    aria-labelledby="confirm-dialog-title"
  >
    <header class="modal__header">
      <h2 id="confirm-dialog-title" class="text-h5 m-0">{{ title }}</h2>
    </header>
    <div class="modal__body">
      <p class="m-0">{{ message }}</p>
    </div>
    <footer class="modal__footer">
      <button class="btn btn--secondary" type="button">Cancel</button>
      <button class="btn btn--danger" type="button">Confirm</button>
    </footer>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'Confirm action',
  },
  message: {
    type: String,
    default: 'This action needs confirmation.',
  },
})
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add focus management, keyboard support, and action emits when destructive flows are implemented.
-->
