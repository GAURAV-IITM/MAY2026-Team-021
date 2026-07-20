<template>
  <section class="student-profile" aria-labelledby="student-profile-title">
    <header class="profile-header">
      <div><p class="text-label text-muted m-0">My Account</p><h1 id="student-profile-title" class="text-h2 profile-header__title">Profile</h1><p class="profile-header__description">Review your membership and keep your contact details current.</p></div>
      <button class="btn btn--primary" type="submit" form="student-profile-form" :disabled="!isDirty || isSaving">{{ isSaving ? 'Saving...' : 'Save Changes' }}</button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>
    <div v-if="errorMessage" class="alert alert--danger" role="alert"><span>{{ errorMessage }}</span><button class="btn btn--secondary btn--sm" type="button" @click="loadProfile">Retry</button></div>
    <LoadingSpinner v-if="isLoading && !hasLoaded" label="Loading your profile" />

    <form v-else-if="hasLoaded" id="student-profile-form" class="profile-form" @submit.prevent="handleSave">
      <aside class="card profile-identity" aria-label="Student identity">
        <span class="profile-identity__avatar" aria-hidden="true">{{ initials }}</span>
        <div><h2>{{ profile.fullName }}</h2><p>{{ profile.email }}</p></div>
        <span class="badge badge--success">{{ formatLabel(profile.status) }}</span>
        <dl>
          <div><dt>Membership ID</dt><dd>{{ profile.membershipId }}</dd></div>
          <div><dt>Library</dt><dd>{{ profile.libraryName }}</dd></div>
          <div><dt>Joined</dt><dd>{{ formatDate(profile.joiningDate) }}</dd></div>
          <div><dt>Allocated Seat</dt><dd>{{ profile.seatNumber || 'Not assigned' }}</dd></div>
        </dl>
      </aside>

      <div class="profile-form__sections">
        <section class="card profile-section" aria-labelledby="personal-details-title">
          <header><h2 id="personal-details-title">Personal Details</h2><p>Identity information is managed by the library team.</p></header>
          <div class="profile-section__body profile-section__grid">
            <div class="form-group"><label class="form-label" for="profile-first-name">First Name</label><input id="profile-first-name" class="form-input" :value="profile.firstName" readonly /></div>
            <div class="form-group"><label class="form-label" for="profile-last-name">Last Name</label><input id="profile-last-name" class="form-input" :value="profile.lastName" readonly /></div>
            <div class="form-group"><label class="form-label" for="profile-email">Email</label><input id="profile-email" class="form-input" type="email" :value="profile.email" readonly /></div>
            <div class="form-group"><label class="form-label" for="profile-birth-date">Date of Birth</label><input id="profile-birth-date" class="form-input" type="date" :value="profile.dateOfBirth" readonly /></div>
          </div>
        </section>

        <section class="card profile-section" aria-labelledby="contact-details-title">
          <header><h2 id="contact-details-title">Contact Details</h2><p>Used for library communication and emergency contact.</p></header>
          <div class="profile-section__body profile-section__grid">
            <div class="form-group"><label class="form-label" for="profile-phone">Phone</label><input id="profile-phone" v-model.trim="form.phone" class="form-input" type="tel" required /></div>
            <div class="form-group"><label class="form-label" for="profile-language">Preferred Language</label><select id="profile-language" v-model="form.preferredLanguage" class="form-select"><option>English</option><option>Hindi</option><option>Bengali</option></select></div>
            <div class="form-group profile-section__full"><label class="form-label" for="profile-address">Address</label><textarea id="profile-address" v-model.trim="form.address" class="form-textarea" rows="3" required></textarea></div>
            <div class="form-group"><label class="form-label" for="profile-guardian-name">Guardian Name</label><input id="profile-guardian-name" v-model.trim="form.guardianName" class="form-input" required /></div>
            <div class="form-group"><label class="form-label" for="profile-guardian-phone">Guardian Phone</label><input id="profile-guardian-phone" v-model.trim="form.guardianPhone" class="form-input" type="tel" required /></div>
          </div>
        </section>

        <footer class="profile-form__footer"><span class="text-small text-muted">{{ isDirty ? 'You have unsaved changes.' : 'Your profile is up to date.' }}</span><div><button class="btn btn--secondary" type="button" :disabled="!isDirty || isSaving" @click="resetForm">Discard</button><button class="btn btn--primary" type="submit" :disabled="!isDirty || isSaving">{{ isSaving ? 'Saving...' : 'Save Changes' }}</button></div></footer>
      </div>
    </form>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import { useAuthStore } from '../../stores/authStore'
import { useStudentPortalStore } from '../../stores/studentPortalStore'

const authStore = useAuthStore()
const portalStore = useStudentPortalStore()
const { currentUser } = storeToRefs(authStore)
const { profile, isLoading, isSaving, errorMessage } = storeToRefs(portalStore)
const form = reactive({ phone: '', address: '', guardianName: '', guardianPhone: '', preferredLanguage: 'English' })
const hasLoaded = ref(false)
const successMessage = ref('')
let successTimer = null
const editableFields = ['phone', 'address', 'guardianName', 'guardianPhone', 'preferredLanguage']
const isDirty = computed(() => hasLoaded.value && editableFields.some((field) => String(form[field] || '') !== String(profile.value?.[field] || '')))
const initials = computed(() => `${profile.value?.firstName?.[0] || ''}${profile.value?.lastName?.[0] || ''}`.toUpperCase())

function resetForm() { if (!profile.value) return; editableFields.forEach((field) => { form[field] = profile.value[field] || (field === 'preferredLanguage' ? 'English' : '') }) }
function formatLabel(value) { return String(value || '-').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(`${value}T00:00:00`)) : '-' }
function showSuccess(message) { successMessage.value = message; window.clearTimeout(successTimer); successTimer = window.setTimeout(() => { successMessage.value = '' }, 3500) }
async function loadProfile() { try { await portalStore.fetchProfile(currentUser.value?.id); resetForm(); hasLoaded.value = true } catch { /* Store-owned errors are rendered above. */ } }
async function handleSave() { try { await portalStore.updateProfile(currentUser.value?.id, { ...form }); resetForm(); showSuccess('Your profile was updated successfully.') } catch { /* Store-owned errors are rendered above. */ } }

onMounted(loadProfile)
onBeforeUnmount(() => window.clearTimeout(successTimer))
</script>

<style scoped>
.student-profile { display: grid; gap: var(--space-6); }
.profile-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.profile-header__title { margin: var(--space-1) 0 0; }
.profile-header__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.profile-form { display: grid; grid-template-columns: minmax(240px, 320px) minmax(0, 1fr); align-items: start; gap: var(--space-5); }
.profile-identity { display: grid; justify-items: center; gap: var(--space-4); padding: var(--space-6); text-align: center; }
.profile-identity__avatar { display: inline-flex; align-items: center; justify-content: center; width: 84px; height: 84px; border-radius: 50%; background: var(--color-primary); color: var(--color-text-inverse); font-size: var(--font-size-h2); font-weight: var(--font-weight-bold); }
.profile-identity h2, .profile-identity p { margin: 0; }
.profile-identity h2 { font-size: var(--font-size-h4); }
.profile-identity p { margin-top: var(--space-1); color: var(--color-text-muted); overflow-wrap: anywhere; }
.profile-identity dl { display: grid; width: 100%; gap: var(--space-3); margin: var(--space-2) 0 0; text-align: left; }
.profile-identity dl div { display: grid; gap: var(--space-1); padding-top: var(--space-3); border-top: 1px solid var(--color-divider); }
.profile-identity dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.profile-identity dd { margin: 0; font-weight: var(--font-weight-medium); overflow-wrap: anywhere; }
.profile-form__sections { display: grid; gap: var(--space-4); min-width: 0; }
.profile-section { overflow: hidden; }
.profile-section header { padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.profile-section header h2, .profile-section header p { margin: 0; }
.profile-section header h2 { font-size: var(--font-size-h5); }
.profile-section header p { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.profile-section__body { padding: var(--space-5); }
.profile-section__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
.profile-section__full { grid-column: 1 / -1; }
.profile-form__footer { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding-top: var(--space-2); }
.profile-form__footer > div { display: flex; gap: var(--space-3); }
@media (max-width: 900px) { .profile-form { grid-template-columns: 1fr; } .profile-identity { grid-template-columns: auto minmax(0, 1fr) auto; justify-items: start; text-align: left; } .profile-identity__avatar { width: 64px; height: 64px; font-size: var(--font-size-h4); } .profile-identity dl { grid-column: 1 / -1; grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 600px) { .profile-header, .profile-form__footer { align-items: stretch; flex-direction: column; } .profile-header .btn { width: 100%; } .profile-identity { grid-template-columns: 1fr; justify-items: center; text-align: center; } .profile-identity dl { grid-column: auto; grid-template-columns: 1fr; } .profile-section__grid { grid-template-columns: 1fr; } .profile-section__full { grid-column: auto; } .profile-form__footer > div { display: grid; } }
</style>
