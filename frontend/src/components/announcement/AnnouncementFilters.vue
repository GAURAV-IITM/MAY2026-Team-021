<template>
  <section class="announcement-filters" aria-label="Announcement filters">
    <SearchBar :model-value="filters.search" placeholder="Search title or message" @update:model-value="updateFilter('search', $event)" @clear="updateFilter('search', '')" />
    <label class="form-field">
      <span class="form-label">Status</span>
      <select class="form-select" :value="filters.status" @change="updateFilter('status', $event.target.value)">
        <option value="">All statuses</option>
        <option value="published">Published</option>
        <option value="draft">Draft</option>
        <option value="scheduled">Scheduled</option>
        <option value="expired">Expired</option>
        <option value="archived">Archived</option>
      </select>
    </label>
    <label class="form-field">
      <span class="form-label">Category</span>
      <select class="form-select" :value="filters.category" @change="updateFilter('category', $event.target.value)">
        <option value="">All categories</option>
        <option v-for="category in categories" :key="category.value" :value="category.value">{{ category.label }}</option>
      </select>
    </label>
    <button class="btn btn--ghost" type="button" :disabled="!hasFilters" @click="$emit('clear')">
      <RotateCcw :size="16" aria-hidden="true" /> Clear
    </button>
  </section>
</template>

<script setup>
import { RotateCcw } from '@lucide/vue'
import { computed } from 'vue'
import SearchBar from '../common/SearchBar.vue'

const props = defineProps({
  filters: { type: Object, required: true },
  categories: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:filters', 'clear'])
const hasFilters = computed(() => Object.values(props.filters).some(Boolean))
function updateFilter(key, value) { emit('update:filters', { ...props.filters, [key]: value }) }
</script>

<style scoped>
.announcement-filters { display: grid; grid-template-columns: minmax(240px, 1fr) minmax(150px, 190px) minmax(170px, 210px) auto; align-items: end; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
.announcement-filters :deep(.search-bar) { max-width: none; }
@media (max-width: 850px) { .announcement-filters { grid-template-columns: repeat(2, minmax(0, 1fr)); } .announcement-filters :deep(.search-bar) { grid-column: 1 / -1; } }
@media (max-width: 540px) { .announcement-filters { grid-template-columns: 1fr; } .announcement-filters :deep(.search-bar) { grid-column: auto; } }
</style>
