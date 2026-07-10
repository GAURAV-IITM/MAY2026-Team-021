<template>
  <div class="error-page">
    <div class="error-card">
      <div class="error-code">{{ code }}</div>

      <h1>{{ title }}</h1>

      <p>{{ description }}</p>

      <div class="actions">
        <router-link :to="{ name: 'landing' }" class="primary-btn">
          Go Home
        </router-link>

        <router-link :to="{ name: 'login' }" class="secondary-btn">
          Login
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  code: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
})
</script>

<style scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #f8fafc;
}

.error-card {
  max-width: 650px;
  width: 100%;
  background: #ffffff;
  padding: 3rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0,0,0,.08);
}

.error-code {
  font-size: 5rem;
  font-weight: 800;
  color: #2563eb;
  margin-bottom: 1rem;
}

h1 {
  margin-bottom: 1rem;
  color: #1e293b;
}

p {
  color: #64748b;
  line-height: 1.7;
  margin-bottom: 2rem;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn {
  text-decoration: none;
  padding: .85rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
}

.primary-btn {
  background: #2563eb;
  color: white;
}

.primary-btn:hover {
  background: #1d4ed8;
}

.secondary-btn {
  border: 2px solid #2563eb;
  color: #2563eb;
}
</style>