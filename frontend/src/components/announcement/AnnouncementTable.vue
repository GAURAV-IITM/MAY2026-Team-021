<template>
  <div class="announcement-records">
    <div class="announcement-records__desktop">
      <DataTable :columns="columns" :rows="announcements" aria-label="Library announcements">
        <template #cell-title="{ row }">
          <div class="announcement-records__title"><strong>{{ row.title }}</strong><span v-if="row.priority === 'important'" class="badge badge--warning">Important</span><small>{{ truncate(row.body, 76) }}</small></div>
        </template>
        <template #cell-category="{ value }">{{ labelFor(categories, value) }}</template>
        <template #cell-audience="{ value }">{{ labelFor(audiences, value) }}</template>
        <template #cell-status="{ value }"><span class="badge" :class="statusClass(value)">{{ formatLabel(value) }}</span></template>
        <template #cell-timeline="{ row }"><div class="announcement-records__date"><span>{{ timelineLabel(row) }}</span><small>{{ formatDate(timelineDate(row)) }}</small><small v-if="row.expiresAt">Expires {{ formatDate(row.expiresAt) }}</small></div></template>
        <template #cell-createdBy="{ row }">{{ row.createdBy?.name || 'Unknown' }}</template>
        <template #actions="{ row }"><AnnouncementActionMenu :announcement="row" @action="$emit('action', row, $event)" /></template>
        <template #empty><slot name="empty">No announcements match the selected filters.</slot></template>
      </DataTable>
    </div>

    <div class="announcement-records__mobile">
      <slot v-if="announcements.length === 0" name="empty">No announcements match the selected filters.</slot>
      <article v-for="announcement in announcements" :key="announcement.id">
        <header><div class="announcement-records__badges"><span class="badge" :class="statusClass(announcement.status)">{{ formatLabel(announcement.status) }}</span><span class="badge announcement-records__category">{{ labelFor(categories, announcement.category) }}</span></div><AnnouncementActionMenu :announcement="announcement" @action="$emit('action', announcement, $event)" /></header>
        <h2>{{ announcement.title }}</h2>
        <p>{{ truncate(announcement.body, 150) }}</p>
        <dl><div><dt>Audience</dt><dd>{{ labelFor(audiences, announcement.audience) }}</dd></div><div><dt>{{ timelineLabel(announcement) }}</dt><dd>{{ formatDate(timelineDate(announcement)) }}</dd></div><div><dt>Created by</dt><dd>{{ announcement.createdBy?.name || 'Unknown' }}</dd></div><div><dt>Priority</dt><dd>{{ formatLabel(announcement.priority) }}</dd></div></dl>
      </article>
    </div>
  </div>
</template>

<script setup>
import DataTable from '../common/DataTable.vue'
import AnnouncementActionMenu from './AnnouncementActionMenu.vue'

defineProps({
  announcements: { type: Array, default: () => [] },
  categories: { type: Array, default: () => [] },
  audiences: { type: Array, default: () => [] },
})
defineEmits(['action'])
const columns = [
  { key: 'title', label: 'Announcement' },
  { key: 'category', label: 'Category' },
  { key: 'audience', label: 'Audience' },
  { key: 'status', label: 'Status' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'createdBy', label: 'Created by' },
]
function labelFor(options, value) { return options.find((item) => item.value === value)?.label || formatLabel(value) }
function formatLabel(value) { return String(value || 'Not set').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function truncate(value, length) { const text = String(value || ''); return text.length > length ? `${text.slice(0, length).trim()}...` : text }
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value)) : 'Not set' }
function timelineDate(announcement) {
  if (announcement.status === 'scheduled') return announcement.scheduledAt
  if (announcement.status === 'published' || announcement.status === 'expired') return announcement.publishedAt
  if (announcement.status === 'archived') return announcement.archivedAt
  return announcement.updatedAt
}
function timelineLabel(announcement) {
  if (announcement.status === 'scheduled') return 'Scheduled'
  if (announcement.status === 'published' || announcement.status === 'expired') return 'Published'
  if (announcement.status === 'archived') return 'Archived'
  return 'Updated'
}
function statusClass(status) {
  if (status === 'published') return 'badge--success'
  if (status === 'scheduled') return 'announcement-records__scheduled'
  if (status === 'expired') return 'announcement-records__expired'
  if (status === 'archived') return 'badge--inactive'
  return 'badge--warning'
}
</script>

<style scoped>
.announcement-records__title, .announcement-records__date { display: grid; gap: 2px; }
.announcement-records__title { min-width: 250px; }
.announcement-records__title > strong { display: flex; align-items: center; gap: var(--space-2); }
.announcement-records__title .badge { width: max-content; margin-top: var(--space-1); }
.announcement-records__title small, .announcement-records__date small { color: var(--color-text-muted); }
.announcement-records__scheduled { background: var(--color-info-light); color: var(--color-info); }
.announcement-records__expired { background: var(--color-warning-light); color: var(--color-warning); }
.announcement-records__mobile { display: none; }
@media (max-width: 700px) {
  .announcement-records__desktop { display: none; }
  .announcement-records__mobile { display: grid; gap: var(--space-3); }
  .announcement-records__mobile article { padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
  .announcement-records__mobile header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
  .announcement-records__badges { display: flex; flex-wrap: wrap; gap: var(--space-2); }
  .announcement-records__category { background: var(--color-surface-secondary); color: var(--color-text-secondary); }
  .announcement-records__mobile h2 { margin: var(--space-3) 0 var(--space-2); font-size: var(--font-size-h5); }
  .announcement-records__mobile p { margin: 0; color: var(--color-text-muted); }
  .announcement-records__mobile dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: var(--space-4) 0 0; padding-top: var(--space-3); border-top: 1px solid var(--color-divider); }
  .announcement-records__mobile dt { color: var(--color-text-muted); font-size: var(--font-size-caption); }
  .announcement-records__mobile dd { margin: 2px 0 0; font-weight: var(--font-weight-medium); }
}
</style>
