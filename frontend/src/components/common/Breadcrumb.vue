<template>
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <ol class="breadcrumb__list">
      <li v-for="item in items" :key="item.label" class="breadcrumb__item">
        <span v-if="item.current" class="breadcrumb__current" aria-current="page">{{
          item.label
        }}</span>
        <a v-else :href="item.href">{{ item.label }}</a>
      </li>
    </ol>
  </nav>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => [
      { label: 'Home', href: '#' },
      { label: 'Current Page', current: true },
    ],
  },
})
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add route-aware breadcrumb generation when page metadata is finalized.
-->
