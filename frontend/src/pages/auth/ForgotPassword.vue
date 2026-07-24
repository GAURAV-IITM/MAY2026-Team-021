<template>
  <section class="forgot-page" aria-labelledby="forgot-title">
    <header class="forgot-page__header">
      <div class="forgot-page__logo" aria-hidden="true"><KeyRound :size="27" /></div>
      <p class="text-label text-muted m-0">Smart Library App</p>
      <h1 id="forgot-title" class="forgot-page__title">Reset your password</h1>
      <p class="forgot-page__description">
        Enter the email linked to your account and we will send password reset instructions.
      </p>
    </header>

    <div v-if="isSubmitted" class="alert alert--success" role="status">
      <MailCheck :size="20" aria-hidden="true" />
      <div>
        <p class="text-label m-0">Check your inbox</p>
        <p class="m-0">
          If this email is connected to an account, reset instructions will be sent shortly.
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
          {{ emailError || 'Use the email connected to your Smart Library account.' }}
        </p>
      </div>

      <button
        class="btn btn--primary btn--lg forgot-page__submit"
        type="submit"
        :disabled="isLoading"
      >
        <span v-if="isLoading" class="btn__loader" aria-hidden="true"></span>
        <Send v-else :size="18" aria-hidden="true" />
        <span>{{ isLoading ? 'Preparing link' : 'Send Reset Link' }}</span>
      </button>

      <RouterLink class="btn btn--outline btn--lg forgot-page__back-link" :to="{ name: 'login' }">
        <ArrowLeft :size="18" aria-hidden="true" /> Back to Login
      </RouterLink>
    </form>
  </section>
</template>

<script setup>
import { ArrowLeft, KeyRound, MailCheck, Send } from '@lucide/vue'
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
  // TODO: Connect this submit to the backend password-reset endpoint when available.
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

  width: 60px;
  height: 60px;

  border: 1px solid var(--color-border);
  border-radius: 16px;

  background: var(--color-primary-light);
  color: var(--color-primary);

  font-weight: 700;
  letter-spacing: 0.5px;

  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.forgot-page__logo:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
}

.forgot-page__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-h2);
  font-weight: 700;
  line-height: 1.2;
}

.forgot-page__description {
  margin: 0;
  color: var(--color-text-muted);
  text-align: center;
  line-height: 1.5;
}

.forgot-page__form {
  display: grid;
  gap: var(--space-5);
}

.form-label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 600;
}

.form-control {
  border-radius: 10px;

  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.form-control:hover {
  border-color: var(--color-primary);
}

.form-control:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.08);
}

.form-help {
  margin-top: 0.35rem;
}

.forgot-page__submit,
.forgot-page__back-link {
  width: 100%;
  border-radius: 10px;

  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.forgot-page__submit:hover,
.forgot-page__back-link:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
}

.forgot-page__submit:active,
.forgot-page__back-link:active {
  transform: translateY(0);
}

.btn__loader {
  margin-right: 0.5rem;
}

@media (max-width: 480px) {
  .forgot-page {
    gap: var(--space-5);
  }

  .forgot-page__logo {
    width: 56px;
    height: 56px;
  }
}
</style>

<!--
src/pages/auth: Authentication and onboarding route pages.
TODO:
- Connect submit to FastAPI password reset integration in a future milestone.
-->
