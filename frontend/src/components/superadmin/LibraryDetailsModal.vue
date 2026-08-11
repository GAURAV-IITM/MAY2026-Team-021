<template>
  <Modal
    :is-open="isOpen"
    title="Library Details"
    title-id="library-details-title"
    @close="$emit('close')"
  >
    <div v-if="library" class="library-details">
      <header class="library-details__header">
        <div>
          <span class="text-label text-muted">{{ library.code }}</span>
          <h3 class="text-h3 m-0">{{ library.name }}</h3>
        </div>
        <span class="badge" :class="statusClass">{{ formatLabel(library.status) }}</span>
      </header>

      <dl class="library-details__grid">
        <div><dt>Contact Email</dt><dd>{{ library.contactEmail }}</dd></div>
        <div><dt>Contact Phone</dt><dd>{{ library.contactPhone || 'Not provided' }}</dd></div>
        <div><dt>Location</dt><dd>{{ location }}</dd></div>
        <div><dt>Timezone</dt><dd>{{ library.timezone }}</dd></div>
        <div><dt>Students</dt><dd>{{ library.studentCount }}</dd></div>
        <div><dt>Physical Seats</dt><dd>{{ library.seatCount }}</dd></div>
        <div><dt>Active Memberships</dt><dd>{{ library.membershipCount }}</dd></div>
        <div><dt>Created</dt><dd>{{ formatDate(library.createdAt) }}</dd></div>
      </dl>

      <section v-if="library.status === 'suspended'" class="library-details__suspension">
        <strong>Suspension</strong>
        <p class="m-0">{{ library.suspensionReason }}</p>
        <small>{{ formatDate(library.suspendedAt, true) }}</small>
      </section>

      <section class="library-details__owner" aria-labelledby="library-owner-title">
        <div>
          <h4 id="library-owner-title" class="m-0">Primary Owner</h4>
          <p class="text-small text-muted m-0">
            {{ library.ownerName || 'No owner assigned' }}
            <template v-if="library.owner?.email"> - {{ library.owner.email }}</template>
          </p>
        </div>
        <form class="library-details__owner-form" @submit.prevent="assignOwner">
          <label class="form-label" for="details-owner">Assign eligible owner</label>
          <div class="library-details__owner-controls">
            <select id="details-owner" v-model="ownerId" class="form-select">
              <option value="">Select owner</option>
              <option v-for="owner in owners" :key="owner.id" :value="owner.id">
                {{ owner.name }} - {{ owner.email }}
              </option>
            </select>
            <button class="btn btn--primary" type="submit" :disabled="!ownerId || isSaving">
              {{ isSaving ? 'Assigning...' : 'Assign' }}
            </button>
          </div>
        </form>
      </section>

      <div v-if="serverError" class="alert alert--danger" role="alert">{{ serverError }}</div>
    </div>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="$emit('close')">
        Close
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  library: { type: Object, default: null },
  owners: { type: Array, default: () => [] },
  isSaving: { type: Boolean, default: false },
  serverError: { type: String, default: '' },
})
const emit = defineEmits(['close', 'assign-owner'])
const ownerId = ref('')

const location = computed(() => {
  const address = [
    props.library?.addressLine,
    props.library?.city,
    props.library?.state,
    props.library?.postalCode,
  ].filter(Boolean)
  return address.join(', ') || 'Not provided'
})
const statusClass = computed(() => {
  if (props.library?.status === 'active') return 'badge--success'
  if (props.library?.status === 'suspended') return 'badge--inactive'
  return 'badge--pending'
})

function formatLabel(value) {
  return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatDate(value, includeTime = false) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    ...(includeTime ? { hour: 'numeric', minute: '2-digit' } : {}),
  }).format(new Date(value))
}

function assignOwner() {
  if (!ownerId.value) return
  emit('assign-owner', {
    ownerId: ownerId.value,
    expectedUpdatedAt: props.library?.updatedAt,
  })
}

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) ownerId.value = ''
})
</script>

<style scoped>
.library-details { display: grid; gap: var(--space-5); }
.library-details__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); }
.library-details__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); margin: 0; }
.library-details__grid div { display: grid; gap: var(--space-1); padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-border); }
.library-details dt { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.library-details dd { margin: 0; overflow-wrap: anywhere; font-weight: var(--font-weight-medium); }
.library-details__suspension { display: grid; gap: var(--space-2); padding: var(--space-4); border-left: 3px solid var(--color-danger); background: var(--color-danger-light); }
.library-details__suspension small { color: var(--color-text-muted); }
.library-details__owner { display: grid; gap: var(--space-4); padding-top: var(--space-2); }
.library-details__owner-form { display: grid; gap: var(--space-2); }
.library-details__owner-controls { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--space-2); }

@media (max-width: 560px) {
  .library-details__grid { grid-template-columns: 1fr; }
  .library-details__owner-controls { grid-template-columns: 1fr; }
}
</style>
