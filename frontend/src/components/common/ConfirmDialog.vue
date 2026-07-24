<template>
  <div
    v-if="isOpen"
    class="modal-backdrop"
    role="presentation"
    @click.self="handleCancel"
  >
    <section
      class="modal confirm-dialog"
      role="alertdialog"
      aria-modal="true"
      :aria-labelledby="titleId"
      :aria-describedby="messageId"
    >
      <header class="modal__header">
        <h2 :id="titleId" class="text-h5 m-0">{{ title }}</h2>
      </header>

      <div class="modal__body">
        <div class="confirm-dialog__message">
          <TriangleAlert :size="22" aria-hidden="true" />
          <p :id="messageId" class="m-0">{{ message }}</p>
        </div>
      </div>

      <footer class="modal__footer">
        <button
          class="btn btn--secondary"
          type="button"
          :disabled="isConfirming"
          @click="handleCancel"
        >
          Cancel
        </button>

        <button
          class="btn btn--danger"
          type="button"
          :disabled="isConfirming"
          @click="$emit('confirm')"
        >
          <span v-if="isConfirming" class="btn__loader" aria-hidden="true"></span>
          <span>{{ isConfirming ? confirmingLabel : confirmLabel }}</span>
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup>
import { TriangleAlert } from '@lucide/vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: 'Confirm action',
  },
  message: {
    type: String,
    default: 'This action needs confirmation.',
  },
  confirmLabel: {
    type: String,
    default: 'Confirm',
  },
  confirmingLabel: {
    type: String,
    default: 'Processing',
  },
  isConfirming: {
    type: Boolean,
    default: false,
  },
  titleId: {
    type: String,
    default: 'confirm-dialog-title',
  },
  messageId: {
    type: String,
    default: 'confirm-dialog-message',
  },
})

const emit = defineEmits(['confirm', 'cancel'])

function handleCancel() {
  if (props.isConfirming) return

  emit('cancel')
}
</script>

<style scoped>
.confirm-dialog__message {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: var(--space-3);
}

.confirm-dialog__message svg {
  color: var(--color-warning);
}
</style>

<!--
src/components: Reusable confirmation dialog for destructive or important actions.

Responsibilities:
- Render confirmation content inside the shared modal presentation.
- Emit confirm and cancel actions.
- Prevent cancellation while an action is processing.
- Display loading state during asynchronous confirmation.
-->
