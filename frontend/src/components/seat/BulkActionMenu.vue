<template>
  <details class="bulk-action-menu">
    <summary
      class="btn btn--secondary bulk-action-menu__trigger"
      :class="{ 'is-disabled': disabled }"
      @click="handleTriggerClick"
    >
      Bulk Actions
    </summary>

    <div class="bulk-action-menu__content" role="menu">
      <p class="text-caption text-muted m-0">
        {{ selectedCount }} selected
      </p>
      <button
        class="bulk-action-menu__item bulk-action-menu__item--danger"
        type="button"
        role="menuitem"
        :disabled="disabled"
        @click="$emit('action', 'delete')"
      >
        Delete Selected Seats
      </button>
      <button
        class="bulk-action-menu__item"
        type="button"
        role="menuitem"
        :disabled="disabled"
        @click="$emit('action', 'available')"
      >
        Mark Available
      </button>
      <button
        class="bulk-action-menu__item"
        type="button"
        role="menuitem"
        :disabled="disabled"
        @click="$emit('action', 'maintenance')"
      >
        Mark Maintenance
      </button>
      <button
        class="bulk-action-menu__item"
        type="button"
        role="menuitem"
        :disabled="disabled"
        @click="$emit('action', 'blocked')"
      >
        Mark Blocked
      </button>
    </div>
  </details>
</template>

<script setup>
const props = defineProps({
  selectedCount: {
    type: Number,
    default: 0,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['action'])

function handleTriggerClick(event) {
  if (!props.disabled) return

  event.preventDefault()
  event.currentTarget.parentElement?.removeAttribute('open')
}
</script>

<style scoped>
.bulk-action-menu {
  position: relative;
  display: inline-flex;
}

.bulk-action-menu__trigger {
  list-style: none;
  cursor: pointer;
}

.bulk-action-menu__trigger::-webkit-details-marker {
  display: none;
}

.bulk-action-menu__trigger.is-disabled {
  opacity: 0.6;
  pointer-events: none;
}

.bulk-action-menu__content {
  position: absolute;
  right: 0;
  top: calc(100% + var(--space-2));
  z-index: 20;
  display: grid;
  gap: var(--space-1);
  min-width: 220px;
  padding: var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-lg);
}

.bulk-action-menu__item {
  min-height: 36px;
  padding: 0 var(--space-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.bulk-action-menu__item:hover {
  background: var(--color-hover);
}

.bulk-action-menu__item--danger {
  color: var(--color-danger);
}
</style>
