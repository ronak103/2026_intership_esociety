/* ══════════════════════════════════════════════════════
   app.js  —  eSociety Resident Dashboard
   All navigation and sidebar interaction logic
══════════════════════════════════════════════════════ */

let isCollapsed = false;

/**
 * Collapse / expand the sidebar
 */
function toggleSidebar() {
  isCollapsed = !isCollapsed;
  document.getElementById('sidebar').classList.toggle('collapsed', isCollapsed);
  document.getElementById('collapse-btn').textContent = isCollapsed ? '▶' : '◀';
}

/**
 * Mark the correct nav-item as active on each page load.
 * Each HTML page sets window.CURRENT_PAGE to its own page id.
 */
function setActiveNav() {
  const current = window.CURRENT_PAGE || '';
  document.querySelectorAll('.nav-item').forEach(function (btn) {
    const active = btn.dataset.page === current;
    btn.classList.toggle('active', active);
  });
}

// Run on DOM ready
document.addEventListener('DOMContentLoaded', function () {
  setActiveNav();
});
