<template>
  <section class="library-settings" aria-labelledby="library-settings-title">
    <header class="library-settings__header">
      <div><p class="text-label text-muted m-0">Library Configuration</p><h1 id="library-settings-title">Settings</h1><p>Manage your library profile, operating rules, fees, and notifications.</p></div>
      <button class="btn btn--primary" type="submit" form="library-settings-form" :disabled="!isDirty || isSaving"><Save :size="17" />{{ isSaving ? 'Saving...' : 'Save Changes' }}</button>
    </header>

    <div v-if="errorMessage" class="alert alert--danger library-settings__error" role="alert"><div><strong>Unable to save library settings.</strong><p class="m-0">{{ errorMessage }}</p></div><button class="btn btn--secondary btn--sm" type="button" @click="loadSettings">Retry</button></div>
    <div v-if="isLoading && !hasLoaded" class="library-settings__loading"><LoadingSpinner label="Loading library settings" /></div>

    <div v-else-if="hasLoaded" class="library-settings__workspace">
      <aside class="library-settings__navigation" aria-label="Settings sections">
        <button v-for="section in sections" :key="section.id" type="button" @click="scrollToSection(section.id)"><component :is="section.icon" :size="17" />{{ section.label }}<ChevronRight :size="15" /></button>
        <div><small>Signed in as</small><strong>{{ currentUser?.name }}</strong><span>{{ currentUser?.email }}</span></div>
      </aside>

      <form id="library-settings-form" class="library-settings__form" novalidate @submit.prevent="saveSettings">
        <section id="settings-profile" class="settings-panel" aria-labelledby="settings-profile-title">
          <header><div><span><Building2 :size="18" /></span><div><h2 id="settings-profile-title">Library Profile</h2><p>Public identity and contact details used on receipts and student pages.</p></div></div></header>
          <div class="settings-panel__body settings-panel__grid">
            <div class="form-field settings-panel__full" :class="{ 'form-field--error': errors.libraryName }"><label class="form-label" for="library-name">Library Name</label><input id="library-name" v-model.trim="form.libraryName" class="form-control" maxlength="100" /><p v-if="errors.libraryName" class="form-help">{{ errors.libraryName }}</p></div>
            <div class="form-field" :class="{ 'form-field--error': errors.contactEmail }"><label class="form-label" for="library-email">Contact Email</label><input id="library-email" v-model.trim="form.contactEmail" class="form-control" type="email" /><p v-if="errors.contactEmail" class="form-help">{{ errors.contactEmail }}</p></div>
            <div class="form-field" :class="{ 'form-field--error': errors.contactPhone }"><label class="form-label" for="library-phone">Contact Phone</label><input id="library-phone" v-model.trim="form.contactPhone" class="form-control" type="tel" maxlength="10" inputmode="numeric" /><p v-if="errors.contactPhone" class="form-help">{{ errors.contactPhone }}</p></div>
            <div class="form-field settings-panel__full" :class="{ 'form-field--error': errors.address }"><label class="form-label" for="library-address">Street Address</label><input id="library-address" v-model.trim="form.address" class="form-control" /><p v-if="errors.address" class="form-help">{{ errors.address }}</p></div>
            <div class="form-field" :class="{ 'form-field--error': errors.city }"><label class="form-label" for="library-city">City</label><input id="library-city" v-model.trim="form.city" class="form-control" /><p v-if="errors.city" class="form-help">{{ errors.city }}</p></div>
            <div class="form-field" :class="{ 'form-field--error': errors.state }"><label class="form-label" for="library-state">State</label><input id="library-state" v-model.trim="form.state" class="form-control" /><p v-if="errors.state" class="form-help">{{ errors.state }}</p></div>
            <div class="form-field" :class="{ 'form-field--error': errors.postalCode }"><label class="form-label" for="library-postal-code">Postal Code</label><input id="library-postal-code" v-model.trim="form.postalCode" class="form-control" maxlength="6" inputmode="numeric" /><p v-if="errors.postalCode" class="form-help">{{ errors.postalCode }}</p></div>
            <label class="form-field"><span class="form-label">Timezone</span><select v-model="form.timezone" class="form-select"><option value="Asia/Kolkata">Asia/Kolkata</option><option value="UTC">UTC</option><option value="Asia/Dubai">Asia/Dubai</option></select></label>
          </div>
        </section>

        <section id="settings-operations" class="settings-panel" aria-labelledby="settings-operations-title">
          <header><div><span><Clock3 :size="18" /></span><div><h2 id="settings-operations-title">Operating Preferences</h2><p>Configure opening hours and student seat-request rules.</p></div></div></header>
          <div class="settings-panel__body">
            <div class="settings-panel__grid settings-panel__block">
              <div class="form-field" :class="{ 'form-field--error': errors.openingTime }"><label class="form-label" for="opening-time">Opening Time</label><input id="opening-time" v-model="form.openingTime" class="form-control" type="time" /><p v-if="errors.openingTime" class="form-help">{{ errors.openingTime }}</p></div>
              <div class="form-field" :class="{ 'form-field--error': errors.closingTime }"><label class="form-label" for="closing-time">Closing Time</label><input id="closing-time" v-model="form.closingTime" class="form-control" type="time" /><p v-if="errors.closingTime" class="form-help">{{ errors.closingTime }}</p></div>
              <label class="form-field"><span class="form-label">Weekly Off</span><select v-model="form.weeklyOff" class="form-select"><option value="none">No weekly off</option><option v-for="day in weekDays" :key="day.toLowerCase()" :value="day.toLowerCase()">{{ day }}</option></select></label>
            </div>
            <div class="settings-panel__toggles">
              <SettingsToggle v-model="form.allowSeatChangeRequests" label="Allow seat change requests" description="Students can submit seat or shift change requests from their portal." />
              <SettingsToggle v-model="form.requireSeatRequestReason" label="Require a request reason" description="Students must explain why they need a seat or shift change." />
            </div>
          </div>
        </section>

        <section id="settings-fees" class="settings-panel" aria-labelledby="settings-fees-title">
          <header><div><span><ReceiptIndianRupee :size="18" /></span><div><h2 id="settings-fees-title">Fees & Receipts</h2><p>Defaults used when monthly payment records and receipts are created.</p></div></div></header>
          <div class="settings-panel__body">
            <div class="settings-panel__grid settings-panel__block">
              <div class="form-field" :class="{ 'form-field--error': errors.defaultMonthlyFee }"><label class="form-label" for="monthly-fee">Default Monthly Fee</label><div class="settings-panel__input-prefix"><span>₹</span><input id="monthly-fee" v-model.number="form.defaultMonthlyFee" class="form-control" type="number" min="1" step="50" /></div><p v-if="errors.defaultMonthlyFee" class="form-help">{{ errors.defaultMonthlyFee }}</p></div>
              <div class="form-field" :class="{ 'form-field--error': errors.feeDueDay }"><label class="form-label" for="fee-due-day">Fee Due Day</label><input id="fee-due-day" v-model.number="form.feeDueDay" class="form-control" type="number" min="1" max="28" /><p class="form-help" :class="{ 'settings-panel__error': errors.feeDueDay }">{{ errors.feeDueDay || 'Day of each month, from 1 to 28.' }}</p></div>
              <div class="form-field" :class="{ 'form-field--error': errors.paymentGraceDays }"><label class="form-label" for="grace-days">Payment Grace Period</label><div class="settings-panel__input-suffix"><input id="grace-days" v-model.number="form.paymentGraceDays" class="form-control" type="number" min="0" max="30" /><span>days</span></div><p v-if="errors.paymentGraceDays" class="form-help">{{ errors.paymentGraceDays }}</p></div>
              <div class="form-field" :class="{ 'form-field--error': errors.receiptPrefix }"><label class="form-label" for="receipt-prefix">Receipt Prefix</label><input id="receipt-prefix" v-model.trim="form.receiptPrefix" class="form-control settings-panel__uppercase" maxlength="10" /><p class="form-help" :class="{ 'settings-panel__error': errors.receiptPrefix }">{{ errors.receiptPrefix || `Example: ${form.receiptPrefix || 'LIB'}-202607-001` }}</p></div>
            </div>
            <div class="settings-panel__toggles"><SettingsToggle v-model="form.whatsappRemindersEnabled" label="Enable WhatsApp fee reminders" description="Allow owners to prepare WhatsApp reminders for unpaid payment records." /></div>
          </div>
        </section>

        <section id="settings-notifications" class="settings-panel" aria-labelledby="settings-notifications-title">
          <header><div><span><BellRing :size="18" /></span><div><h2 id="settings-notifications-title">Owner Notifications</h2><p>Choose the operational events that should appear in owner alerts.</p></div></div></header>
          <div class="settings-panel__body settings-panel__toggles">
            <SettingsToggle v-model="form.notifyPendingPayments" label="Pending payment alerts" description="Notify when monthly fees remain unpaid after the due date." />
            <SettingsToggle v-model="form.notifySeatRequests" label="Seat request alerts" description="Notify when a student submits a seat or shift change request." />
            <SettingsToggle v-model="form.notifyMaintenanceSeats" label="Maintenance seat alerts" description="Notify when seats remain under maintenance." />
            <SettingsToggle v-model="form.emailAnnouncementCopy" label="Email announcement copy" description="Send the owner an email copy when an announcement is published." />
          </div>
        </section>

        <footer class="library-settings__footer"><span>Last updated {{ formatDateTime(settings.updatedAt) }}</span><div><button class="btn btn--secondary" type="button" :disabled="!isDirty || isSaving" @click="resetForm"><Undo2 :size="17" aria-hidden="true" /> Discard Changes</button><button class="btn btn--primary" type="submit" :disabled="!isDirty || isSaving"><Save :size="17" />{{ isSaving ? 'Saving...' : 'Save Changes' }}</button></div></footer>
      </form>
    </div>

    <Toast v-if="toastMessage" :type="toastType">{{ toastMessage }}</Toast>
  </section>
</template>

<script setup>
import { BellRing, Building2, ChevronRight, Clock3, ReceiptIndianRupee, Save, Undo2 } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import SettingsToggle from '../../components/superadmin/SettingsToggle.vue'
import { useAuthStore } from '../../stores/authStore.js'
import { useLibrarySettingsStore } from '../../stores/librarySettingsStore.js'

const store = useLibrarySettingsStore()
const authStore = useAuthStore()
const { settings, isLoading, isSaving, errorMessage } = storeToRefs(store)
const { currentUser } = storeToRefs(authStore)
const form = reactive({})
const errors = reactive({})
const hasLoaded = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
let toastTimer
const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const sections = [
  { id: 'settings-profile', label: 'Library Profile', icon: Building2 },
  { id: 'settings-operations', label: 'Operating Preferences', icon: Clock3 },
  { id: 'settings-fees', label: 'Fees & Receipts', icon: ReceiptIndianRupee },
  { id: 'settings-notifications', label: 'Notifications', icon: BellRing },
]
const isDirty = computed(() => settings.value && JSON.stringify(form) !== JSON.stringify(settings.value))

function clone(value) { return JSON.parse(JSON.stringify(value)) }
function resetForm() { if (settings.value) { Object.keys(form).forEach((key) => delete form[key]); Object.assign(form, clone(settings.value)); clearErrors() } }
function clearErrors() { Object.keys(errors).forEach((key) => delete errors[key]) }
function validate() {
  clearErrors()
  if (String(form.libraryName || '').trim().length < 3) errors.libraryName = 'Library name must contain at least 3 characters.'
  if (!/^\S+@\S+\.\S+$/.test(String(form.contactEmail || ''))) errors.contactEmail = 'Enter a valid email address.'
  if (!/^\d{10}$/.test(String(form.contactPhone || '').replace(/\D/g, ''))) errors.contactPhone = 'Enter exactly 10 digits.'
  if (!String(form.address || '').trim()) errors.address = 'Street address is required.'
  if (!String(form.city || '').trim()) errors.city = 'City is required.'
  if (!String(form.state || '').trim()) errors.state = 'State is required.'
  if (!/^\d{6}$/.test(String(form.postalCode || ''))) errors.postalCode = 'Enter a 6-digit postal code.'
  if (!form.openingTime) errors.openingTime = 'Opening time is required.'
  if (!form.closingTime || form.closingTime <= form.openingTime) errors.closingTime = 'Closing time must be later than opening time.'
  if (!Number.isFinite(Number(form.defaultMonthlyFee)) || Number(form.defaultMonthlyFee) < 1) errors.defaultMonthlyFee = 'Enter a fee greater than zero.'
  if (!Number.isInteger(Number(form.feeDueDay)) || form.feeDueDay < 1 || form.feeDueDay > 28) errors.feeDueDay = 'Due day must be between 1 and 28.'
  if (!Number.isInteger(Number(form.paymentGraceDays)) || form.paymentGraceDays < 0 || form.paymentGraceDays > 30) errors.paymentGraceDays = 'Grace period must be between 0 and 30 days.'
  if (!/^[A-Z0-9]{2,10}$/.test(String(form.receiptPrefix || '').toUpperCase())) errors.receiptPrefix = 'Use 2 to 10 letters or numbers.'
  return Object.keys(errors).length === 0
}
function focusFirstError() { requestAnimationFrame(() => document.querySelector('.form-field--error input, .form-field--error select')?.focus()) }
function showToast(message, type = 'success') { globalThis.clearTimeout(toastTimer); toastMessage.value = message; toastType.value = type; toastTimer = globalThis.setTimeout(() => { toastMessage.value = '' }, 3200) }
function formatDateTime(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value)) : 'Not saved yet' }
function scrollToSection(id) { document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }
async function loadSettings() {
  try { await store.fetchSettings(); resetForm(); hasLoaded.value = true } catch { showToast(errorMessage.value, 'error') }
}
async function saveSettings() {
  if (!validate()) { focusFirstError(); showToast('Please correct the highlighted settings.', 'error'); return }
  try { await store.updateSettings({ ...form, receiptPrefix: form.receiptPrefix.toUpperCase() }); resetForm(); showToast('Library settings saved successfully.') } catch { showToast(errorMessage.value, 'error') }
}

onMounted(loadSettings)
onBeforeUnmount(() => globalThis.clearTimeout(toastTimer))
</script>

<style scoped>
.library-settings { display: grid; gap: var(--space-5); }
.library-settings__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.library-settings__header h1 { margin: var(--space-1) 0 0; font-size: var(--font-size-h2); }
.library-settings__header p:not(.text-label) { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.library-settings__error { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }
.library-settings__loading { display: grid; min-height: 420px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); }
.library-settings__workspace { display: grid; grid-template-columns: 230px minmax(0, 1fr); align-items: start; gap: var(--space-5); }
.library-settings__navigation { position: sticky; top: calc(var(--layout-navbar-height) + var(--space-4)); display: grid; gap: var(--space-1); }
.library-settings__navigation button { display: grid; grid-template-columns: 20px minmax(0, 1fr) auto; align-items: center; gap: var(--space-2); min-height: 42px; padding: 0 var(--space-3); border: 0; border-radius: var(--radius-md); background: transparent; color: var(--color-text-secondary); text-align: left; }
.library-settings__navigation button:hover { background: var(--color-hover); color: var(--color-text-primary); }
.library-settings__navigation > div { display: grid; margin-top: var(--space-4); padding: var(--space-4); border-top: 1px solid var(--color-divider); color: var(--color-text-muted); }
.library-settings__navigation > div strong { color: var(--color-text-primary); }
.library-settings__navigation > div span { overflow: hidden; font-size: var(--font-size-caption); text-overflow: ellipsis; }
.library-settings__form { display: grid; min-width: 0; gap: var(--space-4); }
.settings-panel { scroll-margin-top: calc(var(--layout-navbar-height) + var(--space-4)); overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
.settings-panel > header { padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.settings-panel > header > div { display: flex; align-items: flex-start; gap: var(--space-3); }
.settings-panel > header span { display: grid; width: 36px; height: 36px; flex: 0 0 auto; place-items: center; border-radius: var(--radius-md); background: var(--color-primary-light); color: var(--color-primary); }
.settings-panel h2, .settings-panel header p { margin: 0; }
.settings-panel h2 { font-size: var(--font-size-h5); }
.settings-panel header p { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.settings-panel__body { padding: var(--space-5); }
.settings-panel__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
.settings-panel__full { grid-column: 1 / -1; }
.settings-panel__block { margin-bottom: var(--space-5); }
.settings-panel__toggles { display: grid; gap: var(--space-5); }
.settings-panel__input-prefix, .settings-panel__input-suffix { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: center; gap: var(--space-2); }
.settings-panel__input-suffix { grid-template-columns: minmax(0, 1fr) auto; }
.settings-panel__input-prefix span, .settings-panel__input-suffix span { color: var(--color-text-muted); }
.settings-panel__uppercase { text-transform: uppercase; }
.form-field--error .form-help, .settings-panel__error { color: var(--color-danger); }
.library-settings__footer { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-3) 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.library-settings__footer > div { display: flex; gap: var(--space-2); }
@media (max-width: 950px) { .library-settings__workspace { grid-template-columns: 1fr; } .library-settings__navigation { position: static; display: flex; overflow-x: auto; padding-bottom: var(--space-2); } .library-settings__navigation button { min-width: max-content; } .library-settings__navigation button svg:last-child, .library-settings__navigation > div { display: none; } }
@media (max-width: 650px) { .library-settings__header, .library-settings__footer { align-items: stretch; flex-direction: column; } .settings-panel__grid { grid-template-columns: 1fr; } .settings-panel__full { grid-column: auto; } .library-settings__footer > div { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 480px) { .library-settings__header h1 { font-size: var(--font-size-h3); } .library-settings__header > .btn { width: 100%; } .settings-panel > header, .settings-panel__body { padding: var(--space-4); } .library-settings__error { align-items: stretch; flex-direction: column; } }
</style>
