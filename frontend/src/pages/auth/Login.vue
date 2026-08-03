<template>
  <section class="login-page" aria-labelledby="login-title">
    <header class="login-page__header">
      <p class="login-page__eyebrow">Account access</p>
      <h1 id="login-title">Sign in to your workspace</h1>
      <p>
        Owners, students, and super admins use the same secure sign-in. Your account opens the
        correct workspace automatically.
      </p>
    </header>

    <div class="login-page__roles" aria-label="Supported account roles">
      <span><Building2 :size="15" /> Library Owner</span>
      <span><GraduationCap :size="15" /> Student</span>
      <span><ShieldCheck :size="15" /> Super Admin</span>
    </div>

    <form class="login-page__form" novalidate @submit.prevent="handleSubmit">
      <div v-if="authError" class="alert alert--danger" role="alert">
        <p class="m-0">{{ authError }}</p>
      </div>

      <div class="form-field" :class="{ 'form-field--error': validationErrors.email }">
        <label class="form-label" for="email">
          Email address <span class="required-mark" aria-hidden="true">*</span>
        </label>
        <div class="login-page__input-wrap">
          <Mail :size="18" aria-hidden="true" />
          <input
            id="email"
            v-model.trim="form.email"
            class="form-input"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            required
            aria-required="true"
            :aria-invalid="Boolean(validationErrors.email)"
            :aria-describedby="validationErrors.email ? 'email-error' : undefined"
            @blur="validateEmailField"
            @input="clearEmailError"
          />
        </div>
        <p v-if="validationErrors.email" id="email-error" class="form-error" role="alert">
          {{ validationErrors.email }}
        </p>
      </div>

      <div class="form-field" :class="{ 'form-field--error': validationErrors.password }">
        <div class="login-page__label-row">
          <label class="form-label" for="password">
            Password <span class="required-mark" aria-hidden="true">*</span>
          </label>
          <RouterLink class="login-page__link" :to="{ name: 'forgotPassword' }"
            >Forgot password?</RouterLink
          >
        </div>
        <div class="login-page__input-wrap login-page__input-wrap--password">
          <LockKeyhole :size="18" aria-hidden="true" />
          <input
            id="password"
            v-model="form.password"
            class="form-input"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="Enter your password"
            required
            aria-required="true"
            :aria-invalid="Boolean(validationErrors.password)"
            :aria-describedby="validationErrors.password ? 'password-error' : undefined"
            @blur="validatePasswordField"
            @input="clearPasswordError"
          />
          <button
            class="login-page__password-toggle"
            type="button"
            :aria-pressed="String(showPassword)"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
            :title="showPassword ? 'Hide password' : 'Show password'"
            @click="showPassword = !showPassword"
          >
            <EyeOff v-if="showPassword" :size="18" aria-hidden="true" />
            <Eye v-else :size="18" aria-hidden="true" />
          </button>
        </div>
        <p v-if="validationErrors.password" id="password-error" class="form-error" role="alert">
          {{ validationErrors.password }}
        </p>
      </div>

      <label class="checkbox login-page__remember">
        <input v-model="form.rememberMe" type="checkbox" />
        <span>Keep me signed in on this device</span>
      </label>

      <button class="btn btn--primary login-page__submit" type="submit" :disabled="isLoading">
        <span v-if="isLoading" class="btn__loader" aria-hidden="true"></span>
        <LogIn v-else :size="18" aria-hidden="true" />
        <span>{{ isLoading ? 'Signing in...' : 'Sign In' }}</span>
      </button>
    </form>

    <section class="login-page__owner-callout" aria-label="Library owner registration">
      <div>
        <strong>Opening a new library?</strong>
        <span>Create an owner workspace for your library operations.</span>
      </div>
      <RouterLink :to="{ name: 'registerLibrary' }">
        Register Library <ArrowRight :size="16" aria-hidden="true" />
      </RouterLink>
    </section>
  </section>
</template>

<script setup>
import ArrowRight from '@lucide/vue/dist/esm/icons/arrow-right.mjs'
import Building2 from '@lucide/vue/dist/esm/icons/building-2.mjs'
import Eye from '@lucide/vue/dist/esm/icons/eye.mjs'
import EyeOff from '@lucide/vue/dist/esm/icons/eye-off.mjs'
import GraduationCap from '@lucide/vue/dist/esm/icons/graduation-cap.mjs'
import LockKeyhole from '@lucide/vue/dist/esm/icons/lock-keyhole.mjs'
import LogIn from '@lucide/vue/dist/esm/icons/log-in.mjs'
import Mail from '@lucide/vue/dist/esm/icons/mail.mjs'
import ShieldCheck from '@lucide/vue/dist/esm/icons/shield-check.mjs'
import { storeToRefs } from 'pinia'
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { getDashboardRouteForRole } from '../../guards/authGuard'
import { useAuthStore } from '../../stores/authStore'
import { hasValidationErrors, validateLoginForm } from '../../utils/validators'

const emit = defineEmits(['submit'])
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { currentRole, error, isLoading } = storeToRefs(authStore)
const showPassword = ref(false)
const form = reactive({ email: '', password: '', rememberMe: false })
const validationErrors = reactive({ email: '', password: '' })
const authError = computed(() => error.value?.response?.data?.message || error.value?.message || '')

function setValidationErrors(errors) {
  validationErrors.email = errors.email
  validationErrors.password = errors.password
}
function validateEmailField() {
  validationErrors.email = validateLoginForm({
    email: form.email,
    password: 'valid-password',
  }).email
}
function validatePasswordField() {
  validationErrors.password = validateLoginForm({
    email: 'valid@example.com',
    password: form.password,
  }).password
}
function clearEmailError() {
  if (validationErrors.email) validationErrors.email = ''
}
function clearPasswordError() {
  if (validationErrors.password) validationErrors.password = ''
}
function getRedirectDestination() {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//'))
    return redirect
  return { name: getDashboardRouteForRole(currentRole.value) }
}

async function handleSubmit() {
  const errors = validateLoginForm(form)
  setValidationErrors(errors)
  if (hasValidationErrors(errors)) return

  try {
    const response = await authStore.login({ ...form })
    emit('submit', response)
    await router.push(getRedirectDestination())
  } catch {
    // Store-owned authentication error state is rendered above the form.
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  gap: var(--space-6);
}
.login-page__header {
  display: grid;
  gap: var(--space-2);
}
.login-page__eyebrow {
  margin: 0;
  color: var(--color-primary);
  font-size: var(--font-size-label);
  font-weight: var(--font-weight-bold);
  text-transform: uppercase;
}
.login-page__header h1 {
  margin: 0;
  font-size: 34px;
  letter-spacing: 0;
}
.login-page__header p:last-child {
  margin: 0;
  color: var(--color-text-muted);
  line-height: var(--line-height-relaxed);
}
.login-page__roles {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.login-page__roles span {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 32px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  color: var(--color-text-secondary);
  font-size: var(--font-size-caption);
  font-weight: var(--font-weight-semibold);
}
.login-page__roles span:nth-child(1) svg {
  color: var(--color-primary);
}
.login-page__roles span:nth-child(2) svg {
  color: var(--color-success);
}
.login-page__roles span:nth-child(3) svg {
  color: var(--color-warning);
}
.login-page__form {
  display: grid;
  gap: var(--space-5);
}
.login-page__label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
.login-page__label-row .form-label {
  margin: 0;
}
.login-page__link {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-decoration: none;
}
.login-page__input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.login-page__input-wrap > svg {
  position: absolute;
  left: var(--space-4);
  z-index: 1;
  color: var(--color-text-muted);
  pointer-events: none;
}
.login-page__input-wrap .form-input {
  min-height: 50px;
  padding-left: 44px;
  border-radius: var(--radius-md);
}
.login-page__input-wrap--password .form-input {
  padding-right: 48px;
}
.login-page__password-toggle {
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
.login-page__password-toggle:hover {
  background: var(--color-hover);
  color: var(--color-text-primary);
}
.login-page__remember {
  width: fit-content;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
.login-page__submit {
  width: 100%;
  min-height: 48px;
}
.login-page__owner-callout {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding-top: var(--space-5);
  border-top: 1px solid var(--color-divider);
}
.login-page__owner-callout > div {
  display: grid;
  gap: var(--space-1);
}
.login-page__owner-callout span {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}
.login-page__owner-callout a {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  flex: 0 0 auto;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-decoration: none;
}
.form-error {
  margin: var(--space-1) 0 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}
@media (max-width: 520px) {
  .login-page__header h1 {
    font-size: 29px;
  }
  .login-page__owner-callout {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
