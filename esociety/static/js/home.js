// ============================================================
//  GateNova — home.js
//  All homepage scripts: navbar, scroll reveal, progress bars,
//  hamburger menu
// ============================================================

// ── Navbar scroll shadow ──────────────────────────────────
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 20);
});

// ── Scroll reveal ─────────────────────────────────────────
const reveals = document.querySelectorAll('.reveal');
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      revealObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.1 });
reveals.forEach(el => revealObserver.observe(el));

// ── Progress bar animation on scroll ─────────────────────
const progFills = document.querySelectorAll('.prog__fill');
const progObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.style.width = e.target.style.width; // trigger reflow
      progObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.3 });
progFills.forEach(el => {
  const w = el.style.width;
  el.style.width = '0';
  setTimeout(() => el.style.width = w, 300);
  progObserver.observe(el);
});

// ── Hamburger (mobile) toggle ─────────────────────────────
const hamburger = document.getElementById('hamburger');
hamburger.addEventListener('click', () => hamburger.classList.toggle('active'));
