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
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
          required
        />
        <p class="form-help">Validation placeholder: email is required and must be valid.</p>
      </div>

      <div class="form-field">
        <label class="form-label" for="password">Password</label>
        <div class="login-page__password-field">
          <input
            id="password"
            v-model="form.password"
            class="form-control"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="Enter your password"
            required
            minlength="8"
          />
          <button
            class="btn btn--ghost btn--sm login-page__password-toggle"
            type="button"
            :aria-pressed="String(showPassword)"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? 'Hide' : 'Show' }}
          </button>
        </div>
        <p class="form-help">Validation placeholder: password is required with minimum length.</p>
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

import { useAuthStore } from '../../stores/authStore'

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

const authError = computed(() => {
  return error.value?.response?.data?.message || error.value?.message || ''
})

function getDashboardRouteNameForRole(role) {
  const dashboardRoute = router.getRoutes().find((route) => {
    return route.meta?.role === role && route.meta?.title === 'Dashboard'
  })

  return dashboardRoute?.name || 'login'
}

async function handleSubmit() {
  // TODO: Replace mock authStore.login with FastAPI-backed authentication when backend is ready.
  try {
    const response = await authStore.login({ ...form })
    emit('submit', response)

    await router.push({ name: getDashboardRouteNameForRole(currentRole.value) })
  } catch {
    // Store-owned error state is rendered above the form.
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.login-page__header {
  display: grid;
  justify-items: center;
  gap: 0.75rem;
  text-align: center;
  margin-bottom: 0.5rem;
}

.login-page__logo {
  display: flex;
  align-items: center;
  justify-content: center;

  width: 72px;
  height: 72px;

  border: 1px solid var(--color-border);
  border-radius: 20px;

  background: linear-gradient(
    135deg,
    var(--color-primary-light),
    rgba(255, 255, 255, 0.9)
  );

  color: var(--color-primary);

  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: 1px;

  box-shadow:
    0 10px 24px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);

  transition: all 0.25s ease;
}

.login-page__logo:hover {
  transform: translateY(-2px);
}

.login-page__title {
  margin: 0;

  color: var(--color-text-primary);

  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 1.2;
}

.login-page__description {
  margin: 0;

  max-width: 340px;

  color: var(--color-text-muted);
  line-height: 1.6;
}

.login-page__form {
  display: grid;
  gap: 1.4rem;
}

.form-label {
  display: block;
  margin-bottom: 0.45rem;
  font-weight: 600;
}

.form-control {
  height: 50px;

  border-radius: 12px;

  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.15s ease;
}

.form-control:hover {
  border-color: var(--color-primary);
}

.form-control:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(0, 123, 255, 0.08);
}

.form-help {
  margin-top: 0.35rem;
  font-size: 0.82rem;
  color: var(--color-text-muted);
}

.login-page__password-field {
  position: relative;
}

.login-page__password-field .form-control {
  padding-right: 95px;
}

.login-page__password-toggle {
  position: absolute;
  top: 6px;
  right: 6px;

  height: 38px;
  min-width: 72px;

  border-radius: 10px;

  transition: all 0.2s ease;
}

.login-page__password-toggle:hover {
  transform: translateY(-1px);
}

.login-page__options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.login-page__link {
  font-weight: 600;
  text-decoration: none;
  transition: color 0.2s ease;
}

.login-page__link:hover {
  color: var(--color-primary);
}

.login-page__submit,
.login-page__register {
  width: 100%;
  border-radius: 12px;

  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.login-page__submit:hover,
.login-page__register:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.login-page__submit:active,
.login-page__register:active {
  transform: translateY(0);
}

.alert {
  border-radius: 12px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.checkbox input {
  width: 16px;
  height: 16px;
}

.btn__loader {
  margin-right: 0.5rem;
}

@media (max-width: 480px) {
  .login-page {
    gap: 1.6rem;
  }

  .login-page__logo {
    width: 64px;
    height: 64px;
    font-size: 1.2rem;
  }

  .login-page__title {
    font-size: 1.7rem;
  }

  .login-page__options {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.8rem;
  }
}
</style>

<!--
src/pages/auth: Authentication and onboarding route pages.
TODO:
- Replace placeholder validation messages with real validation state.
- Connect submit to authStore and backend authentication after APIs are available.
-->
