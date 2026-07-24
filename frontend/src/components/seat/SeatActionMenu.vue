<template>
  <div
    ref="menuRef"
    class="seat-action-menu"
    :class="`seat-action-menu--${placement}`"
  >
    <button
      class="btn btn--secondary btn--sm btn--icon seat-action-menu__trigger"
      type="button"
      aria-label="Seat actions"
      title="Seat actions"
      aria-haspopup="menu"
      :aria-expanded="String(isMenuOpen)"
      @click="toggleMenu"
    >
      <Ellipsis :size="18" aria-hidden="true" />
    </button>

    <div v-if="isMenuOpen" class="seat-action-menu__menu" role="menu">
      <span class="text-caption text-muted">Change Status</span>
      <button type="button" role="menuitem" @click="handleStatusChange('available')">
        <CircleCheckBig :size="16" aria-hidden="true" /> Mark Available
      </button>
      <button type="button" role="menuitem" @click="handleStatusChange('maintenance')">
        <Wrench :size="16" aria-hidden="true" /> Mark Maintenance
      </button>
      <button type="button" role="menuitem" @click="handleStatusChange('blocked')">
        <Ban :size="16" aria-hidden="true" /> Mark Blocked
      </button>
      <button type="button" role="menuitem" @click="handleViewMap">
        <Map :size="16" aria-hidden="true" /> View in Seat Map
      </button>
    </div>
  </div>
</template>

<script setup>
import { Ban, CircleCheckBig, Ellipsis, Map, Wrench } from '@lucide/vue'

import { useDismissibleMenu } from '../../composables/useDismissibleMenu'

const props = defineProps({
  seat: {
    type: Object,
    required: true,
  },
  placement: {
    type: String,
    default: 'bottom',
    validator: (value) => ['bottom', 'top'].includes(value),
  },
})

const emit = defineEmits(['change-status', 'view-map'])
const { menuRef, isMenuOpen, closeMenu, toggleMenu } = useDismissibleMenu()

function handleStatusChange(status) {
  closeMenu()
  emit('change-status', props.seat, status)
}

function handleViewMap() {
  closeMenu()
  emit('view-map', props.seat)
}
</script>

<style scoped>
.seat-action-menu {
  position: relative;
  display: inline-flex;
}

.seat-action-menu__trigger {
  cursor: pointer;
}

.seat-action-menu__menu {
  position: absolute;
  right: 0;
  top: calc(100% + var(--space-2));
  z-index: 30;
  display: grid;
  gap: var(--space-1);
  min-width: 190px;
  padding: var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-lg);
}

.seat-action-menu--top .seat-action-menu__menu {
  top: auto;
  bottom: calc(100% + var(--space-2));
}

.seat-action-menu__menu button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 34px;
  padding: 0 var(--space-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.seat-action-menu__menu button:hover {
  background: var(--color-hover);
}
</style>
