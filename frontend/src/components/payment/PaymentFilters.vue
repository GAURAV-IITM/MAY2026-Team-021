<template>
  <section class="payment-filters card" aria-label="Payment filters">
    <div class="payment-filters__search">
      <SearchBar
        :model-value="search"
        placeholder="Search by student name"
        @update:model-value="$emit('update:search', $event)"
        @clear="$emit('update:search', '')"
      />
    </div>

    <div class="payment-filters__field">
      <label class="form-label" for="payment-month-filter">Month</label>

      <input
        id="payment-month-filter"
        class="form-control"
        type="month"
        :value="month"
        @input="$emit('update:month', $event.target.value)"
      />
    </div>

    <div
  v-if="!hideStatus"
  class="payment-filters__field"
>
      <label class="form-label" for="payment-status-filter">Status</label>

      <select
        id="payment-status-filter"
        class="form-select"
        :value="status"
        @change="$emit('update:status', $event.target.value)"
      >
        <option value="">All statuses</option>
        <option value="paid">Paid</option>
        <option value="partially_paid">Partially Paid</option>
        <option value="unpaid">Unpaid</option>
      </select>
    </div>

    <button
      class="btn btn--secondary payment-filters__clear"
      type="button"
      :disabled="!hasActiveFilters"
      @click="$emit('clear')"
    >
      Clear Filters
    </button>
  </section>
</template>

<script setup>
import SearchBar from '../common/SearchBar.vue'

defineProps({
  search: {
    type: String,
    default: '',
  },
  month: {
    type: String,
    default: '',
  },
  status: {
    type: String,
    default: '',
  },
  hasActiveFilters: {
    type: Boolean,
    default: false,
  },
  hideStatus: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'update:search',
  'update:month',
  'update:status',
  'clear',
])

</script>

<style scoped>
.payment-filters {
  display: grid;
  grid-template-columns:
    minmax(240px, 1fr)
    minmax(160px, 200px)
    minmax(150px, 190px)
    auto;
  align-items: end;
  gap: var(--space-4);
  padding: var(--space-4);
}

.payment-filters__search {
  align-self: end;
}

.payment-filters__search :deep(.search-bar) {
  max-width: none;
}

.payment-filters__field {
  display: grid;
  gap: var(--space-2);
}

.payment-filters__clear {
  white-space: nowrap;
}

@media (max-width: 1000px) {
  .payment-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .payment-filters__search {
    grid-column: 1 / -1;
  }
}

@media (max-width: 640px) {
  .payment-filters {
    grid-template-columns: 1fr;
  }

  .payment-filters__search {
    grid-column: auto;
  }

  .payment-filters__clear {
    width: 100%;
  }
}
</style>
