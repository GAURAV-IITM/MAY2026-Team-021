<template>
  <Modal
    :is-open="isOpen"
    title="Owner Details"
    title-id="owner-detail-title"
    @close="$emit('close')"
  >
    <LoadingSpinner v-if="isLoading" label="Loading owner details" />
    <div v-else-if="owner" class="owner-detail">
      <header>
        <div>
          <h3 class="m-0">{{ owner.name }}</h3>
          <p class="m-0 text-muted">{{ owner.email }}</p>
        </div>
        <span class="badge" :class="owner.status === 'active' ? 'badge--success' : owner.status === 'suspended' ? 'badge--inactive' : 'badge--pending'">
          {{ formatLabel(owner.status) }}
        </span>
      </header>
      <dl class="owner-detail__facts">
        <div><dt>Phone</dt><dd>{{ owner.phone || 'Not provided' }}</dd></div>
        <div><dt>Invitation</dt><dd>{{ formatLabel(owner.invitationStatus || 'Not applicable') }}</dd></div>
        <div><dt>Last login</dt><dd>{{ owner.lastLoginAt ? formatDate(owner.lastLoginAt) : 'Never' }}</dd></div>
        <div><dt>Created</dt><dd>{{ formatDate(owner.createdAt) }}</dd></div>
      </dl>
      <section>
        <h3 class="text-h5">Assignment History</h3>
        <p v-if="!owner.assignmentHistory?.length" class="text-muted m-0">No accepted assignments yet.</p>
        <ol v-else class="owner-detail__history">
          <li v-for="assignment in owner.assignmentHistory" :key="`${assignment.libraryId}-${assignment.joinedAt}`">
            <div><strong>{{ assignment.libraryName }}</strong><span>{{ formatLabel(assignment.membershipStatus) }}</span></div>
            <small>{{ formatDate(assignment.joinedAt) }}<template v-if="assignment.leftAt"> to {{ formatDate(assignment.leftAt) }}</template></small>
          </li>
        </ol>
      </section>
    </div>
    <template #footer>
      <button class="btn btn--secondary" type="button" @click="$emit('close')">Close</button>
    </template>
  </Modal>
</template>

<script setup>
import LoadingSpinner from '../common/LoadingSpinner.vue'
import Modal from '../common/Modal.vue'

defineProps({
  isOpen: { type: Boolean, default: false },
  owner: { type: Object, default: null },
  isLoading: { type: Boolean, default: false },
})

defineEmits(['close'])

function formatLabel(value) {
  return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value))
}
</script>

<style scoped>
.owner-detail { display: grid; gap: var(--space-5); }
.owner-detail > header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); }
.owner-detail__facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); margin: 0; }
.owner-detail__facts div { padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-border); }
.owner-detail__facts dt { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.owner-detail__facts dd { margin: var(--space-1) 0 0; font-weight: var(--font-weight-medium); }
.owner-detail__history { display: grid; gap: var(--space-3); margin: 0; padding: 0; list-style: none; }
.owner-detail__history li { display: grid; gap: var(--space-1); padding: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.owner-detail__history li div { display: flex; justify-content: space-between; gap: var(--space-3); }
.owner-detail__history span, .owner-detail__history small { color: var(--color-text-muted); }
@media (max-width: 560px) { .owner-detail__facts { grid-template-columns: 1fr; } }
</style>
