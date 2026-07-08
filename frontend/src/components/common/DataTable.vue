<template>
  <section class="data-table" :aria-label="ariaLabel">
    <div class="data-table__scroll">
      <table class="table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key" scope="col">
              {{ column.label }}
            </th>

            <th v-if="$slots.actions" scope="col">
              Actions
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-if="rows.length === 0">
            <td :colspan="columnCount">
              <div class="table-empty">
                <slot name="empty">No rows to display</slot>
              </div>
            </td>
          </tr>

          <tr v-for="row in rows" :key="getRowKey(row)">
            <td v-for="column in columns" :key="column.key">
              <slot
                :name="`cell-${column.key}`"
                :row="row"
                :value="row[column.key]"
              >
                {{ row[column.key] }}
              </slot>
            </td>

            <td v-if="$slots.actions">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed, useSlots } from 'vue'

const props = defineProps({
  columns: {
    type: Array,
    default: () => [],
  },
  rows: {
    type: Array,
    default: () => [],
  },
  rowKey: {
    type: String,
    default: 'id',
  },
  ariaLabel: {
    type: String,
    default: 'Data table',
  },
})

const slots = useSlots()

const columnCount = computed(() => {
  return props.columns.length + (slots.actions ? 1 : 0)
})

function getRowKey(row) {
  return row[props.rowKey]
}
</script>

<!--
src/components: Reusable data table shared across data-backed pages.
Feature pages own search, filtering, sorting, pagination, and row actions.
-->