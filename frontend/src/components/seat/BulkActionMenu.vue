<template>
  <div ref="menuRef" class="bulk-action-menu">
    <button
      class="btn btn--secondary bulk-action-menu__trigger"
      :class="{ 'is-disabled': disabled }"
      type="button"
      aria-haspopup="menu"
      :aria-expanded="String(isMenuOpen)"
      :disabled="disabled"
      @click="toggleMenu"
    >
      <Layers3 :size="17" aria-hidden="true" /> Bulk Actions <ChevronDown :size="15" aria-hidden="true" />
    </button>

    <div v-if="isMenuOpen" class="bulk-action-menu__content" role="menu">
      <p class="text-caption text-muted m-0">
        {{ selectedCount }} selected
      </p>
      <button
        class="bulk-action-menu__item bulk-action-menu__item--danger"
        type="button"
        role="menuitem"
        :disabled="disabled"
        @click="handleAction('delete')"
      >
        <Trash2 :size="16" aria-hidden="true" /> Delete Selected Seats
      </button>
      <button
        class="bulk-action-menu__item"
        type="button"
        role="menuitem"
        :disabled="disabled"
        @click="handleAction('available')"
      >
        <CircleCheckBig :size="16" aria-hidden="true" /> Mark Available
      </button>
      <button
        class="bulk-action-menu__item"
        type="button"
        role="menuitem"
        :disabled="disabled"
        @click="handleAction('maintenance')"
      >
        <Wrench :size="16" aria-hidden="true" /> Mark Maintenance
      </button>
      <button
        class="bulk-action-menu__item"
        type="button"
        role="menuitem"
        :disabled="disabled"
        @click="handleAction('blocked')"
      >
        <Ban :size="16" aria-hidden="true" /> Mark Blocked
      </button>
    </div>
  </div>
</template>

<script setup>
import { Ban, ChevronDown, CircleCheckBig, Layers3, Trash2, Wrench } from '@lucide/vue'
import { watch } from 'vue'

import { useDismissibleMenu } from '../../composables/useDismissibleMenu'

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

const emit = defineEmits(['action'])
const { menuRef, isMenuOpen, closeMenu, toggleMenu } = useDismissibleMenu()

watch(
  () => props.disabled,
  (isDisabled) => {
    if (isDisabled) {
      closeMenu()
    }
  },
)

function handleAction(action) {
  closeMenu()
  emit('action', action)
}
</script>

<style scoped>
.bulk-action-menu {
  position: relative;
  display: inline-flex;
}

.bulk-action-menu__trigger {
  cursor: pointer;
}

.bulk-action-menu__trigger.is-disabled {
  opacity: 0.6;
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
  display: flex;
  align-items: center;
  gap: var(--space-2);
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
