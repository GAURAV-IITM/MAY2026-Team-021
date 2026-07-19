<template>
  <div class="owner-landing">
    <header class="site-header" :class="{ 'site-header--solid': isScrolled || isMenuOpen }">
      <nav class="site-nav" aria-label="Main navigation">
        <RouterLink class="brand" :to="{ name: 'landing' }" aria-label="Smart Library App home">
          <span class="brand__mark" aria-hidden="true">SL</span>
          <span class="brand__name">Smart Library App</span>
        </RouterLink>

        <button
          class="mobile-menu-button"
          type="button"
          :aria-expanded="isMenuOpen"
          aria-controls="landing-navigation"
          :aria-label="isMenuOpen ? 'Close navigation' : 'Open navigation'"
          @click="isMenuOpen = !isMenuOpen"
        >
          <X v-if="isMenuOpen" :size="21" />
          <Menu v-else :size="21" />
        </button>

        <div id="landing-navigation" class="site-nav__content" :class="{ 'is-open': isMenuOpen }">
          <div class="site-nav__links">
            <a href="#operations" @click="closeMenu">Operations</a>
            <a href="#outcomes" @click="closeMenu">Outcomes</a>
            <a href="#getting-started" @click="closeMenu">Getting Started</a>
          </div>
          <div class="site-nav__actions">
            <RouterLink class="nav-login" :to="{ name: 'login' }" @click="closeMenu">Owner Login</RouterLink>
            <RouterLink class="btn btn--primary" :to="{ name: 'registerLibrary' }" @click="closeMenu">
              Create Library Account
            </RouterLink>
          </div>
        </div>
      </nav>
    </header>

    <main>
      <section class="hero" aria-labelledby="hero-title">
        <div class="hero__backdrop" aria-hidden="true"></div>
        <div class="hero__content">
          <p class="hero__eyebrow">Operations platform for study libraries</p>
          <h1 id="hero-title">Smart Library App</h1>
          <p class="hero__message">
            Run seats, shifts, students, and monthly fees from one clear workspace built for library owners.
          </p>
          <div class="hero__actions">
            <RouterLink class="btn btn--primary hero__primary-action" :to="{ name: 'registerLibrary' }">
              Start Managing Your Library
              <ArrowRight :size="18" aria-hidden="true" />
            </RouterLink>
            <RouterLink class="hero__login-action" :to="{ name: 'login' }">Sign in to your workspace</RouterLink>
          </div>

          <dl class="hero__signals" aria-label="Platform capabilities">
            <div><dt>Seat status</dt><dd>Live by shift</dd></div>
            <div><dt>Fee records</dt><dd>Month by month</dd></div>
            <div><dt>Access</dt><dd>Owner controlled</dd></div>
          </dl>
        </div>
        <p class="hero__image-caption">A clear view of every seat, shift, and operating decision.</p>
      </section>

      <section class="owner-strip" aria-label="Library owner priorities">
        <p>Built around the work owners do every day</p>
        <ul>
          <li><Check :size="16" /> Student records</li>
          <li><Check :size="16" /> Seat availability</li>
          <li><Check :size="16" /> Fee collection</li>
          <li><Check :size="16" /> Shift planning</li>
        </ul>
      </section>

      <section id="operations" class="section operations-section" aria-labelledby="operations-title">
        <div class="section-heading section-heading--split">
          <div>
            <p class="section-eyebrow">One operating system</p>
            <h2 id="operations-title">Run the whole library from one workspace</h2>
          </div>
          <p>
            Replace scattered registers and spreadsheets with connected records that stay useful throughout the day.
          </p>
        </div>

        <div class="operations-layout">
          <div class="operation-list">
            <article v-for="operation in operations" :key="operation.title" class="operation-item">
              <span class="operation-item__icon" :class="`operation-item__icon--${operation.tone}`">
                <component :is="operation.icon" :size="22" aria-hidden="true" />
              </span>
              <div>
                <h3>{{ operation.title }}</h3>
                <p>{{ operation.description }}</p>
              </div>
            </article>
          </div>

          <div class="workspace-preview" aria-label="Owner dashboard snapshot">
            <header class="workspace-preview__header">
              <div>
                <span class="workspace-preview__brand">Smart Library</span>
                <strong>Owner overview</strong>
              </div>
              <span class="workspace-preview__status"><span></span> Live</span>
            </header>
            <div class="workspace-preview__metrics">
              <div><span>Seats</span><strong>120</strong><small>Across 3 floors</small></div>
              <div><span>Active students</span><strong>94</strong><small>6 joined this month</small></div>
              <div><span>Fees collected</span><strong>82%</strong><small>Current month</small></div>
            </div>
            <div class="workspace-preview__body">
              <section class="shift-panel" aria-label="Shift occupancy preview">
                <div class="preview-title"><strong>Shift occupancy</strong><span>Today</span></div>
                <div v-for="shift in shiftPreview" :key="shift.name" class="shift-row">
                  <span>{{ shift.name }}</span>
                  <div><i :style="{ width: `${shift.value}%` }"></i></div>
                  <strong>{{ shift.value }}%</strong>
                </div>
              </section>
              <section class="activity-panel" aria-label="Recent activity preview">
                <div class="preview-title"><strong>Recent activity</strong><span>Latest</span></div>
                <ul>
                  <li><span class="activity-dot activity-dot--green"></span><div><strong>Payment recorded</strong><small>Riya Sen, July fee</small></div><time>9:42</time></li>
                  <li><span class="activity-dot activity-dot--blue"></span><div><strong>Seat request received</strong><small>Morning shift, B-12</small></div><time>9:18</time></li>
                  <li><span class="activity-dot activity-dot--amber"></span><div><strong>Seat marked maintenance</strong><small>Floor 2, C-04</small></div><time>8:55</time></li>
                </ul>
              </section>
            </div>
          </div>
        </div>
      </section>

      <section id="outcomes" class="outcomes-section" aria-labelledby="outcomes-title">
        <div class="outcomes-section__inner">
          <div class="section-heading section-heading--light">
            <p class="section-eyebrow">Built for daily control</p>
            <h2 id="outcomes-title">Know what needs attention before it becomes a problem</h2>
          </div>
          <div class="outcome-grid">
            <article v-for="outcome in outcomes" :key="outcome.title">
              <component :is="outcome.icon" :size="25" aria-hidden="true" />
              <strong>{{ outcome.title }}</strong>
              <p>{{ outcome.description }}</p>
            </article>
          </div>
        </div>
      </section>

      <section class="section capability-section" aria-labelledby="capabilities-title">
        <div class="section-heading section-heading--centered">
          <p class="section-eyebrow">Connected operations</p>
          <h2 id="capabilities-title">Every record supports the next decision</h2>
          <p>Manage the physical library and the people who use it without losing the history behind each change.</p>
        </div>
        <div class="capability-grid">
          <article v-for="capability in capabilities" :key="capability.title" class="capability-card">
            <component :is="capability.icon" :size="23" aria-hidden="true" />
            <h3>{{ capability.title }}</h3>
            <p>{{ capability.description }}</p>
          </article>
        </div>
      </section>

      <section id="getting-started" class="section start-section" aria-labelledby="start-title">
        <div class="section-heading section-heading--split">
          <div>
            <p class="section-eyebrow">A practical start</p>
            <h2 id="start-title">Set up the library in three focused steps</h2>
          </div>
          <p>Start with the structure you already operate. The workspace grows with your student and payment records.</p>
        </div>
        <ol class="start-steps">
          <li v-for="(step, index) in startSteps" :key="step.title">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <div><h3>{{ step.title }}</h3><p>{{ step.description }}</p></div>
          </li>
        </ol>
      </section>

      <section class="owner-cta" aria-labelledby="cta-title">
        <div>
          <p class="section-eyebrow">Ready for a clearer operating day?</p>
          <h2 id="cta-title">Give your library one reliable source of truth.</h2>
        </div>
        <div class="owner-cta__actions">
          <RouterLink class="btn btn--primary" :to="{ name: 'registerLibrary' }">Create Library Account</RouterLink>
          <RouterLink class="owner-cta__login" :to="{ name: 'login' }">Owner Login <ArrowRight :size="17" /></RouterLink>
        </div>
      </section>
    </main>

    <footer class="landing-footer">
      <div class="landing-footer__brand"><span class="brand__mark">SL</span><div><strong>Smart Library App</strong><span>Library operations, clearly managed.</span></div></div>
      <nav aria-label="Footer navigation"><a href="#operations">Operations</a><a href="#outcomes">Outcomes</a><RouterLink :to="{ name: 'login' }">Login</RouterLink></nav>
      <p>&copy; 2026 Smart Library App</p>
    </footer>
  </div>
</template>

<script setup>
import ArrowRight from '@lucide/vue/dist/esm/icons/arrow-right.mjs'
import Armchair from '@lucide/vue/dist/esm/icons/armchair.mjs'
import BarChart3 from '@lucide/vue/dist/esm/icons/chart-bar.mjs'
import Building2 from '@lucide/vue/dist/esm/icons/building-2.mjs'
import Check from '@lucide/vue/dist/esm/icons/check.mjs'
import Clock3 from '@lucide/vue/dist/esm/icons/clock-3.mjs'
import IndianRupee from '@lucide/vue/dist/esm/icons/indian-rupee.mjs'
import LayoutDashboard from '@lucide/vue/dist/esm/icons/layout-dashboard.mjs'
import Megaphone from '@lucide/vue/dist/esm/icons/megaphone.mjs'
import Menu from '@lucide/vue/dist/esm/icons/menu.mjs'
import ShieldCheck from '@lucide/vue/dist/esm/icons/shield-check.mjs'
import Users from '@lucide/vue/dist/esm/icons/users.mjs'
import X from '@lucide/vue/dist/esm/icons/x.mjs'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

const isScrolled = ref(false)
const isMenuOpen = ref(false)

const operations = [
  { title: 'Control physical seats', description: 'Create floors and seats, update maintenance status, and see availability for each shift.', icon: Armchair, tone: 'blue' },
  { title: 'Keep student records connected', description: 'Manage profiles, shifts, fees, and seat history without maintaining duplicate registers.', icon: Users, tone: 'green' },
  { title: 'Close the monthly fee cycle', description: 'Generate monthly records, track pending payments, and keep receipts ready for review.', icon: IndianRupee, tone: 'amber' },
  { title: 'Plan shifts without conflicts', description: 'Create operating shifts and understand how custom timings affect every seat.', icon: Clock3, tone: 'red' },
]

const outcomes = [
  { title: 'Fewer allocation conflicts', description: 'Shift-aware seat status helps prevent double booking and timing overlap.', icon: ShieldCheck },
  { title: 'Faster owner decisions', description: 'Current occupancy, dues, and requests surface in one operational view.', icon: BarChart3 },
  { title: 'A complete operating history', description: 'Changes remain traceable across students, seats, payments, and requests.', icon: LayoutDashboard },
]

const capabilities = [
  { title: 'Seat management', description: 'Floors, physical status, maintenance, and shift-based availability.', icon: Armchair },
  { title: 'Student management', description: 'Profiles, active shifts, fee status, and allocation history.', icon: Users },
  { title: 'Payment records', description: 'Monthly dues, completed payments, methods, and receipts.', icon: IndianRupee },
  { title: 'Owner dashboard', description: 'A focused view of occupancy, collections, activity, and attention items.', icon: LayoutDashboard },
  { title: 'Library communication', description: 'Announcements and updates for students using the portal.', icon: Megaphone },
  { title: 'Multi-library foundation', description: 'Role and library boundaries designed for clean platform-wide isolation.', icon: Building2 },
]

const shiftPreview = [
  { name: 'Morning', value: 78 },
  { name: 'Afternoon', value: 64 },
  { name: 'Evening', value: 51 },
]

const startSteps = [
  { title: 'Create the library workspace', description: 'Register the library and establish the owner account.' },
  { title: 'Add floors, seats, and shifts', description: 'Mirror the physical layout and the timings already in use.' },
  { title: 'Bring in students and fees', description: 'Start operating with connected records from the first allocation.' },
]

function handleScroll() { isScrolled.value = window.scrollY > 24 }
function closeMenu() { isMenuOpen.value = false }

onMounted(() => window.addEventListener('scroll', handleScroll, { passive: true }))
onBeforeUnmount(() => window.removeEventListener('scroll', handleScroll))
</script>

<style scoped>
.owner-landing { min-width: 0; overflow: clip; background: var(--color-background); color: var(--color-text-primary); }
.site-header { position: fixed; inset: 0 0 auto; z-index: var(--z-navbar); border-bottom: 1px solid transparent; color: var(--color-background); transition: background-color var(--transition-normal), border-color var(--transition-normal), color var(--transition-normal), box-shadow var(--transition-normal); }
.site-header--solid { border-color: var(--color-border); background: rgba(255, 255, 255, .98); box-shadow: var(--shadow-sm); color: var(--color-text-primary); }
.site-nav { display: flex; align-items: center; justify-content: space-between; width: min(100% - 40px, 1320px); min-height: 72px; margin: 0 auto; }
.brand { display: inline-flex; align-items: center; gap: var(--space-3); color: inherit; text-decoration: none; }
.brand:hover { color: inherit; text-decoration: none; }
.brand__mark { display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 38px; flex: 0 0 38px; border-radius: var(--radius-md); background: var(--color-primary); color: var(--color-background); font-size: var(--font-size-sm); font-weight: var(--font-weight-bold); }
.brand__name { font-size: var(--font-size-h5); font-weight: var(--font-weight-bold); }
.site-nav__content { display: flex; align-items: center; gap: var(--space-8); }
.site-nav__links, .site-nav__actions { display: flex; align-items: center; gap: var(--space-5); }
.site-nav__links a, .nav-login { color: inherit; font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); text-decoration: none; }
.site-nav__links a:hover, .nav-login:hover { color: var(--color-primary); text-decoration: none; }
.site-header:not(.site-header--solid) .site-nav__links a:hover, .site-header:not(.site-header--solid) .nav-login:hover { color: var(--color-background); opacity: .78; }
.mobile-menu-button { display: none; align-items: center; justify-content: center; width: 42px; height: 42px; padding: 0; border: 1px solid currentColor; border-radius: var(--radius-md); background: transparent; color: inherit; cursor: pointer; }

.hero { position: relative; display: grid; height: calc(100svh - 44px); min-height: 620px; align-items: center; overflow: hidden; background: url('/images/library-operations-hero.png') center center / cover no-repeat; color: var(--color-background); }
.hero__backdrop { position: absolute; inset: 0; background: rgba(8, 17, 30, .58); }
.hero__content { position: relative; z-index: 1; width: min(100% - 40px, 1320px); margin: 0 auto; padding-top: 72px; }
.hero__eyebrow, .section-eyebrow { margin: 0 0 var(--space-3); color: var(--color-primary); font-size: var(--font-size-label); font-weight: var(--font-weight-bold); letter-spacing: 0; text-transform: uppercase; }
.hero__eyebrow { color: #93c5fd; }
.hero h1 { max-width: 720px; margin: 0; color: var(--color-background); font-size: 64px; line-height: 1.05; letter-spacing: 0; }
.hero__message { max-width: 650px; margin: var(--space-5) 0 0; color: rgba(255, 255, 255, .86); font-size: 20px; line-height: 1.55; }
.hero__actions { display: flex; align-items: center; gap: var(--space-5); margin-top: var(--space-8); }
.hero__primary-action { min-height: 48px; padding-inline: var(--space-5); }
.hero__login-action { display: inline-flex; align-items: center; min-height: 44px; color: var(--color-background); font-weight: var(--font-weight-semibold); text-decoration: none; }
.hero__login-action:hover { color: #bfdbfe; text-decoration: none; }
.hero__signals { display: flex; width: fit-content; gap: 0; margin: var(--space-10) 0 0; }
.hero__signals div { display: grid; gap: var(--space-1); min-width: 150px; padding: 0 var(--space-5); border-left: 1px solid rgba(255, 255, 255, .32); }
.hero__signals div:first-child { padding-left: 0; border-left: 0; }
.hero__signals dt { color: rgba(255, 255, 255, .6); font-size: var(--font-size-caption); }
.hero__signals dd { margin: 0; font-weight: var(--font-weight-semibold); }
.hero__image-caption { position: absolute; right: max(20px, calc((100% - 1320px) / 2)); bottom: var(--space-5); z-index: 1; max-width: 320px; margin: 0; color: rgba(255, 255, 255, .72); font-size: var(--font-size-caption); text-align: right; }

.owner-strip { display: flex; align-items: center; justify-content: space-between; gap: var(--space-6); min-height: 88px; padding: var(--space-4) max(20px, calc((100% - 1320px) / 2)); border-bottom: 1px solid var(--color-divider); background: var(--color-background); }
.owner-strip p { margin: 0; font-weight: var(--font-weight-bold); }
.owner-strip ul { display: flex; flex-wrap: wrap; gap: var(--space-6); margin: 0; padding: 0; list-style: none; }
.owner-strip li { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.owner-strip svg { color: var(--color-success); }

.section { width: min(100% - 40px, 1200px); margin: 0 auto; padding-block: 104px; }
.section-heading h2 { max-width: 730px; margin: 0; font-size: 40px; line-height: var(--line-height-tight); letter-spacing: 0; }
.section-heading > p:not(.section-eyebrow), .section-heading--split > p { color: var(--color-text-muted); line-height: var(--line-height-relaxed); }
.section-heading--split { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(280px, .6fr); align-items: end; gap: var(--space-10); }
.section-heading--split > p { margin: 0; }
.section-heading--centered { display: grid; justify-items: center; text-align: center; }
.section-heading--centered > p:last-child { max-width: 670px; margin: var(--space-4) 0 0; }

.operations-layout { display: grid; grid-template-columns: minmax(300px, .75fr) minmax(0, 1.25fr); align-items: center; gap: var(--space-12); margin-top: var(--space-12); }
.operation-list { display: grid; }
.operation-item { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: var(--space-4); padding: var(--space-5) 0; border-bottom: 1px solid var(--color-divider); }
.operation-item:first-child { padding-top: 0; }
.operation-item:last-child { border-bottom: 0; }
.operation-item__icon { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: var(--radius-md); }
.operation-item__icon--blue { background: var(--color-primary-light); color: var(--color-primary); }
.operation-item__icon--green { background: var(--color-success-light); color: var(--color-success); }
.operation-item__icon--amber { background: var(--color-warning-light); color: var(--color-warning); }
.operation-item__icon--red { background: var(--color-danger-light); color: var(--color-danger); }
.operation-item h3 { margin: 0; font-size: var(--font-size-h5); }
.operation-item p { margin: var(--space-2) 0 0; color: var(--color-text-muted); line-height: var(--line-height-relaxed); }

.workspace-preview { min-width: 0; overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-lg); }
.workspace-preview__header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-4) var(--space-5); border-bottom: 1px solid var(--color-divider); }
.workspace-preview__header > div { display: grid; gap: 2px; }
.workspace-preview__brand { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.workspace-preview__status { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-success); font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); }
.workspace-preview__status span { width: 8px; height: 8px; border-radius: var(--radius-pill); background: var(--color-success); }
.workspace-preview__metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-bottom: 1px solid var(--color-divider); background: var(--color-surface); }
.workspace-preview__metrics div { display: grid; gap: var(--space-1); padding: var(--space-5); border-right: 1px solid var(--color-divider); }
.workspace-preview__metrics div:last-child { border-right: 0; }
.workspace-preview__metrics span, .workspace-preview__metrics small { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.workspace-preview__metrics strong { font-size: var(--font-size-h3); }
.workspace-preview__body { display: grid; grid-template-columns: 1.05fr .95fr; }
.shift-panel, .activity-panel { min-width: 0; padding: var(--space-5); }
.shift-panel { border-right: 1px solid var(--color-divider); }
.preview-title { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-bottom: var(--space-5); }
.preview-title span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.shift-row { display: grid; grid-template-columns: 72px minmax(80px, 1fr) 38px; align-items: center; gap: var(--space-3); margin-top: var(--space-4); font-size: var(--font-size-sm); }
.shift-row > div { height: 8px; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-secondary); }
.shift-row i { display: block; height: 100%; border-radius: inherit; background: var(--color-primary); }
.shift-row strong { text-align: right; }
.activity-panel ul { display: grid; gap: var(--space-4); margin: 0; padding: 0; list-style: none; }
.activity-panel li { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--space-3); }
.activity-panel li > div { display: grid; gap: 2px; min-width: 0; }
.activity-panel li strong { overflow: hidden; font-size: var(--font-size-sm); text-overflow: ellipsis; white-space: nowrap; }
.activity-panel li small, .activity-panel time { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.activity-dot { width: 8px; height: 8px; border-radius: var(--radius-pill); }
.activity-dot--green { background: var(--color-success); }.activity-dot--blue { background: var(--color-primary); }.activity-dot--amber { background: var(--color-warning); }

.outcomes-section { background: #17202d; color: var(--color-background); }
.outcomes-section__inner { width: min(100% - 40px, 1200px); margin: 0 auto; padding-block: 96px; }
.section-heading--light h2 { color: var(--color-background); }
.outcome-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-8); margin-top: var(--space-12); }
.outcome-grid article { display: grid; gap: var(--space-4); padding-top: var(--space-5); border-top: 2px solid; }
.outcome-grid article:nth-child(1) { border-color: #60a5fa; }.outcome-grid article:nth-child(2) { border-color: #4ade80; }.outcome-grid article:nth-child(3) { border-color: #fbbf24; }
.outcome-grid svg { color: #93c5fd; }.outcome-grid article:nth-child(2) svg { color: #86efac; }.outcome-grid article:nth-child(3) svg { color: #fde68a; }
.outcome-grid strong { font-size: var(--font-size-h4); }
.outcome-grid p { margin: 0; color: #cbd5e1; line-height: var(--line-height-relaxed); }

.capability-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-4); margin-top: var(--space-10); }
.capability-card { padding: var(--space-6); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); }
.capability-card svg { color: var(--color-primary); }
.capability-card:nth-child(2) svg, .capability-card:nth-child(5) svg { color: var(--color-success); }
.capability-card:nth-child(3) svg, .capability-card:nth-child(6) svg { color: var(--color-warning); }
.capability-card h3 { margin: var(--space-5) 0 0; font-size: var(--font-size-h5); }
.capability-card p { margin: var(--space-2) 0 0; color: var(--color-text-muted); line-height: var(--line-height-relaxed); }

.start-section { border-top: 1px solid var(--color-divider); }
.start-steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-8); margin: var(--space-12) 0 0; padding: 0; list-style: none; counter-reset: steps; }
.start-steps li { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: start; gap: var(--space-4); }
.start-steps > li > span { color: var(--color-primary); font-family: var(--font-family-mono); font-size: var(--font-size-h4); font-weight: var(--font-weight-bold); }
.start-steps h3 { margin: 0; font-size: var(--font-size-h5); }
.start-steps p { margin: var(--space-2) 0 0; color: var(--color-text-muted); line-height: var(--line-height-relaxed); }

.owner-cta { display: flex; align-items: center; justify-content: space-between; gap: var(--space-10); padding: 72px max(20px, calc((100% - 1200px) / 2)); background: var(--color-primary-light); }
.owner-cta h2 { max-width: 680px; margin: 0; font-size: 36px; line-height: var(--line-height-tight); }
.owner-cta__actions { display: flex; align-items: center; gap: var(--space-5); flex: 0 0 auto; }
.owner-cta__login { display: inline-flex; align-items: center; gap: var(--space-2); color: var(--color-text-primary); font-weight: var(--font-weight-semibold); text-decoration: none; }
.landing-footer { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: var(--space-6); padding: var(--space-8) max(20px, calc((100% - 1320px) / 2)); background: #111827; color: var(--color-background); }
.landing-footer__brand { display: flex; align-items: center; gap: var(--space-3); }
.landing-footer__brand > div { display: grid; gap: 2px; }.landing-footer__brand span:last-child { color: #9ca3af; font-size: var(--font-size-caption); }
.landing-footer nav { display: flex; gap: var(--space-5); }.landing-footer nav a { color: #d1d5db; font-size: var(--font-size-sm); text-decoration: none; }.landing-footer nav a:hover { color: var(--color-background); }
.landing-footer p { justify-self: end; margin: 0; color: #9ca3af; font-size: var(--font-size-caption); }

@media (max-width: 1040px) {
  .site-nav__links { display: none; }
  .operations-layout { grid-template-columns: 1fr; }
  .operation-list { grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: var(--space-8); }
  .workspace-preview { width: 100%; }
  .landing-footer { grid-template-columns: 1fr auto; }.landing-footer p { grid-column: 1 / -1; justify-self: start; }
}

@media (max-width: 760px) {
  .site-nav { width: min(100% - 32px, 1320px); min-height: 64px; }
  .mobile-menu-button { display: inline-flex; }
  .site-nav__content { position: absolute; top: 64px; left: 0; right: 0; display: none; align-items: stretch; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-border); background: var(--color-background); color: var(--color-text-primary); box-shadow: var(--shadow-md); }
  .site-nav__content.is-open { display: flex; flex-direction: column; align-items: stretch; }
  .site-nav__links, .site-nav__actions { display: flex; align-items: stretch; flex-direction: column; gap: 0; }
  .site-nav__links a, .nav-login { padding: var(--space-3) 0; }
  .site-header:not(.site-header--solid) .site-nav__links a:hover, .site-header:not(.site-header--solid) .nav-login:hover { color: var(--color-primary); opacity: 1; }
  .hero { height: calc(100svh - 40px); min-height: 0; background-position: 62% center; }
  .hero__content { width: calc(100% - 32px); padding-top: 64px; }
  .hero h1 { font-size: 44px; }
  .hero__message { max-width: 520px; font-size: 17px; }
  .hero__actions { align-items: stretch; flex-direction: column; gap: var(--space-3); }
  .hero__primary-action, .hero__login-action { width: 100%; justify-content: center; }
  .hero__signals { width: 100%; margin-top: var(--space-6); }
  .hero__signals div { min-width: 0; flex: 1; padding-inline: var(--space-3); }
  .hero__image-caption { display: none; }
  .owner-strip { align-items: flex-start; flex-direction: column; padding-block: var(--space-5); }
  .owner-strip ul { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); width: 100%; gap: var(--space-3); }
  .section { padding-block: 72px; }
  .section-heading--split { grid-template-columns: 1fr; gap: var(--space-4); }
  .section-heading h2 { font-size: 32px; }
  .operation-list { grid-template-columns: 1fr; }
  .workspace-preview__body { grid-template-columns: 1fr; }
  .shift-panel { border-right: 0; border-bottom: 1px solid var(--color-divider); }
  .outcome-grid, .capability-grid, .start-steps { grid-template-columns: 1fr; }
  .outcomes-section__inner { padding-block: 72px; }
  .owner-cta { align-items: flex-start; flex-direction: column; padding-block: var(--space-12); }
  .owner-cta h2 { font-size: 30px; }
  .landing-footer { grid-template-columns: 1fr; }.landing-footer nav { flex-wrap: wrap; }.landing-footer p { grid-column: auto; }
}

@media (max-width: 480px) {
  .brand__name { font-size: var(--font-size-body); }
  .hero__content { padding-top: 52px; }
  .hero h1 { font-size: 38px; }
  .hero__message { margin-top: var(--space-3); font-size: 15px; }
  .hero__actions { margin-top: var(--space-5); }
  .hero__signals { display: none; }
  .owner-strip ul { grid-template-columns: 1fr; }
  .workspace-preview__metrics { grid-template-columns: 1fr; }
  .workspace-preview__metrics div { border-right: 0; border-bottom: 1px solid var(--color-divider); }
  .workspace-preview__metrics div:last-child { border-bottom: 0; }
  .owner-cta__actions { align-items: stretch; flex-direction: column; width: 100%; }.owner-cta__actions .btn, .owner-cta__login { width: 100%; justify-content: center; }
}
</style>
