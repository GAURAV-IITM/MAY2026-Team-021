<template>
  <Modal
    :is-open="Boolean(request)"
    :title="request?.status === 'pending' ? 'Review Seat Request' : 'Seat Request Details'"
    title-id="seat-request-review-title"
    @close="handleClose"
  >
    <div v-if="request" class="request-review">
      <header class="request-review__student">
        <div>
          <span class="text-small text-muted">Student</span>
          <strong>{{ request.studentName }}</strong>
          <span class="text-small text-muted">{{ request.studentEmail }}</span>
        </div>
        <span class="badge" :class="statusClass(request.status)">
          {{ formatLabel(request.status) }}
        </span>
      </header>

      <dl class="request-review__details">
        <div><dt>Current Seat</dt><dd>{{ request.currentSeatNumber || 'Not assigned' }}</dd></div>
        <div><dt>Preferred Seat</dt><dd>{{ request.preferredSeatNumber || 'Any seat' }}</dd></div>
        <div><dt>Preferred Floor</dt><dd>{{ request.preferredFloor ? `Floor ${request.preferredFloor}` : 'Any floor' }}</dd></div>
        <div><dt>Preferred Shift</dt><dd>{{ formatLabel(request.preferredShiftName) }}</dd></div>
        <div><dt>Submitted</dt><dd>{{ formatDateTime(request.submittedAt) }}</dd></div>
        <div v-if="request.resolvedAt"><dt>Resolved</dt><dd>{{ formatDateTime(request.resolvedAt) }}</dd></div>
      </dl>

      <section class="request-review__reason" aria-labelledby="request-reason-title">
        <h3 id="request-reason-title" class="text-label text-muted m-0">Student's Reason</h3>
        <p class="m-0">{{ request.reason }}</p>
      </section>

      <template v-if="request.status === 'pending'">
        <div class="alert alert--info request-review__notice" role="note">
          Approval records your decision only. Update the student's seat or shift separately in Student Management.
        </div>

        <div class="form-group">
          <label class="form-label" for="seat-request-admin-note">
            Administrator Note
            <span class="text-small text-muted">(required when rejecting)</span>
          </label>
          <textarea
            id="seat-request-admin-note"
            v-model.trim="adminNote"
            class="form-textarea"
            rows="4"
            placeholder="Add a response for the student"
          ></textarea>
          <span v-if="validationMessage" class="form-error">{{ validationMessage }}</span>
        </div>
      </template>

      <section v-else class="request-review__response" aria-labelledby="admin-response-title">
        <h3 id="admin-response-title" class="text-label text-muted m-0">Administrator Response</h3>
        <p class="m-0">{{ request.adminNote || 'No note was added.' }}</p>
        <span v-if="request.reviewedBy" class="text-small text-muted">
          Reviewed by {{ request.reviewedBy.name }}
        </span>
      </section>
    </div>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="handleClose">
        Close
      </button>
      <template v-if="request?.status === 'pending'">
        <button class="btn btn--danger" type="button" :disabled="isSaving" @click="submitDecision('rejected')">
          {{ isSaving ? 'Saving...' : 'Reject' }}
        </button>
        <button class="btn btn--primary" type="button" :disabled="isSaving" @click="submitDecision('approved')">
          {{ isSaving ? 'Saving...' : 'Approve' }}
        </button>
      </template>
    </template>
  </Modal>
</template>

<script setup>
import { ref, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  request: { type: Object, default: null },
  isSaving: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'review'])
const adminNote = ref('')
const validationMessage = ref('')

watch(
  () => props.request,
  (request) => {
    adminNote.value = request?.adminNote || ''
    validationMessage.value = ''
  },
  { immediate: true },
)

function formatLabel(value) {
  return String(value || '-')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function statusClass(status) {
  return {
    approved: 'badge--success',
    pending: 'badge--warning',
    rejected: 'badge--cancelled',
    cancelled: 'badge--inactive',
  }[status] || 'badge--inactive'
}

function handleClose() {
  if (!props.isSaving) emit('close')
}

function submitDecision(decision) {
  if (decision === 'rejected' && adminNote.value.length < 5) {
    validationMessage.value = 'Add a short reason before rejecting this request.'
    return
  }

  validationMessage.value = ''
  emit('review', { decision, adminNote: adminNote.value })
}
</script>

<style scoped>
.request-review { display: grid; gap: var(--space-5); }
.request-review__student { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); }
.request-review__student > div { display: grid; gap: var(--space-1); min-width: 0; }
.request-review__student span { overflow-wrap: anywhere; }
.request-review__details { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); margin: 0; }
.request-review__details div { display: grid; gap: var(--space-1); min-width: 0; }
.request-review__details dt { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.request-review__details dd { margin: 0; font-weight: var(--font-weight-medium); overflow-wrap: anywhere; }
.request-review__reason, .request-review__response { display: grid; gap: var(--space-2); padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-surface-secondary); }
.request-review__response { border-left: 3px solid var(--color-primary); }
.request-review__notice { font-size: var(--font-size-sm); }
@media (max-width: 560px) { .request-review__details { grid-template-columns: 1fr; } }
</style>
