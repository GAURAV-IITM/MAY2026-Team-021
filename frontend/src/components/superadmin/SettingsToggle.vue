<template>
  <label class="settings-toggle" :class="`settings-toggle--${tone}`">
    <input
      :checked="modelValue"
      type="checkbox"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <span class="settings-toggle__control" aria-hidden="true"></span>
    <span class="settings-toggle__copy">
      <strong>{{ label }}</strong>
      <small>{{ description }}</small>
    </span>
  </label>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, required: true },
  description: { type: String, default: '' },
  tone: { type: String, default: 'default' },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.settings-toggle {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
}

.settings-toggle input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.settings-toggle__control {
  position: relative;
  width: 42px;
  height: 24px;
  border-radius: var(--radius-pill);
  background: var(--color-disabled);
  transition: background var(--transition-fast);
}

.settings-toggle__control::after {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: var(--radius-pill);
  background: #fff;
  box-shadow: var(--shadow-sm);
  content: '';
  transition: transform var(--transition-fast);
}

.settings-toggle input:checked + .settings-toggle__control {
  background: var(--color-primary);
}

.settings-toggle input:checked + .settings-toggle__control::after {
  transform: translateX(18px);
}

.settings-toggle input:focus-visible + .settings-toggle__control {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.settings-toggle--danger input:checked + .settings-toggle__control {
  background: var(--color-danger);
}

.settings-toggle__copy {
  display: grid;
}

.settings-toggle__copy small {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}
</style>
