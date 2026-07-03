<template>
  <section class="data-table" aria-label="Data table">
    <header class="data-table__toolbar">
      <SearchBar placeholder="Search table" />
      <div class="data-table__actions">
        <button class="btn btn--secondary btn--sm" type="button">Filter</button>
        <button class="btn btn--secondary btn--sm" type="button">Sort</button>
      </div>
    </header>

    <div class="data-table__scroll">
      <table class="table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key" scope="col">
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="rows.length === 0">
            <td :colspan="columns.length">
              <div class="table-empty">No rows to display</div>
            </td>
          </tr>
          <tr v-for="(row, rowIndex) in rows" :key="rowIndex">
            <td v-for="column in columns" :key="column.key">
              {{ row[column.key] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer class="data-table__footer">
      <span class="text-small text-muted">Pagination placeholder</span>
      <Pagination />
    </footer>
  </section>
</template>

<script setup>
import Pagination from './Pagination.vue'
import SearchBar from './SearchBar.vue'

defineProps({
  columns: {
    type: Array,
    default: () => [
      { key: 'name', label: 'Name' },
      { key: 'status', label: 'Status' },
    ],
  },
  rows: {
    type: Array,
    default: () => [],
  },
})
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add typed column definitions, sorting, empty states, and row actions.
- Connect filtering, sorting, search, and pagination when feature pages are implemented.
-->
