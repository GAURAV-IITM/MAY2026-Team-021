<template>
  <label class="search-bar">
    <span class="search-bar__icon" aria-hidden="true">/</span>
    <span class="sr-only">Search</span>
    <input
      :value="modelValue"
      type="search"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <kbd class="search-bar__shortcut">{{ shortcut }}</kbd>
    <button
      class="btn btn--ghost btn--icon btn--sm"
      type="button"
      aria-label="Clear search"
      @click="$emit('clear')"
    >
      x
    </button>
  </label>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: 'Search',
  },
  shortcut: {
    type: String,
    default: '/',
  },
})

defineEmits(['update:modelValue', 'clear'])
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add debounced query handling when pages integrate real search behavior.
-->
