<template>
  <section class="owner-profile" aria-labelledby="owner-profile-title">
    <header class="owner-profile__header">
      <div>
        <p class="text-label text-muted m-0">Owner Account</p>
        <h1 id="owner-profile-title">My Profile</h1>
        <p>Manage your personal account details and sign-in password.</p>
      </div>
      <button
        class="btn btn--primary"
        type="submit"
        form="owner-details-form"
        :disabled="!isProfileDirty || isUpdatingProfile"
      >
        <Save :size="17" aria-hidden="true" />
        {{ isUpdatingProfile ? 'Saving...' : 'Save Changes' }}
      </button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>

    <div class="owner-profile__workspace">
      <aside class="owner-profile__identity card" aria-label="Owner account summary">
        <span class="owner-profile__avatar" aria-hidden="true">{{ initials }}</span>
        <div class="owner-profile__identity-heading">
          <h2>{{ currentUser?.name }}</h2>
          <p>{{ currentUser?.email }}</p>
        </div>
        <span class="badge badge--success"
          ><BadgeCheck :size="14" aria-hidden="true" /> Active</span
        >

        <dl class="owner-profile__facts">
          <div>
            <dt><ShieldCheck :size="15" aria-hidden="true" /> Account Role</dt>
            <dd>{{ currentUser?.roleLabel || 'Library Owner' }}</dd>
          </div>
          <div>
            <dt><Building2 :size="15" aria-hidden="true" /> Library</dt>
            <dd>{{ currentUser?.libraryName || 'Not assigned' }}</dd>
          </div>
          <div>
            <dt><KeyRound :size="15" aria-hidden="true" /> Account ID</dt>
            <dd>{{ currentUser?.id || '-' }}</dd>
          </div>
          <div>
            <dt><CalendarDays :size="15" aria-hidden="true" /> Member Since</dt>
            <dd>{{ formatDate(currentUser?.createdAt) }}</dd>
          </div>
        </dl>

        <RouterLink
          class="btn btn--secondary owner-profile__library-link"
          :to="{ name: 'adminSettings' }"
        >
          <Building2 :size="16" aria-hidden="true" /> Library Settings
        </RouterLink>
      </aside>

      <div class="owner-profile__content">
        <form
          id="owner-details-form"
          class="owner-profile__panel"
          novalidate
          @submit.prevent="saveProfile"
        >
          <header class="owner-profile__panel-header">
            <span><UserRound :size="18" aria-hidden="true" /></span>
            <div>
              <h2>Personal Details</h2>
              <p>These details identify you as the owner of this library account.</p>
            </div>
          </header>

          <div
            v-if="profileErrorMessage"
            class="alert alert--danger owner-profile__alert"
            role="alert"
          >
            {{ profileErrorMessage }}
          </div>

          <div class="owner-profile__panel-body owner-profile__grid">
            <div
              class="form-field owner-profile__full"
              :class="{ 'form-field--error': visibleProfileError('name') }"
            >
              <label class="form-label" for="owner-profile-name">Full Name</label>
              <div class="owner-profile__input-wrap">
                <UserRound :size="17" aria-hidden="true" />
                <input
                  id="owner-profile-name"
                  v-model.trim="profileForm.name"
                  class="form-control"
                  maxlength="80"
                  autocomplete="name"
                  :aria-invalid="Boolean(visibleProfileError('name'))"
                />
              </div>
              <p v-if="visibleProfileError('name')" class="form-help">{{ profileErrors.name }}</p>
            </div>

            <div class="form-field" :class="{ 'form-field--error': visibleProfileError('email') }">
              <label class="form-label" for="owner-profile-email">Email Address</label>
              <div class="owner-profile__input-wrap">
                <Mail :size="17" aria-hidden="true" />
                <input
                  id="owner-profile-email"
                  v-model.trim="profileForm.email"
                  class="form-control"
                  type="email"
                  autocomplete="email"
                  :aria-invalid="Boolean(visibleProfileError('email'))"
                />
              </div>
              <p v-if="visibleProfileError('email')" class="form-help">{{ profileErrors.email }}</p>
            </div>

            <div class="form-field" :class="{ 'form-field--error': visibleProfileError('phone') }">
              <label class="form-label" for="owner-profile-phone">Mobile Number</label>
              <div class="owner-profile__input-wrap">
                <Phone :size="17" aria-hidden="true" />
                <input
                  id="owner-profile-phone"
                  v-model.trim="profileForm.phone"
                  class="form-control"
                  type="tel"
                  inputmode="numeric"
                  maxlength="10"
                  autocomplete="tel"
                  :aria-invalid="Boolean(visibleProfileError('phone'))"
                />
              </div>
              <p v-if="visibleProfileError('phone')" class="form-help">{{ profileErrors.phone }}</p>
            </div>
          </div>

          <footer class="owner-profile__panel-footer">
            <span>{{
              isProfileDirty ? 'You have unsaved profile changes.' : 'Your profile is up to date.'
            }}</span>
            <div>
              <button
                class="btn btn--secondary"
                type="button"
                :disabled="!isProfileDirty || isUpdatingProfile"
                @click="resetProfileForm"
              >
                <Undo2 :size="17" aria-hidden="true" /> Discard
              </button>
              <button
                class="btn btn--primary"
                type="submit"
                :disabled="!isProfileDirty || isUpdatingProfile"
              >
                <Save :size="17" aria-hidden="true" />
                {{ isUpdatingProfile ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </footer>
        </form>

        <form class="owner-profile__panel" novalidate @submit.prevent="savePassword">
          <header class="owner-profile__panel-header owner-profile__panel-header--security">
            <span><LockKeyhole :size="18" aria-hidden="true" /></span>
            <div>
              <h2>Account Security</h2>
              <p>Use your current password to set a new account password.</p>
            </div>
          </header>

          <div
            v-if="passwordErrorMessage"
            class="alert alert--danger owner-profile__alert"
            role="alert"
          >
            {{ passwordErrorMessage }}
          </div>

          <div class="owner-profile__panel-body owner-profile__password-grid">
            <div
              class="form-field"
              :class="{ 'form-field--error': visiblePasswordError('currentPassword') }"
            >
              <label class="form-label" for="owner-current-password">Current Password</label>
              <div class="owner-profile__password-wrap">
                <input
                  id="owner-current-password"
                  v-model="passwordForm.currentPassword"
                  class="form-control"
                  :type="showCurrentPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  :aria-invalid="Boolean(visiblePasswordError('currentPassword'))"
                />
                <button
                  type="button"
                  :aria-label="
                    showCurrentPassword ? 'Hide current password' : 'Show current password'
                  "
                  @click="showCurrentPassword = !showCurrentPassword"
                >
                  <EyeOff v-if="showCurrentPassword" :size="17" aria-hidden="true" />
                  <Eye v-else :size="17" aria-hidden="true" />
                </button>
              </div>
              <p v-if="visiblePasswordError('currentPassword')" class="form-help">
                {{ passwordErrors.currentPassword }}
              </p>
            </div>

            <div
              class="form-field"
              :class="{ 'form-field--error': visiblePasswordError('newPassword') }"
            >
              <label class="form-label" for="owner-new-password">New Password</label>
              <div class="owner-profile__password-wrap">
                <input
                  id="owner-new-password"
                  v-model="passwordForm.newPassword"
                  class="form-control"
                  :type="showNewPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  :aria-invalid="Boolean(visiblePasswordError('newPassword'))"
                />
                <button
                  type="button"
                  :aria-label="showNewPassword ? 'Hide new password' : 'Show new password'"
                  @click="showNewPassword = !showNewPassword"
                >
                  <EyeOff v-if="showNewPassword" :size="17" aria-hidden="true" />
                  <Eye v-else :size="17" aria-hidden="true" />
                </button>
              </div>
              <p v-if="visiblePasswordError('newPassword')" class="form-help">
                {{ passwordErrors.newPassword }}
              </p>
              <p v-else class="form-help">
                Use at least 8 characters and choose a password you have not used here.
              </p>
            </div>

            <div
              class="form-field"
              :class="{ 'form-field--error': visiblePasswordError('confirmPassword') }"
            >
              <label class="form-label" for="owner-confirm-password">Confirm New Password</label>
              <div class="owner-profile__password-wrap">
                <input
                  id="owner-confirm-password"
                  v-model="passwordForm.confirmPassword"
                  class="form-control"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  :aria-invalid="Boolean(visiblePasswordError('confirmPassword'))"
                />
                <button
                  type="button"
                  :aria-label="
                    showConfirmPassword ? 'Hide confirmed password' : 'Show confirmed password'
                  "
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <EyeOff v-if="showConfirmPassword" :size="17" aria-hidden="true" />
                  <Eye v-else :size="17" aria-hidden="true" />
                </button>
              </div>
              <p v-if="visiblePasswordError('confirmPassword')" class="form-help">
                {{ passwordErrors.confirmPassword }}
              </p>
            </div>
          </div>

          <footer class="owner-profile__panel-footer owner-profile__panel-footer--security">
            <span>Changing your password keeps the current session active.</span>
            <button class="btn btn--secondary" type="submit" :disabled="isChangingPassword">
              <KeyRound :size="17" aria-hidden="true" />
              {{ isChangingPassword ? 'Updating...' : 'Update Password' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup>
import {
  BadgeCheck,
  Building2,
  CalendarDays,
  Eye,
  EyeOff,
  KeyRound,
  LockKeyhole,
  Mail,
  Phone,
  Save,
  ShieldCheck,
  Undo2,
  UserRound,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import Toast from '../../components/common/Toast.vue'
import { useAuthStore } from '../../stores/authStore'
import { hasValidationErrors, isValidEmail, isValidIndianPhone } from '../../utils/validators'

const authStore = useAuthStore()
const { currentUser, isChangingPassword, isUpdatingProfile, passwordError, profileError } =
  storeToRefs(authStore)

const profileForm = reactive({ name: '', email: '', phone: '' })
const passwordForm = reactive({ currentPassword: '', newPassword: '', confirmPassword: '' })
const profileSubmitted = ref(false)
const passwordSubmitted = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const successMessage = ref('')
let successTimer = null

const initials = computed(() => {
  const words = String(currentUser.value?.name || 'Library Owner')
    .trim()
    .split(/\s+/)
  return words
    .slice(0, 2)
    .map((word) => word[0] || '')
    .join('')
    .toUpperCase()
})

const profileErrors = computed(() => ({
  name:
    profileForm.name.length < 2 || profileForm.name.length > 80
      ? 'Enter a name containing between 2 and 80 characters.'
      : '',
  email: isValidEmail(profileForm.email) ? '' : 'Enter a valid email address.',
  phone: isValidIndianPhone(profileForm.phone)
    ? ''
    : 'Enter a valid 10-digit Indian mobile number.',
}))

const passwordErrors = computed(() => ({
  currentPassword: passwordForm.currentPassword ? '' : 'Current password is required.',
  newPassword:
    passwordForm.newPassword.length < 8
      ? 'New password must contain at least 8 characters.'
      : passwordForm.newPassword === passwordForm.currentPassword
        ? 'New password must be different from the current password.'
        : '',
  confirmPassword: !passwordForm.confirmPassword
    ? 'Confirm your new password.'
    : passwordForm.confirmPassword === passwordForm.newPassword
      ? ''
      : 'Passwords must match.',
}))

const isProfileDirty = computed(() => {
  const user = currentUser.value || {}
  return (
    profileForm.name !== String(user.name || '') ||
    profileForm.email !== String(user.email || '') ||
    profileForm.phone !== String(user.phone || '')
  )
})

const profileErrorMessage = computed(() => getErrorMessage(profileError.value))
const passwordErrorMessage = computed(() => getErrorMessage(passwordError.value))

function getErrorMessage(error) {
  return error?.response?.data?.message || error?.message || ''
}

function visibleProfileError(field) {
  return profileSubmitted.value && profileErrors.value[field]
}

function visiblePasswordError(field) {
  return passwordSubmitted.value && passwordErrors.value[field]
}

function resetProfileForm() {
  const user = currentUser.value || {}
  profileForm.name = String(user.name || '')
  profileForm.email = String(user.email || '')
  profileForm.phone = String(user.phone || '')
  profileSubmitted.value = false
  authStore.clearProfileError()
}

function resetPasswordForm() {
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordSubmitted.value = false
  showCurrentPassword.value = false
  showNewPassword.value = false
  showConfirmPassword.value = false
}

function showSuccess(message) {
  successMessage.value = message
  window.clearTimeout(successTimer)
  successTimer = window.setTimeout(() => {
    successMessage.value = ''
  }, 3500)
}

function formatDate(value) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

async function saveProfile() {
  profileSubmitted.value = true
  if (hasValidationErrors(profileErrors.value) || !isProfileDirty.value) return

  try {
    await authStore.updateProfile({ ...profileForm })
    profileSubmitted.value = false
    showSuccess('Your profile details were updated successfully.')
  } catch {
    // Store-owned errors are rendered in the profile panel.
  }
}

async function savePassword() {
  passwordSubmitted.value = true
  if (hasValidationErrors(passwordErrors.value)) return

  try {
    await authStore.changePassword({
      currentPassword: passwordForm.currentPassword,
      newPassword: passwordForm.newPassword,
    })
    resetPasswordForm()
    showSuccess('Your account password was changed successfully.')
  } catch {
    // Store-owned errors are rendered in the security panel.
  }
}

watch(currentUser, resetProfileForm, { immediate: true })
onBeforeUnmount(() => window.clearTimeout(successTimer))
</script>

<style scoped>
.owner-profile {
  display: grid;
  gap: var(--space-6);
}

.owner-profile__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.owner-profile__header h1,
.owner-profile__header p {
  margin: 0;
}

.owner-profile__header h1 {
  margin-top: var(--space-1);
  font-size: var(--font-size-h2);
}

.owner-profile__header div > p:last-child {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}

.owner-profile__workspace {
  display: grid;
  grid-template-columns: minmax(240px, 310px) minmax(0, 1fr);
  align-items: start;
  gap: var(--space-5);
}

.owner-profile__identity {
  display: grid;
  justify-items: center;
  gap: var(--space-4);
  padding: var(--space-6);
  text-align: center;
}

.owner-profile__avatar {
  display: grid;
  width: 84px;
  height: 84px;
  place-items: center;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-text-inverse, #ffffff);
  font-size: var(--font-size-h2);
  font-weight: var(--font-weight-bold);
}

.owner-profile__identity-heading h2,
.owner-profile__identity-heading p {
  margin: 0;
}

.owner-profile__identity-heading h2 {
  font-size: var(--font-size-h4);
}

.owner-profile__identity-heading p {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  overflow-wrap: anywhere;
}

.owner-profile__identity .badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.owner-profile__facts {
  display: grid;
  width: 100%;
  gap: var(--space-3);
  margin: var(--space-2) 0 0;
  text-align: left;
}

.owner-profile__facts div {
  display: grid;
  gap: var(--space-1);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-divider);
}

.owner-profile__facts dt {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs, 12px);
}

.owner-profile__facts dd {
  margin: 0;
  font-weight: var(--font-weight-medium);
  overflow-wrap: anywhere;
}

.owner-profile__library-link {
  width: 100%;
}

.owner-profile__content {
  display: grid;
  min-width: 0;
  gap: var(--space-5);
}

.owner-profile__panel {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-sm);
}

.owner-profile__panel-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.owner-profile__panel-header > span {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--radius-md);
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.owner-profile__panel-header--security > span {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.owner-profile__panel-header h2,
.owner-profile__panel-header p {
  margin: 0;
}

.owner-profile__panel-header h2 {
  font-size: var(--font-size-h5);
}

.owner-profile__panel-header p {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.owner-profile__alert {
  margin: var(--space-4) var(--space-5) 0;
}

.owner-profile__panel-body {
  padding: var(--space-5);
}

.owner-profile__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.owner-profile__full {
  grid-column: 1 / -1;
}

.owner-profile__input-wrap,
.owner-profile__password-wrap {
  position: relative;
}

.owner-profile__input-wrap > svg {
  position: absolute;
  top: 50%;
  left: var(--space-3);
  z-index: 1;
  color: var(--color-text-muted);
  transform: translateY(-50%);
  pointer-events: none;
}

.owner-profile__input-wrap .form-control {
  padding-left: 40px;
}

.owner-profile__password-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}

.owner-profile__password-wrap .form-control {
  padding-right: 44px;
}

.owner-profile__password-wrap button {
  position: absolute;
  top: 1px;
  right: 1px;
  display: grid;
  width: 40px;
  height: 38px;
  place-items: center;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
}

.owner-profile__password-wrap button:hover {
  background: var(--color-hover);
  color: var(--color-text-primary);
}

.owner-profile__panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--color-divider);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.owner-profile__panel-footer > div {
  display: flex;
  gap: var(--space-3);
}

@media (max-width: 1050px) {
  .owner-profile__workspace {
    grid-template-columns: 1fr;
  }

  .owner-profile__identity {
    grid-template-columns: auto minmax(0, 1fr) auto;
    justify-items: start;
    text-align: left;
  }

  .owner-profile__avatar {
    width: 64px;
    height: 64px;
    font-size: var(--font-size-h4);
  }

  .owner-profile__facts {
    grid-column: 1 / -1;
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .owner-profile__library-link {
    grid-column: 1 / -1;
    width: auto;
  }
}

@media (max-width: 800px) {
  .owner-profile__password-grid {
    grid-template-columns: 1fr;
  }

  .owner-profile__facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .owner-profile__header,
  .owner-profile__panel-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .owner-profile__header > .btn {
    width: 100%;
  }

  .owner-profile__identity {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }

  .owner-profile__facts {
    grid-column: auto;
    grid-template-columns: 1fr;
  }

  .owner-profile__library-link {
    grid-column: auto;
    width: 100%;
  }

  .owner-profile__grid {
    grid-template-columns: 1fr;
  }

  .owner-profile__full {
    grid-column: auto;
  }

  .owner-profile__panel-header,
  .owner-profile__panel-body {
    padding: var(--space-4);
  }

  .owner-profile__alert {
    margin: var(--space-4) var(--space-4) 0;
  }

  .owner-profile__panel-footer > div {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .owner-profile__panel-footer--security .btn {
    width: 100%;
  }
}

@media (max-width: 420px) {
  .owner-profile__panel-footer > div {
    grid-template-columns: 1fr;
  }
}
</style>
