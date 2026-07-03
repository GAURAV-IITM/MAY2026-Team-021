<template>
  <nav class="pagination" aria-label="Pagination">
    <button class="btn btn--secondary btn--sm" type="button" aria-label="Previous page">
      Previous
    </button>
    <span class="pagination__status">Page {{ currentPage }} of {{ totalPages }}</span>
    <button class="btn btn--secondary btn--sm" type="button" aria-label="Next page">Next</button>
  </nav>
</template>

<script setup>
defineProps({
  currentPage: {
    type: Number,
    default: 1,
  },
  totalPages: {
    type: Number,
    default: 1,
  },
})
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Wire controls to real pagination state when data-backed pages are implemented.
-->
