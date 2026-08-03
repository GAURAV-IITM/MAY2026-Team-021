<template>
  <section class="platform-settings" aria-labelledby="platform-settings-title">
    <header class="platform-settings__header">
      <div>
        <p class="text-label text-muted m-0">System Configuration</p>
        <h1 id="platform-settings-title" class="text-h2 platform-settings__title">
          Platform Settings
        </h1>
        <p class="platform-settings__description">
          Manage approved platform-wide registration and access defaults.
        </p>
      </div>
      <button
        class="btn btn--primary"
        type="submit"
        form="platform-settings-form"
        :disabled="!canSave"
      >
        <Save :size="17" aria-hidden="true" />
        {{ isSaving ? 'Saving...' : 'Save Settings' }}
      </button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>{{ errorTitle }}</strong>
        <p class="m-0">{{ errorMessage }}</p>
        <p v-if="errorRequestId" class="text-small m-0">
          Request ID: {{ errorRequestId }}
        </p>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadSettings">
        <RefreshCw :size="16" aria-hidden="true" />
        Reload
      </button>
    </div>

    <div v-if="isLoading && !hasLoadedSettings" class="platform-settings__loading">
      <LoadingSpinner label="Loading platform settings" />
    </div>

    <form
      v-if="hasLoadedSettings"
      id="platform-settings-form"
      class="platform-settings__form"
      novalidate
      @submit.prevent="handleSave"
    >
      <fieldset class="platform-settings__fieldset" :disabled="isSaving">
        <section class="card settings-section" aria-labelledby="identity-settings-title">
          <header class="settings-section__header">
            <div>
              <h2 id="identity-settings-title">Platform Identity</h2>
              <p>Deployment-managed application identity.</p>
            </div>
            <span class="badge badge--neutral"><LockKeyhole :size="14" /> Read-only</span>
          </header>
          <div class="settings-section__body">
            <div class="form-group">
              <label class="form-label" for="platform-name">Platform Name</label>
              <input
                id="platform-name"
                :value="settings.platformName"
                class="form-input"
                type="text"
                readonly
              />
            </div>
          </div>
        </section>

        <section class="card settings-section" aria-labelledby="registration-settings-title">
          <header class="settings-section__header">
            <div>
              <h2 id="registration-settings-title">Library Registration</h2>
              <p>Control whether new library accounts can be created.</p>
            </div>
          </header>
          <div class="settings-section__body">
            <SettingsToggle
              v-model="form.allowLibraryRegistrations"
              label="Allow library registrations"
              description="Permit new owners to register a library account."
            />
          </div>
        </section>

        <section class="card settings-section" aria-labelledby="access-settings-title">
          <header class="settings-section__header">
            <div>
              <h2 id="access-settings-title">Access Defaults</h2>
              <p>Defaults applied when tokens and libraries are created.</p>
            </div>
          </header>
          <div class="settings-section__body settings-section__grid">
            <div class="form-group">
              <label class="form-label" for="session-timeout">Access-token timeout</label>
              <div class="settings-section__input-suffix">
                <input
                  id="session-timeout"
                  v-model.number="form.sessionTimeoutMinutes"
                  class="form-input"
                  :class="{ 'form-input--error': validationErrors.sessionTimeoutMinutes }"
                  type="number"
                  min="15"
                  max="1440"
                  step="1"
                  required
                  :aria-invalid="Boolean(validationErrors.sessionTimeoutMinutes)"
                  aria-describedby="session-timeout-error"
                  @input="validateForm"
                  @blur="validateForm"
                />
                <span>minutes</span>
              </div>
              <small
                v-if="validationErrors.sessionTimeoutMinutes"
                id="session-timeout-error"
                class="platform-settings__field-error"
              >
                {{ validationErrors.sessionTimeoutMinutes }}
              </small>
            </div>

            <div class="form-group">
              <label class="form-label" for="platform-timezone">Default timezone</label>
              <select
                id="platform-timezone"
                v-model="form.defaultTimezone"
                class="form-select"
                :aria-invalid="Boolean(validationErrors.defaultTimezone)"
                @change="validateForm"
              >
                <option value="Asia/Kolkata">Asia/Kolkata</option>
                <option value="UTC">UTC</option>
                <option value="Asia/Dubai">Asia/Dubai</option>
              </select>
              <small
                v-if="validationErrors.defaultTimezone"
                class="platform-settings__field-error"
              >
                {{ validationErrors.defaultTimezone }}
              </small>
            </div>
          </div>
        </section>
      </fieldset>

      <footer class="platform-settings__footer">
        <span class="text-small text-muted">
          Version {{ settingsVersion }}
          <template v-if="settingsUpdatedAt">
            / Updated {{ formatDateTime(settingsUpdatedAt) }}
          </template>
        </span>
        <div>
          <button
            class="btn btn--secondary"
            type="button"
            :disabled="!isDirty || isSaving"
            @click="resetForm"
          >
            <Undo2 :size="17" aria-hidden="true" />
            Discard Changes
          </button>
          <button class="btn btn--primary" type="submit" :disabled="!canSave">
            <Save :size="17" aria-hidden="true" />
            {{ isSaving ? 'Saving...' : 'Save Settings' }}
          </button>
        </div>
      </footer>
    </form>

    <ConfirmDialog
      :is-open="showDisableConfirmation"
      title="Disable library registrations?"
      message="New library owners will be unable to create accounts until registrations are enabled again."
      confirm-label="Disable Registrations"
      confirming-label="Saving"
      :is-confirming="isSaving"
      @cancel="showDisableConfirmation = false"
      @confirm="persistSettings"
    />
  </section>
</template>

<script setup>
import { LockKeyhole, RefreshCw, Save, Undo2 } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import SettingsToggle from '../../components/superadmin/SettingsToggle.vue'
import { useSuperAdminStore } from '../../stores/superAdminStore'

const TIMEZONES = Object.freeze(['Asia/Kolkata', 'UTC', 'Asia/Dubai'])
const store = useSuperAdminStore()
const {
  settings,
  settingsVersion,
  settingsUpdatedAt,
  isLoading,
  isSaving,
  errorMessage,
  errorRequestId,
  errorCode,
} = storeToRefs(store)

const form = reactive({
  allowLibraryRegistrations: true,
  sessionTimeoutMinutes: 30,
  defaultTimezone: 'Asia/Kolkata',
})
const loadedValues = ref(null)
const validationErrors = reactive({})
const successMessage = ref('')
const hasLoadedSettings = ref(false)
const showDisableConfirmation = ref(false)
let toastTimer = null

const editableValues = computed(() => ({
  allowLibraryRegistrations: form.allowLibraryRegistrations,
  sessionTimeoutMinutes: form.sessionTimeoutMinutes,
  defaultTimezone: form.defaultTimezone,
}))
const isDirty = computed(
  () =>
    loadedValues.value !== null &&
    JSON.stringify(editableValues.value) !== JSON.stringify(loadedValues.value),
)
const isValid = computed(() => Object.keys(validationErrors).length === 0)
const canSave = computed(() => isDirty.value && isValid.value && !isSaving.value)
const errorTitle = computed(() =>
  errorCode.value === 'PLATFORM_SETTINGS_UPDATE_CONFLICT'
    ? 'These settings were changed elsewhere.'
    : hasLoadedSettings.value
      ? 'Unable to save platform settings.'
      : 'Unable to load platform settings.',
)

function setForm(value) {
  const editable = {
    allowLibraryRegistrations: value.allowLibraryRegistrations,
    sessionTimeoutMinutes: value.sessionTimeoutMinutes,
    defaultTimezone: value.defaultTimezone,
  }
  Object.assign(form, editable)
  loadedValues.value = structuredClone(editable)
  validateForm()
}

function resetForm() {
  if (loadedValues.value) Object.assign(form, { ...loadedValues.value })
  validateForm()
}

function validateForm() {
  Object.keys(validationErrors).forEach((key) => delete validationErrors[key])
  if (
    !Number.isInteger(form.sessionTimeoutMinutes) ||
    form.sessionTimeoutMinutes < 15 ||
    form.sessionTimeoutMinutes > 1440
  ) {
    validationErrors.sessionTimeoutMinutes = 'Enter a whole number from 15 to 1440.'
  }
  if (!TIMEZONES.includes(form.defaultTimezone)) {
    validationErrors.defaultTimezone = 'Select an approved timezone.'
  }
  return Object.keys(validationErrors).length === 0
}

function formatDateTime(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function showSuccess(message) {
  successMessage.value = message
  window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    successMessage.value = ''
  }, 3500)
}

async function loadSettings() {
  try {
    const response = await store.fetchSettings()
    setForm(response.data.settings)
    hasLoadedSettings.value = true
  } catch {
    // Store-owned errors are rendered above.
  }
}

async function handleSave() {
  if (!validateForm() || !isDirty.value) return
  if (
    loadedValues.value?.allowLibraryRegistrations === true &&
    form.allowLibraryRegistrations === false
  ) {
    showDisableConfirmation.value = true
    return
  }
  await persistSettings()
}

async function persistSettings() {
  showDisableConfirmation.value = false
  try {
    const response = await store.updateSettings(editableValues.value)
    setForm(response.data.settings)
    showSuccess('Platform settings saved successfully.')
  } catch {
    // Store-owned errors are rendered above; loaded values remain unchanged.
  }
}

onMounted(loadSettings)
onBeforeUnmount(() => window.clearTimeout(toastTimer))
</script>

<style scoped>
.platform-settings {
  display: grid;
  gap: var(--space-6);
}

.platform-settings__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.platform-settings__title {
  margin: var(--space-1) 0 0;
}

.platform-settings__description {
  margin: var(--space-2) 0 0;
  color: var(--color-text-muted);
}

.platform-settings__loading {
  display: grid;
  min-height: 420px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.platform-settings__form,
.platform-settings__fieldset {
  display: grid;
  gap: var(--space-4);
}

.platform-settings__fieldset {
  padding: 0;
  border: 0;
  margin: 0;
}

.settings-section {
  overflow: hidden;
}

.settings-section:hover {
  box-shadow: var(--shadow-sm);
}

.settings-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.settings-section__header h2,
.settings-section__header p {
  margin: 0;
}

.settings-section__header h2 {
  font-size: var(--font-size-h5);
}

.settings-section__header p {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.settings-section__header .badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  flex: 0 0 auto;
}

.settings-section__body {
  padding: var(--space-5);
}

.settings-section__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.settings-section__input-suffix {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-2);
}

.settings-section__input-suffix span {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.platform-settings__field-error {
  color: var(--color-danger);
  font-size: var(--font-size-caption);
}

.platform-settings__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding-top: var(--space-2);
}

.platform-settings__footer > div {
  display: flex;
  gap: var(--space-3);
}

@media (max-width: 680px) {
  .platform-settings__header,
  .platform-settings__footer {
    align-items: stretch;
    flex-direction: column;
  }

  .settings-section__grid {
    grid-template-columns: 1fr;
  }

  .platform-settings__footer > div {
    flex-direction: column;
  }
}
</style>
