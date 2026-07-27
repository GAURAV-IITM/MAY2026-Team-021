<template>
  <Modal
    :is-open="isOpen"
    title="Manage Floors"
    title-id="floor-management-title"
    @close="$emit('close')"
  >
    <div class="floor-manager">
      <form class="floor-manager__form" @submit.prevent="submit">
        <div class="form-field" :class="{ 'form-field--error': errors.name }">
          <label class="form-label" for="floor-name">Floor Name</label>
          <input id="floor-name" v-model.trim="form.name" class="form-control" placeholder="Floor 2" />
          <p v-if="errors.name" class="form-help">{{ errors.name }}</p>
        </div>
        <div class="form-field" :class="{ 'form-field--error': errors.code }">
          <label class="form-label" for="floor-code">Code</label>
          <input id="floor-code" v-model.trim="form.code" class="form-control" placeholder="F2" />
          <p v-if="errors.code" class="form-help">{{ errors.code }}</p>
        </div>
        <div class="form-field">
          <label class="form-label" for="floor-level">Level</label>
          <input id="floor-level" v-model.number="form.levelNumber" class="form-control" type="number" />
        </div>
        <div class="form-field">
          <label class="form-label" for="floor-sort">Sort Order</label>
          <input id="floor-sort" v-model.number="form.sortOrder" class="form-control" type="number" min="0" />
        </div>
        <label class="checkbox floor-manager__active">
          <input v-model="form.isActive" type="checkbox" />
          <span>Active floor</span>
        </label>
        <div class="floor-manager__form-actions">
          <button v-if="editingId" class="btn btn--secondary btn--sm" type="button" @click="resetForm">
            Cancel Edit
          </button>
          <button class="btn btn--primary btn--sm" type="submit" :disabled="isSubmitting">
            {{ editingId ? 'Save Floor' : 'Add Floor' }}
          </button>
        </div>
      </form>

      <div class="floor-manager__list">
        <article v-for="floor in floors" :key="floor.id" class="floor-manager__row">
          <div>
            <strong>{{ floor.name }}</strong>
            <span>{{ floor.code }} · {{ floor.seatCount }} seats</span>
          </div>
          <span class="badge" :class="floor.isActive ? 'badge--success' : 'badge--pending'">
            {{ floor.isActive ? 'Active' : 'Inactive' }}
          </span>
          <div>
            <button class="btn btn--outline btn--sm" type="button" @click="editFloor(floor)">
              <Pencil :size="14" aria-hidden="true" /> Edit
            </button>
            <button class="btn btn--danger btn--sm" type="button" @click="pendingDelete = floor">
              <Trash2 :size="14" aria-hidden="true" /> Delete
            </button>
          </div>
        </article>
        <p v-if="floors.length === 0" class="text-small text-muted m-0">
          No floors have been created.
        </p>
      </div>
    </div>
  </Modal>

  <ConfirmDialog
    :is-open="Boolean(pendingDelete)"
    title="Delete Floor"
    :message="`Delete ${pendingDelete?.name || 'this floor'}? Floors containing seats cannot be deleted.`"
    confirm-label="Delete"
    confirming-label="Deleting"
    :is-confirming="isSubmitting"
    @cancel="pendingDelete = null"
    @confirm="confirmDelete"
  />
</template>

<script setup>
import { Pencil, Trash2 } from '@lucide/vue'
import { reactive, ref } from 'vue'

import ConfirmDialog from '../common/ConfirmDialog.vue'
import Modal from '../common/Modal.vue'

defineProps({
  isOpen: { type: Boolean, default: false },
  floors: { type: Array, default: () => [] },
  isSubmitting: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'create', 'update', 'delete'])
const editingId = ref('')
const pendingDelete = ref(null)
const form = reactive({
  name: '',
  code: '',
  levelNumber: 1,
  sortOrder: 1,
  isActive: true,
})
const errors = reactive({})

function resetForm() {
  editingId.value = ''
  Object.assign(form, {
    name: '',
    code: '',
    levelNumber: 1,
    sortOrder: 1,
    isActive: true,
  })
  Object.keys(errors).forEach((key) => delete errors[key])
}

function editFloor(floor) {
  editingId.value = floor.id
  Object.assign(form, {
    name: floor.name,
    code: floor.code,
    levelNumber: floor.levelNumber ?? 1,
    sortOrder: floor.sortOrder,
    isActive: floor.isActive,
  })
}

function submit() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (!form.name) errors.name = 'Floor name is required.'
  if (!form.code) errors.code = 'Floor code is required.'
  if (Object.keys(errors).length) return
  const payload = {
    name: form.name,
    code: form.code.toUpperCase(),
    levelNumber: Number(form.levelNumber),
    sortOrder: Number(form.sortOrder),
    isActive: form.isActive,
  }
  emit(editingId.value ? 'update' : 'create', editingId.value, payload)
  resetForm()
}

function confirmDelete() {
  emit('delete', pendingDelete.value.id)
  pendingDelete.value = null
}
</script>

<style scoped>
.floor-manager { display: grid; gap: var(--space-5); }
.floor-manager__form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); padding-bottom: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.floor-manager__active { align-self: center; }
.floor-manager__form-actions { display: flex; justify-content: flex-end; gap: var(--space-2); }
.floor-manager__list { display: grid; gap: var(--space-2); max-height: 320px; overflow-y: auto; }
.floor-manager__row { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; align-items: center; gap: var(--space-3); padding: var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.floor-manager__row > div:first-child { display: grid; }
.floor-manager__row > div:first-child span { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.floor-manager__row > div:last-child { display: flex; gap: var(--space-2); }
.form-field--error .form-help { color: var(--color-danger); }
@media (max-width: 640px) {
  .floor-manager__form { grid-template-columns: 1fr; }
  .floor-manager__row { grid-template-columns: minmax(0, 1fr) auto; }
  .floor-manager__row > div:last-child { grid-column: 1 / -1; }
}
</style>
