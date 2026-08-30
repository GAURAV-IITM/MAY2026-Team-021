<template>
  <label class="search-bar">
    <Search class="search-bar__icon" :size="18" aria-hidden="true" />
    <span class="sr-only">Search</span>
    <input
      :value="modelValue"
      type="search"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <kbd v-if="shortcut && !modelValue" class="search-bar__shortcut">{{ shortcut }}</kbd>
    <button
      v-if="modelValue"
      class="btn btn--ghost btn--icon btn--sm"
      type="button"
      aria-label="Clear search"
      title="Clear search"
      @click="$emit('clear')"
    >
      <X :size="16" aria-hidden="true" />
    </button>
  </label>
</template>

<script setup>
import { Search, X } from '@lucide/vue'

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
    default: '',
  },
})

defineEmits(['update:modelValue', 'clear'])
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add debounced query handling when pages integrate real search behavior.
-->
