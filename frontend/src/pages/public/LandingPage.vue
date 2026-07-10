<template>
  <div class="landing-page">
    <header class="navbar">
      <div class="logo">
        <span class="logo-icon">📚</span>
        <span>Smart Library App</span>
      </div>

      <router-link class="login-btn" :to="{ name: 'login' }">
        Login
      </router-link>
    </header>

    <section class="hero">
      <div class="hero-content">
        <h1>Reserve Your Perfect Study Space</h1>

        <p>
          Study Spaces helps students quickly find, reserve and manage library
          study seats while providing administrators with real-time occupancy
          management.
        </p>

        <div class="hero-buttons">
          <router-link class="primary-btn" :to="{ name: 'login' }">
            Get Started
          </router-link>

          <a href="#features" class="secondary-btn">
            Learn More
          </a>
        </div>
      </div>

      <div class="hero-card">
        <div class="card">
          <h3>Live Seat Availability</h3>
          <p>View available study spaces instantly.</p>
        </div>

        <div class="card">
          <h3>Fast Reservations</h3>
          <p>Reserve a seat in just a few clicks.</p>
        </div>

        <div class="card">
          <h3>Admin Dashboard</h3>
          <p>Monitor occupancy and manage spaces efficiently.</p>
        </div>
      </div>
    </section>

    <section id="features" class="features">
      <h2>Why Study Spaces?</h2>

      <div class="feature-grid">
        <div class="feature">
          <div class="icon">🪑</div>
          <h3>Seat Reservation</h3>
          <p>Reserve study seats anytime.</p>
        </div>

        <div class="feature">
          <div class="icon">🏢</div>
          <h3>Multiple Libraries</h3>
          <p>Support multiple campuses and study locations.</p>
        </div>

        <div class="feature">
          <div class="icon">📈</div>
          <h3>Real-time Occupancy</h3>
          <p>Know which seats are available before arriving.</p>
        </div>

        <div class="feature">
          <div class="icon">🔐</div>
          <h3>Secure Login</h3>
          <p>Role-based access for students and administrators.</p>
        </div>

        <div class="feature">
          <div class="icon">🔔</div>
          <h3>Notifications</h3>
          <p>Stay informed about bookings and updates.</p>
        </div>

        <div class="feature">
          <div class="icon">⚡</div>
          <h3>Simple & Fast</h3>
          <p>Designed for a smooth reservation experience.</p>
        </div>
      </div>
    </section>

    <section class="steps">
      <h2>How It Works</h2>

      <div class="step-container">
        <div class="step">1. Login</div>
        <div class="arrow">→</div>

        <div class="step">2. Select Library</div>
        <div class="arrow">→</div>

        <div class="step">3. Choose Seat</div>
        <div class="arrow">→</div>

        <div class="step">4. Reserve</div>
      </div>
    </section>

    <footer>
      © 2026 Smart Library App • Library Management System
    </footer>
  </div>
</template>

<style scoped>
*{
  box-sizing:border-box;
}

.landing-page{
  font-family:Inter,Arial,sans-serif;
  background:#f8fafc;
  color:#1e293b;
}

/* ---------------- Navbar ---------------- */

.navbar{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:18px 8%;
  background:rgba(255,255,255,.92);
  backdrop-filter:blur(10px);
  border-bottom:1px solid #e5e7eb;
  position:sticky;
  top:0;
  z-index:100;
}

.logo{
  display:flex;
  align-items:center;
  gap:10px;
  font-size:1.3rem;
  font-weight:700;
}

.logo-icon{
  font-size:28px;
}

/* ---------------- Buttons ---------------- */

.login-btn,
.primary-btn,
.secondary-btn{
  text-decoration:none;
  padding:12px 24px;
  border-radius:12px;
  font-weight:600;
  transition:all .25s ease;
}

.login-btn,
.primary-btn{
  background:#2563eb;
  color:white;
  box-shadow:0 4px 12px rgba(37,99,235,.20);
}

.login-btn:hover,
.primary-btn:hover{
  background:#1d4ed8;
  transform:translateY(-2px);
  box-shadow:0 10px 22px rgba(37,99,235,.25);
}

.secondary-btn{
  border:1px solid #2563eb;
  color:#2563eb;
  background:white;
}

.secondary-btn:hover{
  background:#eff6ff;
  transform:translateY(-2px);
}

/* ---------------- Hero ---------------- */

.hero{
  padding:90px 8%;
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:70px;
  align-items:center;
}

.hero h1{
  font-size:3rem;
  line-height:1.15;
  margin-bottom:20px;
}

.hero p{
  line-height:1.8;
  color:#64748b;
  margin-bottom:32px;
}

.hero-buttons{
  display:flex;
  gap:16px;
}

/* ---------------- Right Cards ---------------- */

.hero-card{
  display:grid;
  gap:22px;
}

.card{
  background:white;
  padding:26px;
  border-radius:18px;
  border:1px solid #e5e7eb;
  box-shadow:
      0 8px 24px rgba(15,23,42,.05),
      0 2px 6px rgba(15,23,42,.03);
  transition:all .25s ease;
}

.card:hover{
  transform:translateY(-5px);
  box-shadow:
      0 18px 40px rgba(15,23,42,.10),
      0 6px 16px rgba(15,23,42,.06);
}

.card h3{
  margin-bottom:10px;
}

.card p{
  margin:0;
  color:#64748b;
}

/* ---------------- Features ---------------- */

.features{
  padding:80px 8%;
  background:white;
}

.features h2,
.steps h2{
  text-align:center;
  margin-bottom:50px;
  font-size:2rem;
}

.feature-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:26px;
}

.feature{
  background:white;
  padding:28px;
  border-radius:18px;
  border:1px solid #e5e7eb;
  text-align:center;
  transition:all .25s ease;
  box-shadow:
      0 6px 18px rgba(15,23,42,.04),
      0 2px 6px rgba(15,23,42,.02);
}

.feature:hover{
  transform:translateY(-6px);
  box-shadow:
      0 18px 36px rgba(15,23,42,.08),
      0 6px 14px rgba(15,23,42,.05);
}

.icon{
  font-size:40px;
  margin-bottom:16px;
}

.feature h3{
  margin-bottom:10px;
}

.feature p{
  color:#64748b;
}

/* ---------------- Steps ---------------- */

.steps{
  padding:80px 8%;
}

.step-container{
  display:flex;
  justify-content:center;
  align-items:center;
  gap:18px;
  flex-wrap:wrap;
}

.step{
  background:white;
  padding:18px 26px;
  border-radius:14px;
  border:1px solid #e5e7eb;
  box-shadow:
      0 6px 18px rgba(15,23,42,.05),
      0 2px 6px rgba(15,23,42,.03);
  transition:all .25s ease;
}

.step:hover{
  transform:translateY(-4px);
}

.arrow{
  font-size:22px;
  color:#64748b;
}

/* ---------------- Footer ---------------- */

footer{
  margin-top:40px;
  padding:34px;
  text-align:center;
  background:#0f172a;
  color:white;
}

/* ---------------- Responsive ---------------- */

@media(max-width:900px){

.hero{
  grid-template-columns:1fr;
  text-align:center;
}

.hero-buttons{
  justify-content:center;
}

.navbar{
  padding:18px 20px;
}

.hero,
.features,
.steps{
  padding:60px 20px;
}

.hero h1{
  font-size:2.3rem;
}

}
</style>