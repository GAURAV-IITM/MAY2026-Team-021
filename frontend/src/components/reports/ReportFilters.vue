<template>
  <form class="report-filters" aria-label="Report filters" @submit.prevent="applyFilters">
    <div class="report-filters__fields">
      <label class="form-field">
        <span class="form-label">From month</span>
        <select v-model="draft.startMonth" class="form-select" :disabled="loading">
          <option v-for="month in options.months" :key="month.value" :value="month.value">
            {{ month.label }}
          </option>
        </select>
      </label>

      <label class="form-field">
        <span class="form-label">To month</span>
        <select v-model="draft.endMonth" class="form-select" :disabled="loading">
          <option v-for="month in options.months" :key="month.value" :value="month.value">
            {{ month.label }}
          </option>
        </select>
      </label>

      <label class="form-field">
        <span class="form-label">Floor</span>
        <select v-model="draft.floorId" class="form-select" :disabled="loading">
          <option value="">All floors</option>
          <option v-for="floor in options.floors" :key="floor.value" :value="floor.value">
            {{ floor.label }}
          </option>
        </select>
      </label>

      <label class="form-field report-filters__shift">
        <span class="form-label">Shift</span>
        <select v-model="draft.shiftId" class="form-select" :disabled="loading">
          <option value="">All shifts</option>
          <option v-for="shift in options.shifts" :key="shift.value" :value="shift.value">
            {{ shift.label }} · {{ shift.timing }}
          </option>
        </select>
      </label>
    </div>

    <p v-if="validationMessage" class="report-filters__error" role="alert">
      {{ validationMessage }}
    </p>

    <div class="report-filters__actions">
      <button class="btn btn--ghost" type="button" :disabled="loading" @click="resetFilters">
        <RotateCcw :size="16" aria-hidden="true" />
        Reset
      </button>
      <button class="btn btn--primary" type="submit" :disabled="loading || !hasChanges">
        <SlidersHorizontal :size="16" aria-hidden="true" />
        {{ loading ? 'Applying...' : 'Apply filters' }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { RotateCcw, SlidersHorizontal } from '@lucide/vue'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  options: {
    type: Object,
    default: () => ({ months: [], floors: [], shifts: [] }),
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['apply', 'reset'])
const draft = reactive({ startMonth: '', endMonth: '', floorId: '', shiftId: '' })
const validationMessage = ref('')

const hasChanges = computed(() => {
  return Object.keys(draft).some((key) => String(draft[key]) !== String(props.modelValue[key]))
})

watch(
  () => props.modelValue,
  (filters) => {
    Object.assign(draft, filters)
  },
  { immediate: true, deep: true },
)

function applyFilters() {
  if (!draft.startMonth || !draft.endMonth) {
    validationMessage.value = 'Select both a start month and an end month.'
    return
  }
  if (draft.startMonth > draft.endMonth) {
    validationMessage.value = 'The start month cannot be after the end month.'
    return
  }

  validationMessage.value = ''
  emit('apply', { ...draft })
}

function resetFilters() {
  validationMessage.value = ''
  emit('reset')
}
</script>

<style scoped>
.report-filters {
  position: sticky;
  top: calc(var(--layout-navbar-height) + var(--space-2));
  z-index: 12;
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(12px);
}

.report-filters__fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(130px, 0.7fr)) minmax(130px, 0.65fr) minmax(210px, 1.25fr);
  flex: 1;
  gap: var(--space-3);
}

.report-filters__actions {
  display: flex;
  gap: var(--space-2);
  flex: 0 0 auto;
}

.report-filters__error {
  order: 3;
  flex: 0 0 100%;
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

@media (max-width: 1100px) {
  .report-filters {
    align-items: stretch;
    flex-direction: column;
  }

  .report-filters__actions {
    justify-content: flex-end;
  }
}

@media (max-width: 720px) {
  .report-filters {
    position: static;
  }

  .report-filters__fields {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .report-filters__shift {
    grid-column: 1 / -1;
  }
}

@media (max-width: 480px) {
  .report-filters__fields {
    grid-template-columns: 1fr;
  }

  .report-filters__shift {
    grid-column: auto;
  }

  .report-filters__actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
