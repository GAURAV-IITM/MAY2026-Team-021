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

.navbar{
display:flex;
justify-content:space-between;
align-items:center;
padding:18px 8%;
background:white;
box-shadow:0 2px 10px rgba(0,0,0,.05);
position:sticky;
top:0;
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

.login-btn,
.primary-btn,
.secondary-btn{
text-decoration:none;
padding:12px 24px;
border-radius:8px;
font-weight:600;
transition:.2s;
}

.login-btn,
.primary-btn{
background:#2563eb;
color:white;
}

.login-btn:hover,
.primary-btn:hover{
background:#1d4ed8;
}

.secondary-btn{
border:2px solid #2563eb;
color:#2563eb;
}

.hero{
padding:80px 8%;
display:grid;
grid-template-columns:1fr 1fr;
gap:60px;
align-items:center;
}

.hero h1{
font-size:3rem;
margin-bottom:20px;
}

.hero p{
line-height:1.8;
color:#475569;
margin-bottom:30px;
}

.hero-buttons{
display:flex;
gap:15px;
}

.hero-card{
display:grid;
gap:20px;
}

.card{
background:white;
padding:24px;
border-radius:12px;
box-shadow:0 6px 20px rgba(0,0,0,.08);
}

.features{
padding:70px 8%;
background:white;
}

.features h2,
.steps h2{
text-align:center;
margin-bottom:45px;
}

.feature-grid{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
gap:25px;
}

.feature{
background:#f8fafc;
padding:25px;
border-radius:12px;
text-align:center;
}

.icon{
font-size:38px;
margin-bottom:15px;
}

.steps{
padding:70px 8%;
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
padding:16px 24px;
border-radius:10px;
box-shadow:0 4px 12px rgba(0,0,0,.08);
}

.arrow{
font-size:22px;
}

footer{
margin-top:50px;
padding:30px;
text-align:center;
background:#0f172a;
color:white;
}

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
font-size:2.2rem;
}

}
</style>