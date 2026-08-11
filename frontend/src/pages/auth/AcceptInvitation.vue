<template>
  <section class="invitation-page" aria-labelledby="invitation-title">
    <div v-if="isLoading" class="invitation-page__loading">
      <LoadingSpinner label="Checking invitation" />
    </div>

    <template v-else>
      <header>
        <span class="invitation-page__icon"><KeyRound :size="24" /></span>
        <p class="text-label text-muted m-0">Account Activation</p>
        <h1 id="invitation-title">Create your password</h1>
        <p v-if="invitation" class="text-muted m-0">
          Welcome {{ invitation.name }}. Activate your {{ accountLabel }} account for
          {{ invitation.libraryName }}.
        </p>
      </header>

      <div v-if="errorMessage" class="alert alert--danger" role="alert">
        {{ errorMessage }}
      </div>

      <form v-if="invitation && !isComplete" novalidate @submit.prevent="submit">
        <div class="form-field">
          <label class="form-label" for="invitation-email">Email</label>
          <input
            id="invitation-email"
            class="form-control"
            :value="invitation.email"
            readonly
          />
        </div>
        <div class="form-field" :class="{ 'form-field--error': errors.password }">
          <label class="form-label" for="invitation-password">Password</label>
          <input
            id="invitation-password"
            v-model="password"
            class="form-control"
            type="password"
            autocomplete="new-password"
          />
          <p class="form-help">{{ errors.password || 'Use at least 8 characters.' }}</p>
        </div>
        <div class="form-field" :class="{ 'form-field--error': errors.confirmPassword }">
          <label class="form-label" for="invitation-confirm-password">
            Confirm Password
          </label>
          <input
            id="invitation-confirm-password"
            v-model="confirmPassword"
            class="form-control"
            type="password"
            autocomplete="new-password"
          />
          <p v-if="errors.confirmPassword" class="form-help">
            {{ errors.confirmPassword }}
          </p>
        </div>
        <button class="btn btn--primary" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Creating Password...' : 'Create Password' }}
        </button>
      </form>

      <div v-if="isComplete" class="invitation-page__complete">
        <CircleCheckBig :size="34" />
        <strong>Password created successfully</strong>
        <p class="text-muted m-0">You can now sign in to your {{ accountLabel }} account.</p>
        <RouterLink class="btn btn--primary" :to="{ name: 'login' }">Go to Login</RouterLink>
      </div>

      <RouterLink v-if="!invitation && !isLoading" class="btn btn--secondary" :to="{ name: 'login' }">
        Back to Login
      </RouterLink>
    </template>
  </section>
</template>

<script setup>
import { CircleCheckBig, KeyRound } from '@lucide/vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import {
  acceptAccountInvitation,
  validateAccountInvitation,
} from '../../services/authService.js'

const route = useRoute()
const token = String(route.query.token || '')
const invitation = ref(null)
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(true)
const isSubmitting = ref(false)
const isComplete = ref(false)
const errorMessage = ref('')
const errors = reactive({})
const accountLabel = computed(() => invitation.value?.role === 'library_owner' ? 'library owner' : 'student portal')

function validate() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (password.value.length < 8) {
    errors.password = 'Password must contain at least 8 characters.'
  }
  if (confirmPassword.value !== password.value) {
    errors.confirmPassword = 'Passwords do not match.'
  }
  return Object.keys(errors).length === 0
}

async function submit() {
  if (!validate()) return
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    await acceptAccountInvitation(token, password.value)
    isComplete.value = true
  } catch (error) {
    errorMessage.value = error.response?.data?.message || error.message
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  if (!token) {
    errorMessage.value = 'The invitation token is missing.'
    isLoading.value = false
    return
  }
  try {
    invitation.value = await validateAccountInvitation(token)
  } catch (error) {
    errorMessage.value = error.response?.data?.message || error.message
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.invitation-page { display: grid; width: min(100%, 480px); gap: var(--space-5); }
.invitation-page header { display: grid; gap: var(--space-2); text-align: center; }
.invitation-page h1 { margin: 0; font-size: var(--font-size-h2); }
.invitation-page__icon { display: grid; width: 48px; height: 48px; margin: 0 auto var(--space-2); place-items: center; border-radius: var(--radius-md); background: var(--color-primary-light); color: var(--color-primary); }
.invitation-page form { display: grid; gap: var(--space-4); }
.invitation-page__loading { display: grid; min-height: 280px; place-items: center; }
.invitation-page__complete { display: grid; justify-items: center; gap: var(--space-3); padding: var(--space-5); border: 1px solid var(--color-success); border-radius: var(--radius-md); color: var(--color-success); text-align: center; }
.invitation-page__complete p { color: var(--color-text-muted); }
.form-field--error .form-help { color: var(--color-danger); }
</style>
