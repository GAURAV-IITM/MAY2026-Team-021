<template>
  <main class="error-page">
    <section class="error-card" :aria-labelledby="titleId">
      <p class="error-code m-0">{{ code }}</p>
      <h1 :id="titleId" class="text-h2 m-0">{{ title }}</h1>
      <p class="error-description m-0">{{ description }}</p>

      <nav class="error-actions" aria-label="Error page actions">
        <template v-for="action in actions" :key="action.label">
          <RouterLink
            v-if="action.to"
            :to="action.to"
            class="btn"
            :class="action.variant === 'primary' ? 'btn--primary' : 'btn--secondary'"
          >
            {{ action.label }}
          </RouterLink>
          <button
            v-else
            class="btn"
            :class="action.variant === 'primary' ? 'btn--primary' : 'btn--secondary'"
            type="button"
            @click="handleAction(action.action)"
          >
            {{ action.label }}
          </button>
        </template>
      </nav>
    </section>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const props = defineProps({
  code: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  actions: {
    type: Array,
    default: () => [
      { label: 'Go Home', to: { name: 'landing' }, variant: 'primary' },
    ],
  },
})

const router = useRouter()
const titleId = computed(() => `error-title-${props.code}`)

function handleAction(action) {
  if (action === 'reload') {
    window.location.reload()
    return
  }

  if (action === 'back' && window.history.length > 1) {
    router.back()
    return
  }

  void router.push({ name: 'landing' })
}
</script>

<style scoped>
.error-page {
  display: grid;
  min-height: 100dvh;
  place-items: center;
  padding: var(--space-6);
  background: var(--color-surface);
}

.error-card {
  display: grid;
  width: min(100%, 620px);
  justify-items: center;
  gap: var(--space-5);
  padding: var(--space-10);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-md);
  text-align: center;
}

.error-code {
  color: var(--color-primary);
  font-size: clamp(3.5rem, 12vw, 5rem);
  font-weight: var(--font-weight-bold);
  line-height: 1;
}

.error-description {
  max-width: 48ch;
  color: var(--color-text-muted);
  line-height: var(--line-height-relaxed);
}

.error-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-3);
}

@media (max-width: 520px) {
  .error-page { padding: var(--space-4); }
  .error-card { padding: var(--space-8) var(--space-5); }
  .error-actions { width: 100%; flex-direction: column; }
  .error-actions .btn { width: 100%; }
}
</style>
