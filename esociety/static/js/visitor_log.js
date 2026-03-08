// ============================================================
//  visitor_logs.js  —  eSociety Admin · Visitor Logs Page
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

  // ── AUTO-SUBMIT ON FILTER CHANGE ──────────────────────────
  // Dropdowns (type, status) submit the form immediately on change
  const filterForm   = document.getElementById("filter-form");
  const autoTriggers = filterForm.querySelectorAll("select[name='type'], select[name='status']");

  autoTriggers.forEach(function (el) {
    el.addEventListener("change", function () {
      filterForm.submit();
    });
  });


  // ── LIVE SEARCH DEBOUNCE ──────────────────────────────────
  // Waits 450 ms after user stops typing before submitting
  const searchInput = filterForm.querySelector("input[name='q']");
  let searchTimer   = null;

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(function () {
        filterForm.submit();
      }, 450);
    });
  }


  // ── ACTIVE FILTER HIGHLIGHT ───────────────────────────────
  // Adds a visible ring to any filter that has a non-default value
  const filterInputs = filterForm.querySelectorAll(".filter-input");

  filterInputs.forEach(function (el) {
    highlightIfActive(el);
    el.addEventListener("change", function () { highlightIfActive(el); });
    el.addEventListener("input",  function () { highlightIfActive(el); });
  });

  function highlightIfActive(el) {
    const isEmpty    = el.value === "" || el.value === "all";
    el.classList.toggle("filter-active", !isEmpty);
  }


  // ── RESULTS COUNT FADE-IN ─────────────────────────────────
  const resultsBar = document.querySelector(".results-bar");
  if (resultsBar) {
    resultsBar.style.opacity = "0";
    resultsBar.style.transition = "opacity 0.3s ease";
    setTimeout(function () { resultsBar.style.opacity = "1"; }, 100);
  }


  // ── ROW CLICK → DETAIL MODAL ─────────────────────────────
  // Each <tr> carries data-* attributes rendered by Django.
  // Clicking a row opens a lightweight modal with full details.
  const tbody = document.querySelector("table tbody");
  if (tbody) {
    tbody.addEventListener("click", function (e) {
      const row = e.target.closest("tr[data-id]");
      if (!row) return;
      openDetailModal(row);
    });
  }


  // ── MODAL BUILD ───────────────────────────────────────────
  function openDetailModal(row) {
    // Remove any existing modal
    const existing = document.getElementById("vl-modal");
    if (existing) existing.remove();

    const d = row.dataset;

    const entryStatusColor = {
      inside:  "#10B981",
      exited:  "#64748B",
      denied:  "#EF4444",
      waiting: "#F59E0B",
    }[d.entryStatus] || "#64748B";

    const approvalColor = {
      approved: "#10B981",
      rejected: "#EF4444",
      pending:  "#F59E0B",
    }[d.approvalStatus] || "#F59E0B";

    const typeColor = {
      guest:       "#1E40AF",
      delivery:    "#5B21B6",
      maintenance: "#92400E",
      staff:       "#334155",
    }[d.visitorType] || "#334155";

    const modal = document.createElement("div");
    modal.id    = "vl-modal";
    modal.innerHTML = `
      <div class="vl-overlay" id="vl-overlay"></div>
      <div class="vl-modal-box" role="dialog" aria-modal="true" aria-label="Visitor Details">

        <div class="vl-modal-header">
          <div class="vl-modal-avatar">${(d.visitorName || "?")[0].toUpperCase()}</div>
          <div>
            <div class="vl-modal-name">${d.visitorName || "—"}</div>
            <div class="vl-modal-sub">${d.mobile || "—"}</div>
          </div>
          <button class="vl-close-btn" id="vl-close" aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="vl-modal-badges">
          <span class="vl-chip" style="background:${typeColor}18;color:${typeColor}">${capitalize(d.visitorType || "—")}</span>
          <span class="vl-chip" style="background:${approvalColor}18;color:${approvalColor}">${capitalize(d.approvalStatus || "—")}</span>
          <span class="vl-chip" style="background:${entryStatusColor}18;color:${entryStatusColor}">${capitalize(d.entryStatus || "—")}</span>
        </div>

        <div class="vl-modal-grid">
          ${modalRow("🏠", "Unit",          d.unit          || "—")}
          ${modalRow("👤", "Resident",      d.resident      || "—")}
          ${modalRow("📅", "Expected Date", d.expectedDate  || "—")}
          ${modalRow("🕐", "Entry Time",    d.entryTime     || "—")}
          ${modalRow("🕔", "Exit Time",     d.exitTime      || "—")}
          ${modalRow("🚗", "Vehicle",       d.vehicle       || "—")}
          ${modalRow("👮", "Guard",         d.guard         || "—")}
        </div>

      </div>`;

    document.body.appendChild(modal);
    // Trigger animation
    requestAnimationFrame(function () {
      modal.querySelector(".vl-modal-box").classList.add("vl-modal-visible");
    });

    // Close handlers
    document.getElementById("vl-close").addEventListener("click", closeModal);
    document.getElementById("vl-overlay").addEventListener("click", closeModal);
    document.addEventListener("keydown", handleEsc);
  }

  function modalRow(icon, label, value) {
    return `
      <div class="vl-modal-row">
        <span class="vl-modal-icon">${icon}</span>
        <span class="vl-modal-label">${label}</span>
        <span class="vl-modal-value">${value}</span>
      </div>`;
  }

  function closeModal() {
    const modal = document.getElementById("vl-modal");
    if (!modal) return;
    const box = modal.querySelector(".vl-modal-box");
    box.classList.remove("vl-modal-visible");
    setTimeout(function () { modal.remove(); }, 220);
    document.removeEventListener("keydown", handleEsc);
  }

  function handleEsc(e) {
    if (e.key === "Escape") closeModal();
  }

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }


  // ── STAT CARD COUNT-UP ANIMATION ──────────────────────────
  document.querySelectorAll(".stat-value").forEach(function (el) {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target) || target === 0) return;

    let current  = 0;
    const step   = Math.ceil(target / 30);
    const ticker = setInterval(function () {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(ticker);
      }
      el.textContent = current;
    }, 30);
  });


  // ── EXPORT BUTTON FEEDBACK ────────────────────────────────
  const exportBtn = document.querySelector(".btn-export");
  if (exportBtn) {
    exportBtn.addEventListener("click", function () {
      const original = exportBtn.innerHTML;
      exportBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 0.7s linear infinite">
          <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
        </svg> Exporting…`;
      exportBtn.style.opacity = "0.75";
      setTimeout(function () {
        exportBtn.innerHTML   = original;
        exportBtn.style.opacity = "1";
      }, 2500);
    });
  }

});  // end DOMContentLoaded


// ── MODAL STYLES (injected once) ─────────────────────────────
(function injectModalStyles() {
  if (document.getElementById("vl-modal-styles")) return;
  const style = document.createElement("style");
  style.id = "vl-modal-styles";
  style.textContent = `
    .vl-overlay {
      position: fixed; inset: 0;
      background: rgba(7, 16, 32, 0.45);
      backdrop-filter: blur(3px);
      z-index: 1000;
      animation: vlFadeIn 0.2s ease;
    }
    .vl-modal-box {
      position: fixed;
      top: 50%; left: 50%;
      transform: translate(-50%, -46%);
      width: 420px; max-width: calc(100vw - 32px);
      background: #fff;
      border-radius: 18px;
      box-shadow: 0 28px 70px rgba(0,0,0,0.22);
      z-index: 1001;
      opacity: 0;
      transition: opacity 0.2s ease, transform 0.2s ease;
    }
    .vl-modal-box.vl-modal-visible {
      opacity: 1;
      transform: translate(-50%, -50%);
    }
    .vl-modal-header {
      display: flex; align-items: center; gap: 14px;
      padding: 22px 22px 16px;
      border-bottom: 1px solid #F1F5F9;
      position: relative;
    }
    .vl-modal-avatar {
      width: 46px; height: 46px; border-radius: 50%;
      background: #0F4C81; color: #fff;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; font-weight: 800; flex-shrink: 0;
    }
    .vl-modal-name  { font-size: 16px; font-weight: 800; color: #1E293B; }
    .vl-modal-sub   { font-size: 12px; color: #94A3B8; margin-top: 2px; font-family: 'DM Mono', monospace; }
    .vl-close-btn {
      position: absolute; top: 18px; right: 18px;
      background: #F1F5F9; border: none; border-radius: 8px;
      width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
      cursor: pointer; color: #64748B; transition: background 0.15s;
    }
    .vl-close-btn:hover { background: #E2E8F0; color: #1E293B; }
    .vl-modal-badges {
      display: flex; gap: 8px; flex-wrap: wrap;
      padding: 14px 22px 0;
    }
    .vl-chip {
      padding: 4px 12px; border-radius: 20px;
      font-size: 11px; font-weight: 700;
    }
    .vl-modal-grid {
      padding: 14px 22px 22px;
      display: flex; flex-direction: column; gap: 2px;
    }
    .vl-modal-row {
      display: flex; align-items: center; gap: 12px;
      padding: 9px 0; border-bottom: 1px solid #F8FAFC;
    }
    .vl-modal-row:last-child { border-bottom: none; }
    .vl-modal-icon  { font-size: 15px; width: 22px; text-align: center; flex-shrink: 0; }
    .vl-modal-label { font-size: 12px; font-weight: 600; color: #64748B; width: 110px; flex-shrink: 0; }
    .vl-modal-value { font-size: 13px; font-weight: 600; color: #1E293B; }
    @keyframes vlFadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes spin { to { transform: rotate(360deg); } }
    .filter-active {
      border-color: #0F4C81 !important;
      box-shadow: 0 0 0 3px rgba(15,76,129,0.1) !important;
    }
    tr[data-id] { cursor: pointer; }
  `;
  document.head.appendChild(style);
})();