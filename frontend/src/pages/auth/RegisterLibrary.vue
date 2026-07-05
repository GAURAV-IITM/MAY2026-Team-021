<template>
  <section class="register-page" aria-labelledby="register-title">
    <header class="register-page__header">
      <div class="register-page__logo" aria-hidden="true">SLA</div>
      <p class="text-label text-muted m-0">Smart Library App</p>
      <h1 id="register-title" class="register-page__title">Register your library</h1>
      <p class="register-page__description">
        Create a workspace for your study library operations.
      </p>
    </header>

    <form class="register-page__form" novalidate @submit.prevent="handleSubmit">
      <div class="form-field" :class="{ 'form-field--error': validation.libraryName }">
        <label class="form-label" for="library-name">Library Name</label>
        <input
          id="library-name"
          v-model.trim="form.libraryName"
          class="form-control"
          type="text"
          autocomplete="organization"
          placeholder="Central Study Library"
          required
        />
        <p class="form-help">
          {{ validation.libraryName || 'Validation placeholder: library name is required.' }}
        </p>
      </div>

      <div class="form-field" :class="{ 'form-field--error': validation.ownerName }">
        <label class="form-label" for="owner-name">Owner Name</label>
        <input
          id="owner-name"
          v-model.trim="form.ownerName"
          class="form-control"
          type="text"
          autocomplete="name"
          placeholder="Owner full name"
          required
        />
        <p class="form-help">
          {{ validation.ownerName || 'Validation placeholder: owner name is required.' }}
        </p>
      </div>

      <div class="register-page__grid">
        <div class="form-field" :class="{ 'form-field--error': validation.email }">
          <label class="form-label" for="register-email">Email</label>
          <input
            id="register-email"
            v-model.trim="form.email"
            class="form-control"
            type="email"
            autocomplete="email"
            placeholder="owner@example.com"
            required
          />
          <p class="form-help">
            {{ validation.email || 'Validation placeholder: valid email is required.' }}
          </p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': validation.phone }">
          <label class="form-label" for="phone">Phone Number</label>
          <input
            id="phone"
            v-model.trim="form.phone"
            class="form-control"
            type="tel"
            autocomplete="tel"
            placeholder="+91 98765 43210"
            required
          />
          <p class="form-help">
            {{ validation.phone || 'Validation placeholder: phone number is required.' }}
          </p>
        </div>
      </div>

      <div class="form-field" :class="{ 'form-field--error': validation.address }">
        <label class="form-label" for="address">Address</label>
        <textarea
          id="address"
          v-model.trim="form.address"
          class="form-textarea"
          autocomplete="street-address"
          placeholder="Library address"
          required
        ></textarea>
        <p class="form-help">
          {{ validation.address || 'Validation placeholder: address is required.' }}
        </p>
      </div>

      <div class="register-page__grid">
        <div class="form-field" :class="{ 'form-field--error': validation.password }">
          <label class="form-label" for="register-password">Password</label>
          <div class="register-page__password-field">
            <input
              id="register-password"
              v-model="form.password"
              class="form-control"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="Create password"
              required
              minlength="8"
            />
            <button
              class="btn btn--ghost btn--sm register-page__password-toggle"
              type="button"
              :aria-pressed="String(showPassword)"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
          <p class="form-help">
            {{ validation.password || 'Validation placeholder: minimum 8 characters.' }}
          </p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': validation.confirmPassword }">
          <label class="form-label" for="confirm-password">Confirm Password</label>
          <div class="register-page__password-field">
            <input
              id="confirm-password"
              v-model="form.confirmPassword"
              class="form-control"
              :type="showConfirmPassword ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="Confirm password"
              required
            />
            <button
              class="btn btn--ghost btn--sm register-page__password-toggle"
              type="button"
              :aria-pressed="String(showConfirmPassword)"
              @click="showConfirmPassword = !showConfirmPassword"
            >
              {{ showConfirmPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
          <p class="form-help">
            {{ validation.confirmPassword || 'Validation placeholder: passwords should match.' }}
          </p>
        </div>
      </div>

      <div class="form-field" :class="{ 'form-field--error': validation.acceptTerms }">
        <label class="checkbox register-page__terms">
          <input v-model="form.acceptTerms" type="checkbox" required />
          <span>I agree to the terms and privacy policy placeholders.</span>
        </label>
        <p class="form-help">
          {{ validation.acceptTerms || 'Validation placeholder: terms must be accepted.' }}
        </p>
      </div>

      <button
        class="btn btn--primary btn--lg register-page__submit"
        type="submit"
        :disabled="isLoading"
      >
        <span v-if="isLoading" class="btn__loader" aria-hidden="true"></span>
        <span>{{ isLoading ? 'Registering' : 'Register Library' }}</span>
      </button>

      <p class="register-page__signin">
        Already have an account?
        <RouterLink :to="{ name: 'login' }">Login</RouterLink>
      </p>
    </form>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

const emit = defineEmits(['submit'])

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const isLoading = ref(false)

const form = reactive({
  libraryName: '',
  ownerName: '',
  email: '',
  phone: '',
  address: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
})

const validation = computed(() => ({
  libraryName: form.libraryName ? '' : 'Library name is required.',
  ownerName: form.ownerName ? '' : 'Owner name is required.',
  email: getEmailError(form.email),
  phone: form.phone ? '' : 'Phone number is required.',
  address: form.address ? '' : 'Address is required.',
  password: getPasswordError(form.password),
  confirmPassword: getConfirmPasswordError(),
  acceptTerms: form.acceptTerms ? '' : 'Please accept the terms.',
}))

function getEmailError(email) {
  if (!email) return 'Email is required.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Enter a valid email address.'
  return ''
}

function getPasswordError(password) {
  if (!password) return 'Password is required.'
  if (password.length < 8) return 'Password should be at least 8 characters.'
  return ''
}

function getConfirmPasswordError() {
  if (!form.confirmPassword) return 'Confirm password is required.'
  if (form.password !== form.confirmPassword) return 'Passwords must match.'
  return ''
}

function handleSubmit() {
  // TODO: Connect this placeholder submit to the future registration service/backend API.
  emit('submit', { ...form })
}
</script>

<style scoped>
.register-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.register-page__header {
  display: grid;
  justify-items: center;
  gap: var(--space-2);
  text-align: center;
}

.register-page__logo {
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

.register-page__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-h2);
  line-height: var(--line-height-tight);
}

.register-page__description,
.register-page__signin {
  margin: 0;
  color: var(--color-text-muted);
  text-align: center;
}

.register-page__form {
  display: grid;
  gap: var(--space-5);
}

.register-page__grid {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.register-page__password-field {
  position: relative;
}

.register-page__password-field .form-control {
  padding-right: 88px;
}

.register-page__password-toggle {
  position: absolute;
  top: 4px;
  right: 4px;
}

.register-page__terms {
  align-items: flex-start;
}

.register-page__submit {
  width: 100%;
}

@media (max-width: 640px) {
  .register-page__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .register-page {
    gap: var(--space-5);
  }
}
</style>

<!--
src/pages/auth: Authentication and onboarding route pages.
TODO:
- Replace placeholder validation with shared validators when form architecture is finalized.
- Connect registration submit to FastAPI backend integration in a future milestone.
-->
