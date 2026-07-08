<template>
  <nav class="pagination" aria-label="Pagination">
    <button
      class="btn btn--secondary btn--sm"
      type="button"
      aria-label="Previous page"
      :disabled="currentPage <= 1"
      @click="$emit('update:currentPage', currentPage - 1)"
    >
      Previous
    </button>

    <span class="pagination__status">
      Page {{ currentPage }} of {{ normalizedTotalPages }}
    </span>

    <button
      class="btn btn--secondary btn--sm"
      type="button"
      aria-label="Next page"
      :disabled="currentPage >= normalizedTotalPages"
      @click="$emit('update:currentPage', currentPage + 1)"
    >
      Next
    </button>
  </nav>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: {
    type: Number,
    default: 1,
  },
  totalPages: {
    type: Number,
    default: 1,
  },
})

defineEmits(['update:currentPage'])

const normalizedTotalPages = computed(() => Math.max(1, props.totalPages))
</script>

<!--
src/components: Reusable pagination control shared across data-backed pages.
-->