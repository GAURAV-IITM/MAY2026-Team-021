<template>
  <section class="login-page" aria-labelledby="login-title">
    <header class="login-page__header">
      <div class="login-page__logo" aria-hidden="true">SLA</div>
      <p class="text-label text-muted m-0">Smart Library App</p>
      <h1 id="login-title" class="login-page__title">Welcome back</h1>
      <p class="login-page__description">Sign in to manage your study library workspace.</p>
    </header>

    <form class="login-page__form" novalidate @submit.prevent="handleSubmit">
      <div v-if="authError" class="alert alert--danger" role="alert">
        <p class="m-0">{{ authError }}</p>
      </div>

      <div class="form-field">
        <label class="form-label" for="email">Email address</label>

        <input
          id="email"
          v-model="form.email"
          class="form-control"
          :class="{ 'form-control--error': validationErrors.email }"
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
          :aria-invalid="Boolean(validationErrors.email)"
          :aria-describedby="validationErrors.email ? 'email-error' : undefined"
          @blur="validateEmailField"
          @input="clearEmailError"
        />

        <p
          v-if="validationErrors.email"
          id="email-error"
          class="form-error"
          role="alert"
        >
          {{ validationErrors.email }}
        </p>
      </div>

      <div class="form-field">
        <label class="form-label" for="password">Password</label>

        <div class="login-page__password-field">
          <input
            id="password"
            v-model="form.password"
            class="form-control"
            :class="{ 'form-control--error': validationErrors.password }"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="Enter your password"
            :aria-invalid="Boolean(validationErrors.password)"
            :aria-describedby="validationErrors.password ? 'password-error' : undefined"
            @blur="validatePasswordField"
            @input="clearPasswordError"
          />

          <button
            class="btn btn--ghost btn--sm login-page__password-toggle"
            type="button"
            :aria-pressed="String(showPassword)"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? 'Hide' : 'Show' }}
          </button>
        </div>

        <p
          v-if="validationErrors.password"
          id="password-error"
          class="form-error"
          role="alert"
        >
          {{ validationErrors.password }}
        </p>
      </div>

      <div class="login-page__options">
        <label class="checkbox">
          <input v-model="form.rememberMe" type="checkbox" />
          <span>Remember me</span>
        </label>

        <RouterLink class="login-page__link" :to="{ name: 'forgotPassword' }">
          Forgot password?
        </RouterLink>
      </div>

      <button
        class="btn btn--primary btn--lg login-page__submit"
        type="submit"
        :disabled="isLoading"
      >
        <span v-if="isLoading" class="btn__loader" aria-hidden="true"></span>
        <span>{{ isLoading ? 'Signing in' : 'Login' }}</span>
      </button>

      <RouterLink
        class="btn btn--outline btn--lg login-page__register"
        :to="{ name: 'registerLibrary' }"
      >
        Register Library
      </RouterLink>
    </form>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { getDashboardRouteForRole } from '../../guards/authGuard'
import { useAuthStore } from '../../stores/authStore'
import {
  hasValidationErrors,
  validateLoginForm,
} from '../../utils/validators'

const emit = defineEmits(['submit'])

const router = useRouter()
const authStore = useAuthStore()
const { currentRole, error, isLoading } = storeToRefs(authStore)

const showPassword = ref(false)

const form = reactive({
  email: '',
  password: '',
  rememberMe: false,
})

const validationErrors = reactive({
  email: '',
  password: '',
})

const authError = computed(() => {
  return error.value?.response?.data?.message || error.value?.message || ''
})


function setValidationErrors(errors) {
  validationErrors.email = errors.email
  validationErrors.password = errors.password
}

function validateEmailField() {
  const errors = validateLoginForm({
    email: form.email,
    password: 'valid-password',
  })

  validationErrors.email = errors.email
}

function validatePasswordField() {
  const errors = validateLoginForm({
    email: 'valid@example.com',
    password: form.password,
  })

  validationErrors.password = errors.password
}

function clearEmailError() {
  if (validationErrors.email) {
    validationErrors.email = ''
  }
}

function clearPasswordError() {
  if (validationErrors.password) {
    validationErrors.password = ''
  }
}

async function handleSubmit() {
  const errors = validateLoginForm(form)
  setValidationErrors(errors)

  if (hasValidationErrors(errors)) {
    return
  }

  try {
    const response = await authStore.login({ ...form })
    emit('submit', response)

    await router.push({
      name: getDashboardRouteForRole(currentRole.value),
    })
  } catch {
    // Store-owned authentication error state is rendered above the form.
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.login-page__header {
  display: grid;
  justify-items: center;
  gap: var(--space-2);
  text-align: center;
}

.login-page__logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
}

.login-page__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-h2);
  line-height: var(--line-height-tight);
}

.login-page__description {
  margin: 0;
  color: var(--color-text-muted);
}

.login-page__form {
  display: grid;
  gap: var(--space-5);
}

.login-page__password-field {
  position: relative;
}

.login-page__password-field .form-control {
  padding-right: 88px;
}

.login-page__password-toggle {
  position: absolute;
  top: 4px;
  right: 4px;
}

.login-page__options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.login-page__link {
  font-weight: var(--font-weight-medium);
}

.login-page__submit,
.login-page__register {
  width: 100%;
}

.form-error {
  margin: var(--space-1) 0 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.form-control--error {
  border-color: var(--color-danger);
}

@media (max-width: 480px) {
  .login-page {
    gap: var(--space-5);
  }

  .login-page__options {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--space-3);
  }
}
</style>