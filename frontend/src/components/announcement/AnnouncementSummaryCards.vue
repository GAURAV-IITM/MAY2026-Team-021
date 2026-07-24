<template>
  <section class="announcement-summary" aria-label="Announcement summary">
    <article v-for="item in items" :key="item.label">
      <span :class="`announcement-summary__icon--${item.tone}`">
        <component :is="item.icon" :size="18" aria-hidden="true" />
      </span>
      <div><small>{{ item.label }}</small><strong>{{ item.value }}</strong><p>{{ item.detail }}</p></div>
    </article>
  </section>
</template>

<script setup>
defineProps({ items: { type: Array, default: () => [] } })
</script>

<style scoped>
.announcement-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-3); }
.announcement-summary article { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: start; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
.announcement-summary article > span { display: grid; width: 36px; height: 36px; place-items: center; border-radius: var(--radius-md); background: var(--color-primary-light); color: var(--color-primary); }
.announcement-summary .announcement-summary__icon--success { background: var(--color-success-light); color: var(--color-success); }
.announcement-summary .announcement-summary__icon--warning { background: var(--color-warning-light); color: var(--color-warning); }
.announcement-summary .announcement-summary__icon--info { background: var(--color-info-light); color: var(--color-info); }
.announcement-summary article > div { display: grid; min-width: 0; }
.announcement-summary small, .announcement-summary p { color: var(--color-text-muted); }
.announcement-summary strong { font-size: var(--font-size-h3); line-height: 1.2; }
.announcement-summary p { margin: var(--space-1) 0 0; overflow: hidden; font-size: var(--font-size-caption); text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 900px) { .announcement-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 460px) { .announcement-summary article { padding: var(--space-3); } .announcement-summary strong { font-size: var(--font-size-h4); } }
</style>

