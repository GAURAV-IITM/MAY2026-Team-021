<template>
  <div class="status-distribution">
    <div class="status-distribution__bar" aria-hidden="true">
      <span
        v-for="item in items"
        :key="item.status"
        :class="`status-distribution__segment--${item.status}`"
        :style="{ width: getWidth(item.count) }"
      ></span>
    </div>

    <ul class="status-distribution__list">
      <li v-for="item in items" :key="item.status">
        <span
          class="status-distribution__dot"
          :class="`status-distribution__dot--${item.status}`"
          aria-hidden="true"
        ></span>
        <span>{{ formatLabel(item.status) }}</span>
        <strong>{{ item.count }}</strong>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})

const total = computed(() => {
  return props.items.reduce((sum, item) => sum + Number(item.count || 0), 0)
})

function getWidth(value) {
  if (total.value === 0) return '0%'

  return `${(Number(value || 0) / total.value) * 100}%`
}

function formatLabel(value) {
  return String(value || '')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}
</script>

<style scoped>
.status-distribution {
  display: grid;
  gap: var(--space-5);
}

.status-distribution__bar {
  display: flex;
  height: 10px;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-surface-secondary);
}

.status-distribution__bar span {
  height: 100%;
}

.status-distribution__segment--active,
.status-distribution__dot--active {
  background: var(--color-success);
}

.status-distribution__segment--pending,
.status-distribution__dot--pending,
.status-distribution__segment--invited,
.status-distribution__dot--invited {
  background: var(--color-warning);
}

.status-distribution__segment--suspended,
.status-distribution__dot--suspended {
  background: var(--color-danger);
}

.status-distribution__list {
  display: grid;
  gap: var(--space-3);
  padding: 0;
  margin: 0;
  list-style: none;
}

.status-distribution__list li {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.status-distribution__dot {
  width: 9px;
  height: 9px;
  border-radius: var(--radius-pill);
}
</style>
