<template>
  <section class="seat-filters card" aria-label="Seat filters">
    <div class="seat-filters__field">
      <label class="form-label" for="seat-filter-floor">Floor</label>
      <select
        id="seat-filter-floor"
        class="form-select"
        :value="filters.floor"
        @change="emitUpdate('floor', $event.target.value)"
      >
        <option value="">All floors</option>
        <option
          v-for="floor in floors"
          :key="floor"
          :value="String(floor)"
        >
          Floor {{ floor }}
        </option>
      </select>
    </div>

    <div class="seat-filters__field">
      <label class="form-label" for="seat-filter-status">Status</label>
      <select
        id="seat-filter-status"
        class="form-select"
        :value="filters.status"
        @change="emitUpdate('status', $event.target.value)"
      >
        <option value="">All</option>
        <option value="available">Available</option>
        <option value="occupied">Occupied</option>
        <option value="maintenance">Maintenance</option>
        <option value="blocked">Blocked</option>
      </select>
    </div>

    <div class="seat-filters__search">
      <label class="form-label" for="seat-filter-search">Search</label>
      <SearchBar
        id="seat-filter-search"
        :model-value="filters.search"
        placeholder="Search seat number, notes, or floor"
        @update:model-value="emitUpdate('search', $event)"
        @clear="emitUpdate('search', '')"
      />
    </div>

    <button
      class="btn btn--secondary seat-filters__reset"
      type="button"
      :disabled="!hasActiveFilters"
      @click="$emit('reset')"
    >
      <RotateCcw :size="16" aria-hidden="true" /> Reset
    </button>
  </section>
</template>

<script setup>
import { RotateCcw } from '@lucide/vue'

import SearchBar from '../common/SearchBar.vue'

defineProps({
  filters: {
    type: Object,
    default: () => ({
      floor: '',
      status: '',
      search: '',
    }),
  },
  floors: {
    type: Array,
    default: () => [],
  },
  hasActiveFilters: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update', 'reset'])

function emitUpdate(filterName, value) {
  emit('update', filterName, value)
}
</script>

<style scoped>
.seat-filters {
  position: sticky;
  z-index: 5;
  top: var(--space-4);
  display: grid;
  grid-template-columns: minmax(140px, 0.6fr) minmax(160px, 0.7fr) minmax(260px, 1fr) auto;
  gap: var(--space-4);
  align-items: end;
  padding: var(--space-4);
}

.seat-filters__field,
.seat-filters__search {
  display: grid;
  gap: var(--space-2);
}

.seat-filters__search :deep(.search-bar) {
  max-width: none;
}

.seat-filters__reset {
  white-space: nowrap;
}

@media (max-width: 980px) {
  .seat-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .seat-filters__search {
    grid-column: 1 / -1;
  }
}

@media (max-width: 560px) {
  .seat-filters {
    position: static;
    grid-template-columns: 1fr;
  }

  .seat-filters__reset {
    justify-content: center;
    width: 100%;
  }
}
</style>
