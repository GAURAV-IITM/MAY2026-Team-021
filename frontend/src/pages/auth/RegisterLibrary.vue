<template>
  <section class="register-page" aria-labelledby="register-title">
    <header class="register-page__header">
      <p class="register-page__eyebrow">Owner workspace</p>
      <h1 id="register-title">Register your library</h1>
      <p>
        Create the owner account and core library profile. Students and staff accounts are managed
        from the workspace later.
      </p>
    </header>

    <div v-if="authError" class="alert alert--danger" role="alert">
      <p class="m-0">{{ authError }}</p>
    </div>

    <form class="register-page__form" novalidate @submit.prevent="handleSubmit">
      <section class="register-section" aria-labelledby="library-details-title">
        <header>
          <span class="register-section__icon"><Building2 :size="19" /></span>
          <div>
            <h2 id="library-details-title">Library details</h2>
            <p>The identity and primary contact for this workspace.</p>
          </div>
        </header>
        <div class="register-section__fields">
          <div
            class="form-field register-section__full"
            :class="{ 'form-field--error': visibleError('libraryName') }"
          >
            <label class="form-label" for="library-name">Library name</label>
            <div class="register-page__input-wrap">
              <Building2 :size="18" /><input
                id="library-name"
                v-model.trim="form.libraryName"
                class="form-input"
                type="text"
                autocomplete="organization"
                placeholder="Central Study Library"
              />
            </div>
            <p v-if="visibleError('libraryName')" class="form-error">
              {{ validation.libraryName }}
            </p>
          </div>

          <div class="form-field" :class="{ 'form-field--error': visibleError('phone') }">
            <label class="form-label" for="phone">Library phone</label>
            <div class="register-page__input-wrap">
              <Phone :size="18" /><input
                id="phone"
                v-model.trim="form.phone"
                class="form-input"
                type="tel"
                autocomplete="tel"
                placeholder="98765 43210"
              />
            </div>
            <p v-if="visibleError('phone')" class="form-error">{{ validation.phone }}</p>
          </div>

          <div class="form-field" :class="{ 'form-field--error': visibleError('seatCount') }">
            <label class="form-label" for="seat-count">Current physical seats</label>
            <div class="register-page__input-wrap">
              <Armchair :size="18" /><input
                id="seat-count"
                v-model.number="form.seatCount"
                class="form-input"
                type="number"
                inputmode="numeric"
                min="1"
                max="1000"
                step="1"
                placeholder="Example: 120"
              />
            </div>
            <p v-if="visibleError('seatCount')" class="form-error">{{ validation.seatCount }}</p>
            <p v-else class="form-help">
              Available seats will be created on Floor 1 and can be reorganized later.
            </p>
          </div>

          <div
            class="form-field register-section__full"
            :class="{ 'form-field--error': visibleError('address') }"
          >
            <label class="form-label" for="address">Library address</label>
            <div class="register-page__input-wrap register-page__input-wrap--textarea">
              <MapPin :size="18" /><textarea
                id="address"
                v-model.trim="form.address"
                class="form-textarea"
                rows="3"
                autocomplete="street-address"
                placeholder="Full operating address"
              ></textarea>
            </div>
            <p v-if="visibleError('address')" class="form-error">{{ validation.address }}</p>
          </div>
        </div>
      </section>

      <section class="register-section" aria-labelledby="owner-account-title">
        <header>
          <span class="register-section__icon register-section__icon--green"
            ><UserRound :size="19"
          /></span>
          <div>
            <h2 id="owner-account-title">Owner account</h2>
            <p>These credentials provide administrative access to the library.</p>
          </div>
        </header>
        <div class="register-section__fields">
          <div class="form-field" :class="{ 'form-field--error': visibleError('ownerName') }">
            <label class="form-label" for="owner-name">Owner name</label>
            <div class="register-page__input-wrap">
              <UserRound :size="18" /><input
                id="owner-name"
                v-model.trim="form.ownerName"
                class="form-input"
                type="text"
                autocomplete="name"
                placeholder="Full name"
              />
            </div>
            <p v-if="visibleError('ownerName')" class="form-error">{{ validation.ownerName }}</p>
          </div>

          <div class="form-field" :class="{ 'form-field--error': visibleError('email') }">
            <label class="form-label" for="register-email">Owner email</label>
            <div class="register-page__input-wrap">
              <Mail :size="18" /><input
                id="register-email"
                v-model.trim="form.email"
                class="form-input"
                type="email"
                autocomplete="email"
                placeholder="owner@example.com"
              />
            </div>
            <p v-if="visibleError('email')" class="form-error">{{ validation.email }}</p>
          </div>

          <div class="form-field" :class="{ 'form-field--error': visibleError('password') }">
            <label class="form-label" for="register-password">Password</label>
            <div class="register-page__input-wrap register-page__input-wrap--password">
              <LockKeyhole :size="18" /><input
                id="register-password"
                v-model="form.password"
                class="form-input"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password"
                placeholder="Minimum 8 characters"
              />
              <button
                class="register-page__password-toggle"
                type="button"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                :title="showPassword ? 'Hide password' : 'Show password'"
                @click="showPassword = !showPassword"
              >
                <EyeOff v-if="showPassword" :size="18" /><Eye v-else :size="18" />
              </button>
            </div>
            <p v-if="visibleError('password')" class="form-error">{{ validation.password }}</p>
          </div>

          <div class="form-field" :class="{ 'form-field--error': visibleError('confirmPassword') }">
            <label class="form-label" for="confirm-password">Confirm password</label>
            <div class="register-page__input-wrap register-page__input-wrap--password">
              <LockKeyhole :size="18" /><input
                id="confirm-password"
                v-model="form.confirmPassword"
                class="form-input"
                :type="showConfirmPassword ? 'text' : 'password'"
                autocomplete="new-password"
                placeholder="Repeat your password"
              />
              <button
                class="register-page__password-toggle"
                type="button"
                :aria-label="showConfirmPassword ? 'Hide password' : 'Show password'"
                :title="showConfirmPassword ? 'Hide password' : 'Show password'"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <EyeOff v-if="showConfirmPassword" :size="18" /><Eye v-else :size="18" />
              </button>
            </div>
            <p v-if="visibleError('confirmPassword')" class="form-error">
              {{ validation.confirmPassword }}
            </p>
          </div>
        </div>
      </section>

      <div class="form-field" :class="{ 'form-field--error': visibleError('acceptTerms') }">
        <label class="checkbox register-page__terms"
          ><input v-model="form.acceptTerms" type="checkbox" /><span
            >I agree to the platform terms and privacy policy.</span
          ></label
        >
        <p v-if="visibleError('acceptTerms')" class="form-error">{{ validation.acceptTerms }}</p>
      </div>

      <button class="btn btn--primary register-page__submit" type="submit" :disabled="isLoading">
        <span v-if="isLoading" class="btn__loader" aria-hidden="true"></span>
        <Building2 v-else :size="18" aria-hidden="true" />
        <span>{{ isLoading ? 'Creating workspace...' : 'Create Owner Workspace' }}</span>
      </button>

      <p class="register-page__signin">
        Already have an owner, student, or super-admin account?
        <RouterLink :to="{ name: 'login' }">Sign in</RouterLink>
      </p>
    </form>
  </section>
</template>

<script setup>
import Building2 from '@lucide/vue/dist/esm/icons/building-2.mjs'
import Armchair from '@lucide/vue/dist/esm/icons/armchair.mjs'
import Eye from '@lucide/vue/dist/esm/icons/eye.mjs'
import EyeOff from '@lucide/vue/dist/esm/icons/eye-off.mjs'
import LockKeyhole from '@lucide/vue/dist/esm/icons/lock-keyhole.mjs'
import Mail from '@lucide/vue/dist/esm/icons/mail.mjs'
import MapPin from '@lucide/vue/dist/esm/icons/map-pin.mjs'
import Phone from '@lucide/vue/dist/esm/icons/phone.mjs'
import UserRound from '@lucide/vue/dist/esm/icons/user-round.mjs'
import { storeToRefs } from 'pinia'
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { getDashboardRouteForRole } from '../../guards/authGuard'
import { useAuthStore } from '../../stores/authStore'
import { hasValidationErrors, isRequired, isValidEmail } from '../../utils/validators'

const emit = defineEmits(['submit'])
const router = useRouter()
const authStore = useAuthStore()
const { currentRole, error, isLoading } = storeToRefs(authStore)
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const hasSubmitted = ref(false)
const form = reactive({
  libraryName: '',
  seatCount: '',
  ownerName: '',
  email: '',
  phone: '',
  address: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
})
const authError = computed(() => error.value?.response?.data?.message || error.value?.message || '')
const validation = computed(() => ({
  libraryName: isRequired(form.libraryName) ? '' : 'Library name is required.',
  ownerName: isRequired(form.ownerName) ? '' : 'Owner name is required.',
  email: !isRequired(form.email)
    ? 'Email is required.'
    : isValidEmail(form.email)
      ? ''
      : 'Enter a valid email address.',
  phone: getPhoneError(form.phone),
  seatCount: getSeatCountError(form.seatCount),
  address: isRequired(form.address) ? '' : 'Library address is required.',
  password: !form.password
    ? 'Password is required.'
    : form.password.length >= 8
      ? ''
      : 'Use at least 8 characters.',
  confirmPassword: !form.confirmPassword
    ? 'Confirm your password.'
    : form.password === form.confirmPassword
      ? ''
      : 'Passwords must match.',
  acceptTerms: form.acceptTerms ? '' : 'Please accept the terms and privacy policy.',
}))

function getPhoneError(value) {
  const digits = String(value || '').replace(/\D/g, '')
  const localNumber = digits.length === 12 && digits.startsWith('91') ? digits.slice(2) : digits
  if (!localNumber) return 'Phone number is required.'
  return /^[6-9]\d{9}$/.test(localNumber) ? '' : 'Enter a valid 10-digit Indian phone number.'
}
function getSeatCountError(value) {
  const count = Number(value)
  if (value === '' || value === null) return 'Current seat count is required.'
  return Number.isInteger(count) && count >= 1 && count <= 1000
    ? ''
    : 'Enter a whole number between 1 and 1000.'
}
function visibleError(field) {
  return hasSubmitted.value && Boolean(validation.value[field])
}

async function handleSubmit() {
  hasSubmitted.value = true
  if (hasValidationErrors(validation.value)) return

  try {
    const response = await authStore.register({ ...form })
    emit('submit', response)
    await router.push({ name: getDashboardRouteForRole(currentRole.value) })
  } catch {
    // Store-owned registration error state is rendered above the form.
  }
}
</script>

<style scoped>
.register-page {
  display: grid;
  gap: var(--space-6);
}
.register-page__header {
  display: grid;
  gap: var(--space-2);
}
.register-page__eyebrow {
  margin: 0;
  color: var(--color-primary);
  font-size: var(--font-size-label);
  font-weight: var(--font-weight-bold);
  text-transform: uppercase;
}
.register-page__header h1 {
  margin: 0;
  font-size: 34px;
  letter-spacing: 0;
}
.register-page__header > p:last-child {
  max-width: 650px;
  margin: 0;
  color: var(--color-text-muted);
  line-height: var(--line-height-relaxed);
}
.register-page__form {
  display: grid;
  gap: var(--space-6);
}
.register-section {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.register-section > header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-divider);
  background: var(--color-surface);
}
.register-section__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  border-radius: var(--radius-md);
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.register-section__icon--green {
  background: var(--color-success-light);
  color: var(--color-success);
}
.register-section header h2,
.register-section header p {
  margin: 0;
}
.register-section header h2 {
  font-size: var(--font-size-h5);
}
.register-section header p {
  margin-top: 2px;
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}
.register-section__fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-5);
  padding: var(--space-5);
}
.register-section__full {
  grid-column: 1 / -1;
}
.register-page__input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.register-page__input-wrap > svg {
  position: absolute;
  left: var(--space-4);
  z-index: 1;
  color: var(--color-text-muted);
  pointer-events: none;
}
.register-page__input-wrap .form-input,
.register-page__input-wrap .form-textarea {
  padding-left: 44px;
  border-radius: var(--radius-md);
}
.register-page__input-wrap .form-input {
  min-height: 48px;
}
.register-page__input-wrap--textarea {
  align-items: flex-start;
}
.register-page__input-wrap--textarea > svg {
  top: var(--space-4);
}
.register-page__input-wrap--password .form-input {
  padding-right: 48px;
}
.register-page__password-toggle {
  position: absolute;
  right: var(--space-2);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}
.register-page__password-toggle:hover {
  background: var(--color-hover);
  color: var(--color-text-primary);
}
.register-page__terms {
  align-items: flex-start;
  width: fit-content;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
.register-page__terms input {
  margin-top: 2px;
}
.register-page__submit {
  width: 100%;
  min-height: 48px;
}
.register-page__signin {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}
.register-page__signin a {
  font-weight: var(--font-weight-semibold);
  text-decoration: none;
}
.form-error {
  margin: var(--space-1) 0 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}
@media (max-width: 660px) {
  .register-section__fields {
    grid-template-columns: 1fr;
    padding: var(--space-4);
  }
  .register-section__full {
    grid-column: auto;
  }
  .register-page__header h1 {
    font-size: 29px;
  }
}
</style>
