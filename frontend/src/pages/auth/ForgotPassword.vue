<template>
  <section class="forgot-page" aria-labelledby="forgot-title">
    <header class="forgot-page__header">
      <div class="forgot-page__logo" aria-hidden="true">SLA</div>
      <p class="text-label text-muted m-0">Smart Library App</p>
      <h1 id="forgot-title" class="forgot-page__title">Reset your password</h1>
      <p class="forgot-page__description">
        Enter your email and we will show a placeholder reset confirmation.
      </p>
    </header>

    <div v-if="isSubmitted" class="alert alert--success" role="status">
      <div>
        <p class="text-label m-0">Reset link placeholder</p>
        <p class="m-0">
          If this email is connected to an account, reset instructions will be sent later.
        </p>
      </div>
    </div>

    <form class="forgot-page__form" novalidate @submit.prevent="handleSubmit">
      <div class="form-field" :class="{ 'form-field--error': emailError }">
        <label class="form-label" for="forgot-email">Email field</label>
        <input
          id="forgot-email"
          v-model.trim="email"
          class="form-control"
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
          required
        />
        <p class="form-help">
          {{ emailError || 'Validation placeholder: email is required and must be valid.' }}
        </p>
      </div>

      <button
        class="btn btn--primary btn--lg forgot-page__submit"
        type="submit"
        :disabled="isLoading"
      >
        <span v-if="isLoading" class="btn__loader" aria-hidden="true"></span>
        <span>{{ isLoading ? 'Preparing link' : 'Send Reset Link' }}</span>
      </button>

      <RouterLink class="btn btn--outline btn--lg forgot-page__back-link" :to="{ name: 'login' }">
        Back to Login
      </RouterLink>
    </form>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'

const emit = defineEmits(['submit'])

const email = ref('')
const isLoading = ref(false)
const isSubmitted = ref(false)

const emailError = computed(() => {
  if (!email.value) return 'Email is required.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) return 'Enter a valid email address.'
  return ''
})

function handleSubmit() {
  // TODO: Connect this placeholder submit to the backend password-reset endpoint when available.
  isSubmitted.value = true
  emit('submit', { email: email.value })
}
</script>

<style scoped>
.forgot-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.forgot-page__header {
  display: grid;
  justify-items: center;
  gap: var(--space-2);
  text-align: center;
}

.forgot-page__logo {
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

.forgot-page__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-h2);
  line-height: var(--line-height-tight);
}

.forgot-page__description {
  margin: 0;
  color: var(--color-text-muted);
}

.forgot-page__form {
  display: grid;
  gap: var(--space-5);
}

.forgot-page__submit,
.forgot-page__back-link {
  width: 100%;
}

@media (max-width: 480px) {
  .forgot-page {
    gap: var(--space-5);
  }
}
</style>

<!--
src/pages/auth: Authentication and onboarding route pages.
TODO:
- Replace placeholder success message with real password-reset response handling.
- Connect submit to FastAPI password reset integration in a future milestone.
-->
