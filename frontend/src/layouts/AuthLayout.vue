<template>
  <div class="auth-shell" :class="{ 'auth-shell--register': isRegistration }">
    <header class="auth-shell__topbar">
      <RouterLink class="auth-brand" :to="{ name: 'landing' }" aria-label="Smart Library App home">
        <span class="auth-brand__mark" aria-hidden="true"><LibraryBig :size="20" /></span>
        <span>Smart Library App</span>
      </RouterLink>
      <RouterLink class="auth-shell__home-link" :to="{ name: 'landing' }">
        <ArrowLeft :size="17" aria-hidden="true" />
        Back to home
      </RouterLink>
    </header>

    <div class="auth-shell__body">
      <aside class="auth-story" aria-label="Smart Library platform access">
        <div class="auth-story__backdrop" aria-hidden="true"></div>
        <div class="auth-story__content">
          <p class="auth-story__eyebrow">{{ story.eyebrow }}</p>
          <h2>{{ story.title }}</h2>
          <p class="auth-story__description">{{ story.description }}</p>
          <ul class="auth-story__roles">
            <li v-for="item in story.items" :key="item.title">
              <span><component :is="item.icon" :size="19" aria-hidden="true" /></span>
              <div><strong>{{ item.title }}</strong><small>{{ item.description }}</small></div>
            </li>
          </ul>
        </div>
        <p class="auth-story__caption">Secure access, scoped to every role and library.</p>
      </aside>

      <main class="auth-shell__main">
        <section class="auth-shell__form" :class="{ 'auth-shell__form--wide': isRegistration }">
          <slot><RouterView /></slot>
        </section>
        <footer class="auth-shell__footer">
          <ShieldCheck :size="15" aria-hidden="true" />
          Role-based access for owners, students, and platform administrators
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup>
import ArrowLeft from '@lucide/vue/dist/esm/icons/arrow-left.mjs'
import Armchair from '@lucide/vue/dist/esm/icons/armchair.mjs'
import Building2 from '@lucide/vue/dist/esm/icons/building-2.mjs'
import Clock3 from '@lucide/vue/dist/esm/icons/clock-3.mjs'
import IndianRupee from '@lucide/vue/dist/esm/icons/indian-rupee.mjs'
import LibraryBig from '@lucide/vue/dist/esm/icons/library-big.mjs'
import ShieldCheck from '@lucide/vue/dist/esm/icons/shield-check.mjs'
import Users from '@lucide/vue/dist/esm/icons/users.mjs'
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()
const isRegistration = computed(() => route.name === 'registerLibrary')
const story = computed(() => {
  if (isRegistration.value) {
    return {
      eyebrow: 'Library owner onboarding',
      title: 'Build the operating foundation your library needs.',
      description: 'Create the owner workspace first. Seats, shifts, students, and monthly records follow in one connected system.',
      items: [
        { title: 'Physical setup', description: 'Floors, seats, and availability', icon: Armchair },
        { title: 'Operating schedule', description: 'Default and custom shifts', icon: Clock3 },
        { title: 'Monthly control', description: 'Students, fees, and receipts', icon: IndianRupee },
      ],
    }
  }

  return {
    eyebrow: 'One secure sign-in',
    title: 'The right workspace opens for every role.',
    description: 'Use the account provided for your role. Smart Library App routes you to the tools and records you are allowed to access.',
    items: [
      { title: 'Library owners', description: 'Operations, students, seats, and fees', icon: Building2 },
      { title: 'Students', description: 'Seat, shift, receipts, and requests', icon: Users },
      { title: 'Super admins', description: 'Libraries, owners, and platform control', icon: ShieldCheck },
    ],
  }
})
</script>

<style scoped>
.auth-shell { min-height: 100svh; background: var(--color-background); }
.auth-shell__topbar { position: absolute; inset: 0 0 auto; z-index: 2; display: flex; align-items: center; justify-content: space-between; gap: var(--space-5); min-height: 72px; padding: var(--space-3) max(24px, calc((100% - 1400px) / 2)); color: var(--color-background); }
.auth-brand, .auth-shell__home-link { display: inline-flex; align-items: center; gap: var(--space-3); color: inherit; font-weight: var(--font-weight-bold); text-decoration: none; }
.auth-brand:hover, .auth-shell__home-link:hover { color: var(--color-background); text-decoration: none; opacity: .84; }
.auth-brand__mark { display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 38px; border-radius: var(--radius-md); background: var(--color-primary); color: var(--color-background); font-size: var(--font-size-sm); }
.auth-shell__home-link { font-size: var(--font-size-sm); }
.auth-shell__body { display: grid; grid-template-columns: minmax(430px, 42%) minmax(0, 1fr); min-height: 100svh; }
.auth-story { position: sticky; top: 0; display: flex; height: 100svh; min-height: 680px; align-items: center; overflow: hidden; padding: 110px max(44px, calc((100vw - 1400px) / 2)) 80px; background: url('/images/library-operations-hero.png') 61% center / cover no-repeat; color: var(--color-background); }
.auth-story__backdrop { position: absolute; inset: 0; background: rgba(8, 17, 30, .7); }
.auth-story__content { position: relative; z-index: 1; max-width: 540px; }
.auth-story__eyebrow { margin: 0 0 var(--space-3); color: #93c5fd; font-size: var(--font-size-label); font-weight: var(--font-weight-bold); text-transform: uppercase; }
.auth-story h2 { margin: 0; color: var(--color-background); font-size: 42px; line-height: var(--line-height-tight); letter-spacing: 0; }
.auth-story__description { margin: var(--space-5) 0 0; color: rgba(255, 255, 255, .78); font-size: var(--font-size-body-lg); line-height: var(--line-height-relaxed); }
.auth-story__roles { display: grid; gap: var(--space-4); margin: var(--space-8) 0 0; padding: 0; list-style: none; }
.auth-story__roles li { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: center; gap: var(--space-3); padding-top: var(--space-4); border-top: 1px solid rgba(255, 255, 255, .22); }
.auth-story__roles li > span { display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 38px; border-radius: var(--radius-md); background: rgba(255, 255, 255, .12); color: #bfdbfe; }
.auth-story__roles li > div { display: grid; gap: 2px; }
.auth-story__roles small { color: rgba(255, 255, 255, .62); }
.auth-story__caption { position: absolute; right: max(44px, calc((100vw - 1400px) / 2)); bottom: var(--space-6); z-index: 1; margin: 0; color: rgba(255, 255, 255, .55); font-size: var(--font-size-caption); }
.auth-shell__main { display: flex; min-width: 0; flex-direction: column; align-items: center; justify-content: center; padding: 104px clamp(32px, 7vw, 104px) var(--space-8); }
.auth-shell__form { width: min(100%, 470px); }
.auth-shell__form--wide { width: min(100%, 760px); padding-block: var(--space-8); }
.auth-shell__footer { display: flex; align-items: center; justify-content: center; gap: var(--space-2); margin-top: var(--space-8); color: var(--color-text-muted); font-size: var(--font-size-caption); text-align: center; }
.auth-shell__footer svg { flex: 0 0 auto; color: var(--color-success); }

@media (max-width: 900px) {
  .auth-shell__topbar { position: absolute; min-height: 64px; padding-inline: var(--space-5); }
  .auth-shell__body { grid-template-columns: 1fr; }
  .auth-story { position: relative; height: 330px; min-height: 330px; align-items: flex-end; padding: 92px var(--space-6) var(--space-6); background-position: center 48%; }
  .auth-story h2 { max-width: 680px; font-size: 32px; }
  .auth-story__description { max-width: 680px; margin-top: var(--space-3); }
  .auth-story__roles, .auth-story__caption { display: none; }
  .auth-shell__main { padding: var(--space-10) var(--space-5) var(--space-8); }
}

@media (max-width: 560px) {
  .auth-shell__home-link { gap: var(--space-1); font-size: var(--font-size-caption); }
  .auth-story { height: 210px; min-height: 210px; padding-inline: var(--space-5); }
  .auth-story h2 { font-size: 25px; }
  .auth-story__eyebrow, .auth-story__description { display: none; }
  .auth-shell--register .auth-story { height: 280px; min-height: 280px; }
  .auth-shell--register .auth-story__eyebrow, .auth-shell--register .auth-story__description { display: block; }
  .auth-shell--register .auth-story__description { font-size: var(--font-size-body); }
  .auth-shell__main { padding-inline: var(--space-4); }
}
</style>
