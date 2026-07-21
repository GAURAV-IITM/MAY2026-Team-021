<template>
  <Modal :is-open="isOpen" :title="mode === 'edit' ? 'Edit Announcement' : 'Create Announcement'" title-id="announcement-form-title" @close="close">
    <form class="announcement-form" novalidate @submit.prevent="submit">
      <div class="form-field" :class="{ 'form-field--error': errors.title }">
        <div class="announcement-form__label"><label class="form-label" for="announcement-title">Title</label><small>{{ form.title.length }}/120</small></div>
        <input id="announcement-title" v-model="form.title" class="form-control" maxlength="120" placeholder="Example: Library closed for maintenance" :aria-invalid="Boolean(errors.title)" />
        <p v-if="errors.title" class="form-help">{{ errors.title }}</p>
      </div>

      <div class="form-field" :class="{ 'form-field--error': errors.body }">
        <div class="announcement-form__label"><label class="form-label" for="announcement-body">Message</label><small>{{ form.body.length }}/1000</small></div>
        <textarea id="announcement-body" v-model="form.body" class="form-textarea" maxlength="1000" rows="6" placeholder="Write the complete update students should receive." :aria-invalid="Boolean(errors.body)"></textarea>
        <p v-if="errors.body" class="form-help">{{ errors.body }}</p>
      </div>

      <div class="announcement-form__grid">
        <label class="form-field"><span class="form-label">Category</span><select v-model="form.category" class="form-select"><option v-for="item in categories" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
        <label class="form-field"><span class="form-label">Audience</span><select v-model="form.audience" class="form-select"><option v-for="item in audiences" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
      </div>

      <fieldset class="announcement-form__publication">
        <legend class="form-label">Publication</legend>
        <label><input v-model="form.publication" type="radio" value="draft" /> Save as draft</label>
        <label><input v-model="form.publication" type="radio" value="published" /> Publish now</label>
        <label><input v-model="form.publication" type="radio" value="scheduled" /> Schedule</label>
      </fieldset>

      <div v-if="form.publication === 'scheduled'" class="form-field" :class="{ 'form-field--error': errors.publishedAt }">
        <label class="form-label" for="announcement-publish-at">Publish date and time</label>
        <input id="announcement-publish-at" v-model="form.publishedAt" class="form-control" type="datetime-local" :min="minimumDateTime" />
        <p v-if="errors.publishedAt" class="form-help">{{ errors.publishedAt }}</p>
      </div>

      <div class="announcement-form__grid">
        <label class="form-field"><span class="form-label">Expires on <small>(optional)</small></span><input v-model="form.expiresAt" class="form-control" type="datetime-local" :min="minimumDateTime" /></label>
        <label class="announcement-form__important"><input v-model="form.isImportant" type="checkbox" /><span><strong>Important announcement</strong><small>Highlight this notice for students.</small></span></label>
      </div>
      <p v-if="errors.expiresAt" class="form-help announcement-form__expiry-error">{{ errors.expiresAt }}</p>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSubmitting" @click="close">Cancel</button>
      <button class="btn btn--primary" type="button" :disabled="isSubmitting" @click="submit"><span v-if="isSubmitting" class="btn__loader"></span>{{ isSubmitting ? 'Saving...' : submitLabel }}</button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  mode: { type: String, default: 'create' },
  announcement: { type: Object, default: null },
  categories: { type: Array, default: () => [] },
  audiences: { type: Array, default: () => [] },
  isSubmitting: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'save'])
const form = reactive({ title: '', body: '', category: 'general', audience: 'all', publication: 'published', publishedAt: '', expiresAt: '', isImportant: false })
const errors = reactive({})
const minimumDateTime = computed(() => toLocalInput(new Date()))
const submitLabel = computed(() => {
  if (props.mode === 'edit') return 'Save Changes'
  if (form.publication === 'draft') return 'Save Draft'
  if (form.publication === 'scheduled') return 'Schedule'
  return 'Publish'
})

watch(() => [props.isOpen, props.announcement], ([isOpen]) => { if (isOpen) reset() }, { deep: true })
function toLocalInput(value) {
  if (!value) return ''
  const date = new Date(value)
  const offset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}
function reset() {
  const item = props.announcement
  form.title = item?.title || ''
  form.body = item?.body || ''
  form.category = item?.category || props.categories[0]?.value || 'general'
  form.audience = item?.audience || props.audiences[0]?.value || 'all'
  form.publication = item?.status === 'scheduled' ? 'scheduled' : item?.status === 'draft' || item?.status === 'archived' ? 'draft' : 'published'
  form.publishedAt = item?.status === 'scheduled' ? toLocalInput(item.publishedAt) : ''
  form.expiresAt = toLocalInput(item?.expiresAt)
  form.isImportant = item?.priority === 'important'
  clearErrors()
}
function clearErrors() { Object.keys(errors).forEach((key) => delete errors[key]) }
function validate() {
  clearErrors()
  if (form.title.trim().length < 5) errors.title = 'Enter a title with at least 5 characters.'
  if (form.body.trim().length < 10) errors.body = 'Enter a message with at least 10 characters.'
  if (form.publication === 'scheduled' && !form.publishedAt) errors.publishedAt = 'Select when this announcement should be published.'
  const publishTime = form.publication === 'scheduled' ? new Date(form.publishedAt) : new Date()
  if (form.publication === 'scheduled' && publishTime <= new Date()) errors.publishedAt = 'Scheduled publish time must be in the future.'
  if (form.expiresAt && new Date(form.expiresAt) <= publishTime) errors.expiresAt = 'Expiry must be later than the publish time.'
  return Object.keys(errors).length === 0
}
function submit() {
  if (!validate()) return
  emit('save', {
    title: form.title.trim(),
    body: form.body.trim(),
    category: form.category,
    audience: form.audience,
    priority: form.isImportant ? 'important' : 'normal',
    status: form.publication === 'scheduled' ? 'published' : form.publication,
    publishedAt:
      form.publication === 'scheduled'
        ? form.publishedAt
        : form.publication === 'published'
          ? props.announcement?.publishedAt || null
          : null,
    expiresAt: form.expiresAt || null,
  })
}
function close() { if (!props.isSubmitting) emit('close') }
</script>

<style scoped>
.announcement-form { display: grid; gap: var(--space-5); }
.announcement-form__label { display: flex; justify-content: space-between; gap: var(--space-3); }
.announcement-form__label small, .form-label small { color: var(--color-text-muted); font-weight: var(--font-weight-regular); }
.announcement-form__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
.announcement-form__publication { display: flex; flex-wrap: wrap; gap: var(--space-3); margin: 0; padding: 0; border: 0; }
.announcement-form__publication legend { width: 100%; margin-bottom: var(--space-1); }
.announcement-form__publication label { display: inline-flex; align-items: center; gap: var(--space-2); min-height: 38px; padding: 0 var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-md); cursor: pointer; }
.announcement-form__publication input { width: 16px; min-height: 16px; }
.announcement-form__important { display: flex; align-items: center; gap: var(--space-3); align-self: end; min-height: 40px; cursor: pointer; }
.announcement-form__important input { width: 18px; min-height: 18px; }
.announcement-form__important span { display: grid; }
.announcement-form__important small { color: var(--color-text-muted); }
.form-field--error .form-help, .announcement-form__expiry-error { color: var(--color-danger); }
@media (max-width: 600px) { .announcement-form__grid { grid-template-columns: 1fr; } .announcement-form__publication { display: grid; } }
</style>
