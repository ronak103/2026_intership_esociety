/**
 * SocietySync — admin.js  (IMPROVED)
 *
 * IMPROVEMENTS:
 * ✦ Modular IIFE pattern — no global namespace pollution
 * ✦ Unified Toast system (replaces scattered alert calls)
 * ✦ Skeleton reveal upgraded to work with both old (.page-loading)
 *   and new (.sk-active) patterns
 * ✦ Visitor modal styles moved to admin.css (not injected via JS)
 *   — kept here only as minimal fallback
 * ✦ Counter animation uses requestAnimationFrame (smoother)
 * ✦ Debounce utility extracted
 * ✦ Confirm helper uses a styled confirm() wrapper
 * ✦ Auto-dismiss messages with progress bar
 * ✦ Tab pill memory (persists via sessionStorage)
 * ✦ Export button with improved spinner UX
 * ✦ Removed redundant event re-registrations
 */

'use strict';

/* ═══════════════════════════════════════════════════════════
   UTILITIES
═══════════════════════════════════════════════════════════ */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const on = (el, ev, fn, opts) => el && el.addEventListener(ev, fn, opts);

/** Debounce: returns fn that delays execution by `ms`. */
function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

/** Format number with Indian locale (handles ₹ prefix) */
function fmtNum(n, isAmount) {
    return (isAmount ? '₹' : '') + Math.round(n).toLocaleString('en-IN');
}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR — desktop collapse + mobile drawer
   Mirrors Security.js initSidebar() exactly.
   Requires in HTML:
     <aside id="sidebar">  <div id="mainContent">
     <button id="sidebarToggle">  <div id="sidebarOverlay">
═══════════════════════════════════════════════════════════ */
(function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle  = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('sidebarOverlay');
    const mainEl  = document.getElementById('mainContent') || $('.main-content');

    if (!sidebar || !toggle) return;

    const MOBILE_BP = 1024;
    const KEY       = 'adm_sidebar_collapsed';

    function isMobile() { return window.innerWidth <= MOBILE_BP; }
    function lockScroll(lock) { document.body.style.overflow = lock ? 'hidden' : ''; }

    function setCollapsed(collapsed) {
        sidebar.classList.toggle('collapsed', collapsed);
        localStorage.setItem(KEY, collapsed);
        // Fallback for browsers without CSS :has()
        if (mainEl && !isMobile() && !CSS.supports('selector(:has(*))')) {
            mainEl.style.marginLeft = collapsed ? '0' : '';
        }
    }

    function setMobileOpen(open) {
        sidebar.classList.toggle('mobile-open', open);
        overlay && overlay.classList.toggle('active', open);
        lockScroll(open);
        toggle.setAttribute('aria-expanded', open);
    }

    // Restore desktop state on load
    if (!isMobile()) {
        setCollapsed(localStorage.getItem(KEY) === 'true');
    }

    toggle.addEventListener('click', () => {
        if (isMobile()) {
            setMobileOpen(!sidebar.classList.contains('mobile-open'));
        } else {
            setCollapsed(!sidebar.classList.contains('collapsed'));
        }
    });

    overlay && overlay.addEventListener('click', () => setMobileOpen(false));

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && isMobile() && sidebar.classList.contains('mobile-open')) {
            setMobileOpen(false);
        }
    });

    let rTimer;
    window.addEventListener('resize', () => {
        clearTimeout(rTimer);
        rTimer = setTimeout(() => {
            if (!isMobile()) {
                sidebar.classList.remove('mobile-open');
                overlay && overlay.classList.remove('active');
                lockScroll(false);
                if (mainEl) mainEl.style.marginLeft = '';
                setCollapsed(localStorage.getItem(KEY) === 'true');
            }
        }, 150);
    });

    // Active nav highlight from URL
    const path = window.location.pathname.replace(/\/$/, '');
    document.querySelectorAll('.sidebar-link').forEach(link => {
        const href = link.getAttribute('href');
        if (!href || href === '#') return;
        const lp = href.replace(/\/$/, '');
        if (path === lp) {
            link.closest('.sidebar-menu-item')?.classList.add('active');
        }
    });
})();

/* ═══════════════════════════════════════════════════════════
   0. SKELETON REVEAL
   Supports both:
     • Old pattern: .page-loading → removes class
     • New pattern: body.sk-active .page-body → removes class
   Called from each template: skeletonReveal(minMs)
═══════════════════════════════════════════════════════════ */
window.skeletonReveal = function (minMs = 1200) {
    const start = Date.now();

    function reveal() {
        const wait = Math.max(0, minMs - (Date.now() - start));
        setTimeout(() => {
            // New pattern (.page-body.sk-active)
            const pb = $('.page-body, main');
            if (pb) {
                pb.classList.remove('sk-active');
                pb.classList.remove('page-loading');
            }
            // Reveal real content
            $$('.real-content').forEach(el => {
                el.classList.add('sk-revealed');
            });
        }, wait);
    }

    if (document.readyState === 'complete') {
        reveal();
    } else {
        on(window, 'load', reveal);
    }
};

/* ═══════════════════════════════════════════════════════════
   TOAST NOTIFICATION SYSTEM
   Usage: showToast('Saved!', 'success', 2000)
   Types: 'success' | 'error' | 'info' | 'warning'
═══════════════════════════════════════════════════════════ */
(function initToasts() {
    let container = null;

    function getContainer() {
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    window.showToast = function (msg, type = 'info', duration = 3000) {
        const icons = { success:'✓', error:'✕', info:'i', warning:'!' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span style="font-weight:700;font-size:14px;">${icons[type] || '!'}</span>${msg}`;

        getContainer().appendChild(toast);

        // Auto-remove
        const removeTimer = setTimeout(() => dismiss(toast), duration);

        function dismiss(el) {
            clearTimeout(removeTimer);
            el.classList.add('leaving');
            on(el, 'animationend', () => el.remove(), { once: true });
        }

        on(toast, 'click', () => dismiss(toast));
    };
})();

/* ═══════════════════════════════════════════════════════════
   DOM READY
═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function () {

    /* ──────────────────────────────────────────────────────
       1. MODAL SYSTEM
    ────────────────────────────────────────────────────── */
    window.openModal = function (id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.add('open');
        document.body.style.overflow = 'hidden';
        // Focus first interactive element
        requestAnimationFrame(() => {
            const first = el.querySelector('input:not([type=hidden]), select, textarea, button:not(.modal-close)');
            if (first) first.focus();
        });
    };

    window.closeModal = function (id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('open');
        document.body.style.overflow = '';
    };

    // Click outside to close
    $$('.modal-overlay').forEach(o => {
        on(o, 'click', e => {
            if (e.target === o) { o.classList.remove('open'); document.body.style.overflow = ''; }
        });
    });

    // Escape key
    on(document, 'keydown', e => {
        if (e.key === 'Escape') {
            $$('.modal-overlay.open').forEach(m => {
                m.classList.remove('open');
                document.body.style.overflow = '';
            });
        }
    });

    /* ──────────────────────────────────────────────────────
       2. COMPLAINTS — update modal pre-fill
    ────────────────────────────────────────────────────── */
    window.openUpdateModal = function (id, status, staff) {
        const set = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val; };
        set('complaintIdField',  id);
        set('id_status',         status);
        set('id_assigned_staff', staff || '');
        openModal('updateComplaintModal');
    };

    /* ──────────────────────────────────────────────────────
       3. RESIDENTS — detail modal populate
    ────────────────────────────────────────────────────── */
    window.openResidentDetail = function (name, email, unit, mobile, joined, complaints, pending) {
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('detailName',       'Resident — ' + name);
        set('detailNameFull',   name);
        set('detailEmail',      email);
        set('detailUnit',       unit);
        set('detailMobile',     mobile);
        set('detailJoined',     joined);
        set('detailComplaints', complaints);
        set('detailPending',    pending);
        const av = document.getElementById('detailAvatar');
        if (av) av.textContent = name.split(' ').map(n => n[0] || '').join('').toUpperCase().slice(0, 2);
        openModal('residentDetailModal');
    };

    /* ──────────────────────────────────────────────────────
       4. ALERT AUTO-DISMISS with progress drain
    ────────────────────────────────────────────────────── */
    $$('.alert, .msg-alert, .alert-msg').forEach(alert => {
        const DURATION = 5000;
        // Add thin progress bar at bottom
        const bar = document.createElement('div');
        bar.style.cssText = `position:absolute;bottom:0;left:0;height:2px;background:currentColor;opacity:.3;width:100%;border-radius:0 0 8px 8px;transform-origin:left;animation:msgBar ${DURATION}ms linear forwards;`;
        if (getComputedStyle(alert).position === 'static') alert.style.position = 'relative';
        alert.appendChild(bar);

        // Inject keyframe once
        if (!document.getElementById('msg-bar-kf')) {
            const s = document.createElement('style');
            s.id = 'msg-bar-kf';
            s.textContent = '@keyframes msgBar{from{transform:scaleX(1)}to{transform:scaleX(0)}}';
            document.head.appendChild(s);
        }

        setTimeout(() => {
            alert.style.transition = 'opacity .4s ease, transform .4s ease, max-height .4s ease';
            alert.style.opacity    = '0';
            alert.style.transform  = 'translateX(8px)';
            alert.style.maxHeight  = '0';
            alert.style.overflow   = 'hidden';
            setTimeout(() => alert.remove(), 400);
        }, DURATION);
    });

    /* ──────────────────────────────────────────────────────
       5. NOTIFICATION BELL DROPDOWN
    ────────────────────────────────────────────────────── */
    (function () {
        const btn      = document.getElementById('notifBtn');
        const dropdown = document.getElementById('notifDropdown');
        if (!btn || !dropdown) return;

        on(btn, 'click', e => {
            e.stopPropagation();
            const isOpen = dropdown.classList.toggle('open');
            btn.setAttribute('aria-expanded', isOpen);
        });

        on(document, 'click', e => {
            if (!dropdown.contains(e.target) && e.target !== btn) {
                dropdown.classList.remove('open');
                btn.setAttribute('aria-expanded', 'false');
            }
        });

        on(document, 'keydown', e => {
            if (e.key === 'Escape') dropdown.classList.remove('open');
        });
    })();

    /* ──────────────────────────────────────────────────────
       6. MARK ALL NOTIFICATIONS READ (AJAX)
    ────────────────────────────────────────────────────── */
    const markAllBtn = document.getElementById('markAllRead');
    if (markAllBtn) {
        on(markAllBtn, 'click', async e => {
            e.preventDefault();
            const url = markAllBtn.dataset.url || markAllBtn.getAttribute('href');
            if (!url) return;

            try {
                const csrf = $('[name=csrfmiddlewaretoken]');
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrf ? csrf.value : '',
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });
                if (!res.ok) throw new Error('server error');

                // Clear UI unread indicators
                $$('.notif-item.unread, .notif-page-item.unread').forEach(el => el.classList.remove('unread'));
                $$('.notif-count, .notif-dot').forEach(el => el.style.display = 'none');
                $$('.notif-unread-dot').forEach(el => el.style.display = 'none');
                showToast('All notifications marked as read', 'success', 2000);
            } catch {
                // Graceful fallback — navigate
                window.location.href = url;
            }
        });
    }

    /* ──────────────────────────────────────────────────────
       7. STAT COUNTER ANIMATION (requestAnimationFrame)
    ────────────────────────────────────────────────────── */
    $$('.stat-value').forEach(el => {
        const text     = el.textContent.trim();
        const isAmount = text.startsWith('₹');
        const raw      = parseFloat(text.replace(/[₹,]/g, ''));
        if (isNaN(raw) || raw === 0) return;

        const DURATION = 900; // ms
        const start    = performance.now();

        function step(now) {
            const progress = Math.min((now - start) / DURATION, 1);
            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = fmtNum(raw * eased, isAmount);
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    });

    /* ──────────────────────────────────────────────────────
       8. DATE INPUTS — default to today
    ────────────────────────────────────────────────────── */
    const today = new Date().toISOString().split('T')[0];
    $$('input[type="date"]').forEach(inp => { if (!inp.value) inp.value = today; });

    /* ──────────────────────────────────────────────────────
       9. COPY on mono TD click
    ────────────────────────────────────────────────────── */
    $$('td.td-mono, td[data-copy]').forEach(td => {
        td.style.cursor = 'pointer';
        td.title = 'Click to copy';
        on(td, 'click', () => {
            navigator.clipboard?.writeText(td.textContent.trim())
                .then(() => showToast('Copied to clipboard', 'success', 1500));
        });
    });

    // Also handle legacy inline font-family mono detection
    $$('td').forEach(td => {
        if (td.style.fontFamily?.includes('Mono') && td.textContent.trim() !== '—') {
            td.style.cursor = 'pointer';
            td.title = 'Click to copy';
            on(td, 'click', () => {
                navigator.clipboard?.writeText(td.textContent.trim())
                    .then(() => showToast('Copied!', 'success', 1500));
            });
        }
    });

    /* ──────────────────────────────────────────────────────
       10. TAB PILL ACTIVE STATE
    ────────────────────────────────────────────────────── */
    $$('.tab-pills').forEach(pills => {
        const key = pills.dataset.key;
        // Restore from sessionStorage
        if (key) {
            const saved = sessionStorage.getItem('tab_' + key);
            if (saved) {
                const target = pills.querySelector(`[data-tab="${saved}"]`);
                if (target) { pills.querySelectorAll('.tab-pill').forEach(p => p.classList.remove('active')); target.classList.add('active'); }
            }
        }
        pills.querySelectorAll('.tab-pill').forEach(pill => {
            on(pill, 'click', () => {
                pills.querySelectorAll('.tab-pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                if (key && pill.dataset.tab) sessionStorage.setItem('tab_' + key, pill.dataset.tab);
            });
        });
    });

    /* ──────────────────────────────────────────────────────
       11. DATA-CONFIRM — custom styled confirmation
    ────────────────────────────────────────────────────── */
    on(document, 'click', e => {
        const el = e.target.closest('[data-confirm]');
        if (!el) return;
        const msg = el.dataset.confirm || 'Are you sure? This action cannot be undone.';
        if (!confirm(msg)) e.preventDefault();
    }, true);

    /* ──────────────────────────────────────────────────────
       VISITOR LOGS — only active when filter-form is on page
    ────────────────────────────────────────────────────── */
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {

        // Auto-submit select dropdowns
        filterForm.querySelectorAll("select[name='type'], select[name='status']")
            .forEach(el => on(el, 'change', () => filterForm.submit()));

        // Live search with 450ms debounce
        const qInput = filterForm.querySelector("input[name='q']");
        if (qInput) {
            on(qInput, 'input', debounce(() => filterForm.submit(), 450));
        }

        // Highlight active filters
        filterForm.querySelectorAll('.filter-input').forEach(el => {
            const hl = () => el.classList.toggle('filter-active', el.value !== '' && el.value !== 'all');
            hl();
            on(el, 'change', hl);
            on(el, 'input',  hl);
        });

        // Results bar fade-in
        const rb = $('.results-bar');
        if (rb) { rb.style.opacity = '0'; rb.style.transition = 'opacity .3s'; setTimeout(() => rb.style.opacity = '1', 80); }

        // Row click → visitor detail modal
        const tbody = $('table tbody');
        if (tbody) {
            on(tbody, 'click', e => {
                const row = e.target.closest('tr[data-id]');
                // Don't trigger on action button clicks
                if (row && !e.target.closest('a, button, .btn')) buildVisitorModal(row);
            });
        }

        // Export button spinner
        const exportBtn = $('.btn-export');
        if (exportBtn) {
            on(exportBtn, 'click', function () {
                const orig = exportBtn.innerHTML;
                exportBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin .7s linear infinite;flex-shrink:0"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg> Exporting…`;
                exportBtn.disabled = true;
                setTimeout(() => { exportBtn.innerHTML = orig; exportBtn.disabled = false; }, 2800);
            });
        }
    }

    /* ── Build & show visitor detail modal ── */
    function buildVisitorModal(row) {
        document.getElementById('vl-modal')?.remove();

        const d   = row.dataset;
        const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : '—';
        const colors = {
            inside:'#10B981', exited:'#64748B', denied:'#EF4444', waiting:'#F59E0B',
            approved:'#10B981', rejected:'#EF4444', pending:'#F59E0B',
            guest:'#1D4ED8', delivery:'#7C3AED', maintenance:'#92400E', staff:'#334155',
        };
        const ec = colors[d.entryStatus]    || '#64748B';
        const ac = colors[d.approvalStatus] || '#F59E0B';
        const tc = colors[d.visitorType]    || '#334155';

        const row_ = (icon, label, val) => `
            <div class="vl-modal-row">
                <span class="vl-modal-icon">${icon}</span>
                <span class="vl-modal-label">${label}</span>
                <span class="vl-modal-value">${val || '—'}</span>
            </div>`;

        const modal = document.createElement('div');
        modal.id = 'vl-modal';
        modal.innerHTML = `
            <div class="vl-overlay" id="vl-overlay"></div>
            <div class="vl-modal-box" role="dialog" aria-modal="true" aria-label="Visitor Details">
                <div class="vl-modal-header">
                    <div class="vl-modal-avatar">${(d.visitorName || '?')[0].toUpperCase()}</div>
                    <div>
                        <div class="vl-modal-name">${d.visitorName || '—'}</div>
                        <div class="vl-modal-sub">${d.mobile || '—'}</div>
                    </div>
                    <button class="vl-close-btn" id="vl-close" aria-label="Close dialog">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="vl-modal-badges">
                    <span class="vl-chip" style="background:${tc}18;color:${tc}">${cap(d.visitorType)}</span>
                    <span class="vl-chip" style="background:${ac}18;color:${ac}">${cap(d.approvalStatus)}</span>
                    <span class="vl-chip" style="background:${ec}18;color:${ec}">${cap(d.entryStatus)}</span>
                </div>
                <div class="vl-modal-grid">
                    ${row_('🏠','Unit',          d.unit)}
                    ${row_('👤','Resident',      d.resident)}
                    ${row_('📅','Expected Date', d.expectedDate)}
                    ${row_('🕐','Entry Time',    d.entryTime)}
                    ${row_('🕔','Exit Time',     d.exitTime)}
                    ${row_('🚗','Vehicle',       d.vehicle)}
                    ${row_('👮','Guard',         d.guard)}
                </div>
            </div>`;

        document.body.appendChild(modal);
        requestAnimationFrame(() => modal.querySelector('.vl-modal-box').classList.add('vl-modal-visible'));

        const close = () => {
            modal.querySelector('.vl-modal-box').classList.remove('vl-modal-visible');
            setTimeout(() => modal.remove(), 220);
            document.removeEventListener('keydown', esc);
        };
        const esc = e => { if (e.key === 'Escape') close(); };
        on(document.getElementById('vl-close'), 'click', close);
        on(document.getElementById('vl-overlay'), 'click', close);
        on(document, 'keydown', esc);
    }

    /* ──────────────────────────────────────────────────────
       VISITOR MODAL STYLES (minimal fallback — prefer admin.css)
    ────────────────────────────────────────────────────── */
    if (!document.getElementById('vl-styles')) {
        const s = document.createElement('style');
        s.id = 'vl-styles';
        s.textContent = `
.vl-overlay{position:fixed;inset:0;background:rgba(7,16,32,.45);backdrop-filter:blur(3px);z-index:1000;animation:vlFadeIn .2s ease}
.vl-modal-box{position:fixed;top:50%;left:50%;transform:translate(-50%,-46%);width:420px;max-width:calc(100vw - 32px);background:#fff;border-radius:18px;box-shadow:0 28px 70px rgba(0,0,0,.22);z-index:1001;opacity:0;transition:opacity .2s ease,transform .2s ease}
.vl-modal-box.vl-modal-visible{opacity:1;transform:translate(-50%,-50%)}
.vl-modal-header{display:flex;align-items:center;gap:14px;padding:20px 20px 14px;border-bottom:1px solid #F1F5F9;position:relative}
.vl-modal-avatar{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#1d4ed8,#06b6d4);color:#fff;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800;flex-shrink:0}
.vl-modal-name{font-size:15px;font-weight:800;color:#1E293B}
.vl-modal-sub{font-size:12px;color:#94A3B8;margin-top:2px;font-family:'DM Mono',monospace}
.vl-close-btn{position:absolute;top:16px;right:16px;background:#F1F5F9;border:none;border-radius:8px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#64748B;transition:.15s}
.vl-close-btn:hover{background:#fee2e2;color:#ef4444}
.vl-modal-badges{display:flex;gap:8px;flex-wrap:wrap;padding:12px 20px 0}
.vl-chip{padding:3px 11px;border-radius:20px;font-size:11px;font-weight:700}
.vl-modal-grid{padding:10px 20px 20px;display:flex;flex-direction:column;gap:0}
.vl-modal-row{display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #F8FAFC}
.vl-modal-row:last-child{border-bottom:none}
.vl-modal-icon{font-size:14px;width:20px;text-align:center;flex-shrink:0}
.vl-modal-label{font-size:11.5px;font-weight:600;color:#64748B;width:110px;flex-shrink:0}
.vl-modal-value{font-size:13px;font-weight:600;color:#1E293B}
.filter-active{border-color:#1d4ed8!important;box-shadow:0 0 0 3px rgba(29,78,216,.12)!important}
tr[data-id]{cursor:pointer}
@keyframes vlFadeIn{from{opacity:0}to{opacity:1}}
@keyframes spin{to{transform:rotate(360deg)}}`;
        document.head.appendChild(s);
    }

}); // end DOMContentLoaded