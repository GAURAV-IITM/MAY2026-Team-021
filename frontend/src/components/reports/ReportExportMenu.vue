<template>
  <div ref="menuRef" class="report-export">
    <button
      class="btn btn--secondary"
      type="button"
      :disabled="disabled"
      :aria-expanded="String(isMenuOpen)"
      aria-haspopup="menu"
      @click="toggleMenu"
    >
      <Download :size="17" aria-hidden="true" />
      {{ exporting ? 'Preparing...' : 'Export' }}
      <ChevronDown :size="15" aria-hidden="true" />
    </button>

    <div v-if="isMenuOpen" class="report-export__menu" role="menu">
      <button type="button" role="menuitem" @click="selectAction('csv')">
        <FileSpreadsheet :size="17" aria-hidden="true" />
        <span><strong>Download CSV</strong><small>Current report and filters</small></span>
      </button>
      <button type="button" role="menuitem" @click="selectAction('print')">
        <Printer :size="17" aria-hidden="true" />
        <span><strong>Print report</strong><small>Print or save as PDF</small></span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ChevronDown, Download, FileSpreadsheet, Printer } from '@lucide/vue'

import { useDismissibleMenu } from '../../composables/useDismissibleMenu.js'

defineProps({
  disabled: { type: Boolean, default: false },
  exporting: { type: Boolean, default: false },
})

const emit = defineEmits(['export', 'print'])
const { menuRef, isMenuOpen, closeMenu, toggleMenu } = useDismissibleMenu()

function selectAction(action) {
  closeMenu()
  emit(action === 'csv' ? 'export' : 'print')
}
</script>

<style scoped>
.report-export { position: relative; }
.report-export__menu {
  position: absolute;
  top: calc(100% + var(--space-2));
  right: 0;
  z-index: var(--z-dropdown);
  width: 230px;
  padding: var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-lg);
}
.report-export__menu button {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-primary);
  text-align: left;
}
.report-export__menu button:hover { background: var(--color-hover); }
.report-export__menu span { display: grid; gap: 2px; }
.report-export__menu small { color: var(--color-text-muted); }
</style>

