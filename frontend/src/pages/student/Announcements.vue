<template>
  <section class="student-announcements" aria-labelledby="student-announcements-title">
    <header class="announcements-header"><div><p class="text-label text-muted m-0">Library Updates</p><h1 id="student-announcements-title" class="text-h2 announcements-header__title">Announcements</h1><p class="announcements-header__description">Important notices and updates from your library.</p></div><button class="btn btn--secondary" type="button" :disabled="isLoading" @click="loadAnnouncements">{{ isLoading ? 'Refreshing...' : 'Refresh' }}</button></header>
    <div v-if="errorMessage" class="alert alert--danger" role="alert"><span>{{ errorMessage }}</span><button class="btn btn--secondary btn--sm" type="button" @click="loadAnnouncements">Retry</button></div>
    <LoadingSpinner v-if="isLoading && announcements.length === 0" label="Loading announcements" />

    <template v-else>
      <StudentSummaryCards :items="summaryItems" aria-label="Announcement summary" />
      <section class="announcement-toolbar" aria-label="Announcement filters">
        <div class="announcement-tabs" role="group" aria-label="Filter announcements">
          <button v-for="option in filterOptions" :key="option.value" class="announcement-tabs__button" :class="{ 'is-active': filter === option.value }" type="button" @click="filter = option.value">{{ option.label }} <span>{{ option.count }}</span></button>
        </div>
      </section>
      <section class="announcement-list" aria-live="polite">
        <article v-for="announcement in filteredAnnouncements" :key="announcement.id" class="announcement-card" :class="{ 'is-unread': !announcement.isRead }">
          <div class="announcement-card__marker" aria-hidden="true"></div>
          <div class="announcement-card__content">
            <header><div class="announcement-card__badges"><span class="badge badge--category">{{ formatLabel(announcement.category) }}</span><span v-if="announcement.priority === 'important'" class="badge badge--warning">Important</span><span v-if="!announcement.isRead" class="badge badge--new">New</span></div><time :datetime="announcement.publishedAt">{{ formatDate(announcement.publishedAt) }}</time></header>
            <h2>{{ announcement.title }}</h2><p>{{ announcement.body }}</p>
            <button v-if="!announcement.isRead" class="btn btn--ghost btn--sm" type="button" :disabled="isSaving" @click="markRead(announcement.id)">Mark as Read</button>
          </div>
        </article>
        <div v-if="filteredAnnouncements.length === 0" class="announcement-empty"><strong>No announcements found</strong><p class="text-muted m-0">There are no announcements matching this filter.</p></div>
      </section>
    </template>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import StudentSummaryCards from '../../components/student/StudentSummaryCards.vue'
import { useAuthStore } from '../../stores/authStore'
import { useStudentPortalStore } from '../../stores/studentPortalStore'

const authStore = useAuthStore()
const portalStore = useStudentPortalStore()
const { currentUser } = storeToRefs(authStore)
const { announcements, isLoading, isSaving, errorMessage } = storeToRefs(portalStore)
const filter = ref('all')
const unreadCount = computed(() => announcements.value.filter((item) => !item.isRead).length)
const importantCount = computed(() => announcements.value.filter((item) => item.priority === 'important').length)
const filterOptions = computed(() => [{ label: 'All', value: 'all', count: announcements.value.length }, { label: 'Unread', value: 'unread', count: unreadCount.value }, { label: 'Important', value: 'important', count: importantCount.value }])
const filteredAnnouncements = computed(() => announcements.value.filter((item) => filter.value === 'all' || (filter.value === 'unread' && !item.isRead) || (filter.value === 'important' && item.priority === 'important')))
const summaryItems = computed(() => [
  { label: 'All Updates', value: announcements.value.length, detail: 'Library announcements', icon: 'A', tone: 'primary' },
  { label: 'Unread', value: unreadCount.value, detail: 'Waiting for you', icon: 'U', tone: unreadCount.value ? 'warning' : 'success' },
  { label: 'Important', value: importantCount.value, detail: 'Priority notices', icon: 'I', tone: 'danger' },
  { label: 'Read', value: announcements.value.length - unreadCount.value, detail: 'Updates reviewed', icon: 'R', tone: 'success' },
])

function formatLabel(value) { return String(value || '-').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) }
async function loadAnnouncements() { try { await portalStore.fetchAnnouncements(currentUser.value?.id) } catch { /* Store-owned errors are rendered above. */ } }
async function markRead(id) { try { await portalStore.markAnnouncementRead(currentUser.value?.id, id) } catch { /* Store-owned errors are rendered above. */ } }
onMounted(loadAnnouncements)
</script>

<style scoped>
.student-announcements { display: grid; gap: var(--space-6); }
.announcements-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.announcements-header__title { margin: var(--space-1) 0 0; }
.announcements-header__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.announcement-toolbar { display: flex; justify-content: space-between; }
.announcement-tabs { display: inline-flex; gap: var(--space-1); padding: var(--space-1); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); }
.announcement-tabs__button { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-2) var(--space-3); border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--color-text-muted); cursor: pointer; font: inherit; font-weight: var(--font-weight-medium); }
.announcement-tabs__button span { display: inline-flex; min-width: 22px; justify-content: center; padding: 1px var(--space-1); border-radius: var(--radius-pill); background: var(--color-surface-secondary); font-size: var(--font-size-xs); }
.announcement-tabs__button.is-active { background: var(--color-primary); color: var(--color-text-inverse); }
.announcement-list { display: grid; gap: var(--space-3); }
.announcement-card { display: grid; grid-template-columns: 4px minmax(0, 1fr); overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); }
.announcement-card__marker { background: var(--color-divider); }
.announcement-card.is-unread .announcement-card__marker { background: var(--color-primary); }
.announcement-card.is-unread { border-color: var(--color-primary); }
.announcement-card__content { display: grid; gap: var(--space-3); padding: var(--space-5); }
.announcement-card__content header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.announcement-card__badges { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.announcement-card .badge--category { background: var(--color-surface-secondary); color: var(--color-text-muted); }
.announcement-card .badge--new { background: var(--color-info-light); color: var(--color-info); }
.announcement-card time { color: var(--color-text-muted); font-size: var(--font-size-sm); white-space: nowrap; }
.announcement-card h2 { margin: 0; font-size: var(--font-size-h5); }
.announcement-card p { margin: 0; color: var(--color-text-muted); line-height: var(--line-height-relaxed); }
.announcement-card .btn { justify-self: start; }
.announcement-empty { display: grid; justify-items: center; gap: var(--space-2); padding: var(--space-8); border: 1px dashed var(--color-border); border-radius: var(--radius-md); text-align: center; }
@media (max-width: 600px) { .announcements-header { flex-direction: column; } .announcements-header .btn { width: 100%; } .announcement-tabs { width: 100%; } .announcement-tabs__button { flex: 1; justify-content: center; } .announcement-card__content header { flex-direction: column; } }
</style>
