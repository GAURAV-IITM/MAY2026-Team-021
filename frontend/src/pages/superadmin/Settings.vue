<template>
  <section class="platform-settings" aria-labelledby="platform-settings-title">
    <header class="platform-settings__header">
      <div>
        <p class="text-label text-muted m-0">System Configuration</p>
        <h1 id="platform-settings-title" class="text-h2 platform-settings__title">Platform Settings</h1>
        <p class="platform-settings__description">Configure registration, access, support, and platform-wide notifications.</p>
      </div>
      <button class="btn btn--primary" type="submit" form="platform-settings-form" :disabled="!isDirty || isSaving">
        <Save :size="17" aria-hidden="true" />
        {{ isSaving ? 'Saving...' : 'Save Settings' }}
      </button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div><strong>Unable to save platform settings.</strong><p class="m-0">{{ errorMessage }}</p></div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadSettings"><RefreshCw :size="16" aria-hidden="true" /> Retry</button>
    </div>

    <div v-if="isLoading && !hasLoadedSettings" class="platform-settings__loading">
      <LoadingSpinner label="Loading platform settings" />
    </div>

    <form v-if="hasLoadedSettings" id="platform-settings-form" class="platform-settings__form" @submit.prevent="handleSave">
      <section class="card settings-section" aria-labelledby="general-settings-title">
        <header class="settings-section__header"><h2 id="general-settings-title">General</h2><p>Platform identity and support contact details.</p></header>
        <div class="settings-section__body settings-section__grid">
          <div class="form-group settings-section__full"><label class="form-label" for="platform-name">Platform Name</label><input id="platform-name" v-model.trim="form.platformName" class="form-input" required /></div>
          <div class="form-group"><label class="form-label" for="support-email">Support Email</label><input id="support-email" v-model.trim="form.supportEmail" class="form-input" type="email" required /></div>
          <div class="form-group"><label class="form-label" for="support-phone">Support Phone</label><input id="support-phone" v-model.trim="form.supportPhone" class="form-input" type="tel" /></div>
        </div>
      </section>

      <section class="card settings-section" aria-labelledby="registration-settings-title">
        <header class="settings-section__header"><h2 id="registration-settings-title">Library Registration</h2><p>Control how new libraries enter the platform.</p></header>
        <div class="settings-section__body settings-section__toggles">
          <SettingsToggle v-model="form.allowLibraryRegistrations" label="Allow library registrations" description="Permit new libraries to submit registration requests." />
          <SettingsToggle v-model="form.requireRegistrationApproval" label="Require Super Admin approval" description="Keep new registrations pending until they are reviewed." />
        </div>
      </section>

      <section class="card settings-section" aria-labelledby="security-settings-title">
        <header class="settings-section__header"><h2 id="security-settings-title">Access and Availability</h2><p>Configure sessions and platform maintenance controls.</p></header>
        <div class="settings-section__body settings-section__grid">
          <div class="form-group"><label class="form-label" for="session-timeout">Session Timeout</label><div class="settings-section__input-suffix"><input id="session-timeout" v-model.number="form.sessionTimeoutMinutes" class="form-input" type="number" min="15" step="5" required /><span>minutes</span></div></div>
          <div class="form-group"><label class="form-label" for="platform-timezone">Default Timezone</label><select id="platform-timezone" v-model="form.defaultTimezone" class="form-select"><option value="Asia/Kolkata">Asia/Kolkata</option><option value="UTC">UTC</option><option value="Asia/Dubai">Asia/Dubai</option></select></div>
          <div class="settings-section__full">
            <SettingsToggle v-model="form.maintenanceMode" label="Maintenance mode" description="Temporarily prevent library owners from accessing operational modules." tone="danger" />
          </div>
        </div>
      </section>

      <section class="card settings-section" aria-labelledby="notification-settings-title">
        <header class="settings-section__header"><h2 id="notification-settings-title">Notifications</h2><p>Choose which platform events notify the Super Admin.</p></header>
        <div class="settings-section__body settings-section__toggles">
          <SettingsToggle v-model="form.notifyOnLibraryRegistration" label="New library registrations" description="Notify when a registration request is submitted." />
          <SettingsToggle v-model="form.notifyOnOwnerSuspension" label="Owner access changes" description="Notify when an owner account is suspended." />
          <SettingsToggle v-model="form.weeklySummaryEnabled" label="Weekly platform summary" description="Receive a weekly overview of platform activity." />
        </div>
      </section>

      <footer class="platform-settings__footer">
        <span class="text-small text-muted">Last updated {{ formatDateTime(settings.updatedAt) }}</span>
        <div><button class="btn btn--secondary" type="button" :disabled="!isDirty || isSaving" @click="resetForm"><Undo2 :size="17" aria-hidden="true" /> Discard Changes</button><button class="btn btn--primary" type="submit" :disabled="!isDirty || isSaving"><Save :size="17" aria-hidden="true" />{{ isSaving ? 'Saving...' : 'Save Settings' }}</button></div>
      </footer>
    </form>
  </section>
</template>

<script setup>
import { RefreshCw, Save, Undo2 } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import SettingsToggle from '../../components/superadmin/SettingsToggle.vue'
import { useSuperAdminStore } from '../../stores/superAdminStore'

const store = useSuperAdminStore()
const { settings, isLoading, isSaving, errorMessage } = storeToRefs(store)
const form = reactive({})
const successMessage = ref('')
const hasLoadedSettings = ref(false)
let toastTimer = null

const isDirty = computed(() => settings.value && JSON.stringify(form) !== JSON.stringify(settings.value))

function cloneSettings(value) { return JSON.parse(JSON.stringify(value)) }
function resetForm() { if (settings.value) Object.assign(form, cloneSettings(settings.value)) }
function formatDateTime(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value)) : '—' }
function showSuccess(message) { successMessage.value = message; window.clearTimeout(toastTimer); toastTimer = window.setTimeout(() => { successMessage.value = '' }, 3500) }
async function loadSettings() {
  try {
    const response = await store.fetchSettings()
    Object.assign(form, cloneSettings(response.data.settings))
    hasLoadedSettings.value = true
  } catch { /* Store-owned errors are rendered above. */ }
}
async function handleSave() { try { await store.updateSettings({ ...form }); resetForm(); showSuccess('Platform settings saved successfully.') } catch { /* Store-owned errors are rendered above. */ } }

onMounted(loadSettings)
onBeforeUnmount(() => window.clearTimeout(toastTimer))
</script>

<style scoped>
.platform-settings { display: grid; gap: var(--space-6); }
.platform-settings__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.platform-settings__title { margin: var(--space-1) 0 0; }
.platform-settings__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.platform-settings__loading { display: grid; min-height: 420px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); }
.platform-settings__form { display: grid; gap: var(--space-4); }
.settings-section { overflow: hidden; }
.settings-section:hover { box-shadow: var(--shadow-sm); }
.settings-section__header { padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.settings-section__header h2, .settings-section__header p { margin: 0; }
.settings-section__header h2 { font-size: var(--font-size-h5); }
.settings-section__header p { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.settings-section__body { padding: var(--space-5); }
.settings-section__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
.settings-section__full { grid-column: 1 / -1; }
.settings-section__toggles { display: grid; gap: var(--space-4); }
.settings-section__input-suffix { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: var(--space-2); }
.settings-section__input-suffix span { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.platform-settings__footer { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding-top: var(--space-2); }
.platform-settings__footer > div { display: flex; gap: var(--space-3); }
@media (max-width: 680px) { .platform-settings__header, .platform-settings__footer { align-items: stretch; flex-direction: column; } .settings-section__grid { grid-template-columns: 1fr; } .settings-section__full { grid-column: auto; } .platform-settings__footer > div { flex-direction: column; } }
</style>
