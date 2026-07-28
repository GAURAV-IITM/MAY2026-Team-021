<template>
  <div ref="menuRef" class="announcement-actions">
    <button class="btn btn--ghost btn--icon" type="button" title="Announcement actions" aria-label="Announcement actions" :aria-expanded="String(isMenuOpen)" aria-haspopup="menu" @click="toggleMenu">
      <Ellipsis :size="18" aria-hidden="true" />
    </button>
    <div v-if="isMenuOpen" class="announcement-actions__menu" role="menu">
      <button v-if="['draft', 'scheduled'].includes(announcement.status)" type="button" role="menuitem" @click="select('edit')"><Pencil :size="16" /> Edit</button>
      <button v-if="['draft', 'scheduled'].includes(announcement.status)" type="button" role="menuitem" @click="select('publish')"><Send :size="16" /> Publish now</button>
      <button v-if="['published', 'scheduled', 'expired'].includes(announcement.status)" type="button" role="menuitem" @click="select('archive')"><Archive :size="16" /> Archive</button>
      <button v-if="['draft', 'archived'].includes(announcement.status)" class="announcement-actions__danger" type="button" role="menuitem" @click="select('delete')"><Trash2 :size="16" /> Delete</button>
    </div>
  </div>
</template>

<script setup>
import { Archive, Ellipsis, Pencil, Send, Trash2 } from '@lucide/vue'
import { useDismissibleMenu } from '../../composables/useDismissibleMenu.js'

defineProps({ announcement: { type: Object, required: true } })
const emit = defineEmits(['action'])
const { menuRef, isMenuOpen, closeMenu, toggleMenu } = useDismissibleMenu()
function select(action) { closeMenu(); emit('action', action) }
</script>

<style scoped>
.announcement-actions { position: relative; display: inline-flex; }
.announcement-actions__menu { position: absolute; top: calc(100% + var(--space-1)); right: 0; z-index: var(--z-dropdown); width: 165px; padding: var(--space-2); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-lg); }
.announcement-actions__menu button { display: flex; align-items: center; gap: var(--space-2); width: 100%; padding: var(--space-2) var(--space-3); border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--color-text-primary); text-align: left; }
.announcement-actions__menu button:hover { background: var(--color-hover); }
.announcement-actions__menu .announcement-actions__danger { color: var(--color-danger); }
</style>
