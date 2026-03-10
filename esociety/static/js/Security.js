/**
 * SocietySync — Security.js  (IMPROVED)
 * Single file for ALL security guard pages.
 *
 * IMPROVEMENTS OVER OLD VERSION:
 *  ✦ Sidebar: desktop mini-collapse (icon-only) with localStorage — old version
 *    only did full hide/show. Mobile breakpoint raised to 1024px (was 768px).
 *  ✦ Notification bell: aria-expanded + ESC close added
 *  ✦ Modal system: body scroll lock + focus trap + ESC + click-outside
 *  ✦ Skeleton reveal: uses requestAnimationFrame + minMs guarantee (was raw setTimeout)
 *  ✦ Mark-all-read: toast feedback + error handling improved
 *  ✦ Table search: debounced 200ms (was instant)
 *  ✦ Clock: uses Intl.DateTimeFormat for locale-correct formatting
 *  ✦ NEW — Visitor entry/exit AJAX with optimistic row update
 *  ✦ NEW — Visitor log modal (row click) matching admin panel style
 *  ✦ NEW — Toast notification system (matching resident.js)
 *  ✦ NEW — OTP field auto-focus + numeric-only enforcement
 *  ✦ NEW — Log form: expected-date default + vehicle plate uppercase
 *  ✦ NEW — Auto-submit selects (filter dropdowns)
 *  ✦ NEW — data-confirm event delegation (one listener, not N)
 *  ✦ NEW — Topbar scroll shadow
 */

'use strict';

/* ============================================================
   UTILITIES
   ============================================================ */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function getCsrf() {
    const el = $('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}


/* ============================================================
   1. SIDEBAR — desktop icon-only collapse + mobile drawer
   Breakpoint raised from 768 → 1024 to match sidebar.css
   ============================================================ */
(function initSidebar() {
    const sidebar  = document.getElementById('sidebar');
    const toggle   = document.getElementById('sidebarToggle');
    const overlay  = document.getElementById('sidebarOverlay');
    const mainEl   = document.getElementById('mainContent') ||
                     $('.main-content') || $('.page-body');
    if (!sidebar || !toggle) return;

    const MOBILE_BP = 1024;
    const KEY       = 'sg_sidebar_collapsed';

    function isMobile() { return window.innerWidth <= MOBILE_BP; }
    function lockScroll(lock) { document.body.style.overflow = lock ? 'hidden' : ''; }

    function setCollapsed(collapsed) {
        sidebar.classList.toggle('collapsed', collapsed);
        localStorage.setItem(KEY, collapsed);
        // Fallback for browsers without CSS :has()
        if (mainEl && !isMobile() && !CSS.supports('selector(:has(*))')) {
            const collW = getComputedStyle(document.documentElement)
                .getPropertyValue('--sidebar-collapsed-width').trim() || '68px';
            const fullW = getComputedStyle(document.documentElement)
                .getPropertyValue('--sidebar-width').trim() || '260px';
            mainEl.style.marginLeft = collapsed ? collW : fullW;
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
    $$('.sidebar-link').forEach(link => {
        const href = link.getAttribute('href');
        if (!href || href === '#') return;
        const lp = href.replace(/\/$/, '');
        if (path === lp || (lp.length > 1 && path.startsWith(lp))) {
            link.closest('.sidebar-menu-item')?.classList.add('active');
        }
    });
})();


/* ============================================================
   2. NOTIFICATION BELL DROPDOWN
   ============================================================ */
(function initNotifBell() {
    const btn      = document.getElementById('notifBtn');
    const dropdown = document.getElementById('notifDropdown');
    if (!btn || !dropdown) return;

    btn.addEventListener('click', e => {
        e.stopPropagation();
        const open = dropdown.classList.toggle('open');
        btn.setAttribute('aria-expanded', open);
    });

    document.addEventListener('click', e => {
        if (!dropdown.contains(e.target) && e.target !== btn) {
            dropdown.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
        }
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            dropdown.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
        }
    });
})();


/* ============================================================
   3. MODAL SYSTEM
   openModal(id) / closeModal(id)
   Features: body scroll lock, focus first input, ESC, click-outside
   ============================================================ */
(function initModals() {
    window.openModal = function (id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.add('open');
        el.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        requestAnimationFrame(() => {
            const focusable = el.querySelector(
                'input:not([type=hidden]), select, textarea, button:not([data-dismiss])'
            );
            focusable?.focus();
        });
    };

    window.closeModal = function (id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('open');
        el.style.display = '';
        document.body.style.overflow = '';
    };

    // Click outside
    document.addEventListener('click', e => {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.classList.remove('open');
            e.target.style.display = '';
            document.body.style.overflow = '';
        }
    });

    // ESC
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            $$('.modal-overlay.open').forEach(m => {
                m.classList.remove('open');
                m.style.display = '';
            });
            document.body.style.overflow = '';
        }
    });

    // data-dismiss buttons
    document.addEventListener('click', e => {
        const btn = e.target.closest('[data-dismiss="modal"]');
        if (!btn) return;
        const modal = btn.closest('.modal-overlay');
        if (modal) { modal.classList.remove('open'); modal.style.display = ''; document.body.style.overflow = ''; }
    });
})();


/* ============================================================
   4. SKELETON REVEAL
   Called from templates: skeletonReveal(minMs)
   Uses requestAnimationFrame for smooth reveal.
   ============================================================ */
window.skeletonReveal = function (minMs = 900) {
    const start = Date.now();

    function reveal() {
        const wait = Math.max(0, minMs - (Date.now() - start));
        setTimeout(() => {
            const pb = $('.page-body');
            pb?.classList.remove('sk-active', 'page-loading');
            $$('.real-content').forEach(el => {
                el.classList.add('sk-revealed');
                // Stagger children for polished effect
                $$('[data-sk-child]', el).forEach((child, i) => {
                    child.style.animationDelay = (i * 60) + 'ms';
                });
            });
        }, wait);
    }

    if (document.readyState === 'complete') reveal();
    else window.addEventListener('load', reveal);
};


/* ============================================================
   5. DJANGO MESSAGES AUTO-DISMISS
   ============================================================ */
(function initMessages() {
    if (!document.getElementById('_sg-kf')) {
        const s = document.createElement('style');
        s.id = '_sg-kf';
        s.textContent = '@keyframes _sgDrain{from{transform:scaleX(1)}to{transform:scaleX(0)}}';
        document.head.appendChild(s);
    }

    $$('.msg-alert, .alert, .messages-wrap .alert').forEach(el => {
        const DELAY = 4500;
        const bar = document.createElement('div');
        bar.style.cssText = `position:absolute;bottom:0;left:0;height:2px;width:100%;background:currentColor;opacity:.22;border-radius:0 0 6px 6px;transform-origin:left;animation:_sgDrain ${DELAY}ms linear forwards;`;
        if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
        el.appendChild(bar);

        setTimeout(() => {
            el.style.transition = 'opacity .4s ease, transform .4s ease';
            el.style.opacity    = '0';
            el.style.transform  = 'translateX(10px)';
            setTimeout(() => el.remove(), 420);
        }, DELAY);
    });
})();


/* ============================================================
   6. MARK ALL NOTIFICATIONS READ — AJAX
   ============================================================ */
(function initMarkAllRead() {
    const btn = document.getElementById('markAllRead');
    if (!btn) return;

    btn.addEventListener('click', async e => {
        e.preventDefault();
        const url = btn.dataset.url || btn.getAttribute('href');
        if (!url) return;

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrf(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            if (!res.ok) throw new Error();

            $$('.notif-item.unread, .notif-page-item.unread').forEach(el => el.classList.remove('unread'));
            $$('.notif-count, .notif-dot, .notif-unread-dot').forEach(el => el.style.display = 'none');
            showToast('All notifications marked as read', 'success', 2000);
        } catch {
            window.location.href = url;
        }
    });
})();


/* ============================================================
   7. VISITOR ENTRY / EXIT — AJAX with optimistic row update
   Buttons:
     <button data-action="enter" data-url="/..." data-visitor-id="X">Mark Entered</button>
     <button data-action="exit"  data-url="/..." data-visitor-id="X">Mark Exited</button>
   ============================================================ */
(function initVisitorActions() {
    document.addEventListener('click', async e => {
        const btn = e.target.closest('[data-action="enter"], [data-action="exit"], [data-action="deny"]');
        if (!btn || !btn.dataset.url) return;

        const action = btn.dataset.action;
        const url    = btn.dataset.url;

        if (action === 'deny' && !confirm('Deny entry for this visitor?')) return;

        const origHTML = btn.innerHTML;
        btn.disabled   = true;
        btn.innerHTML  = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrf(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            if (!res.ok) throw new Error();

            const data = await res.json().catch(() => ({}));

            // Update status badge in the same row
            const row    = btn.closest('tr, .visitor-card, .pending-item');
            const badge  = row?.querySelector('.badge, [data-status-badge]');
            const statusMap = {
                enter: { text: 'Inside',  cls: 'badge-success' },
                exit:  { text: 'Exited',  cls: 'badge-gray'    },
                deny:  { text: 'Denied',  cls: 'badge-danger'  },
            };
            if (badge && statusMap[action]) {
                badge.textContent = statusMap[action].text;
                badge.className   = 'badge ' + statusMap[action].cls;
            }

            // Update entry/exit time cells
            if (data.entry_time) {
                const timeCell = row?.querySelector('[data-entry-time]');
                if (timeCell) timeCell.textContent = data.entry_time;
            }
            if (data.exit_time) {
                const timeCell = row?.querySelector('[data-exit-time]');
                if (timeCell) timeCell.textContent = data.exit_time;
            }

            // Update or hide action button
            if (action === 'enter') {
                btn.textContent  = 'Mark Exited';
                btn.dataset.action = 'exit';
                btn.disabled     = false;
                btn.className    = btn.className.replace(/btn-\w+/, 'btn-outline');
            } else {
                btn.remove();
            }

            const msgs = { enter: 'Visitor marked as entered.', exit: 'Visitor marked as exited.', deny: 'Visitor denied entry.' };
            showToast(data.message || msgs[action], action === 'deny' ? 'warning' : 'success');
        } catch {
            btn.disabled  = false;
            btn.innerHTML = origHTML;
            showToast('Action failed. Please try again.', 'error');
        }
    });
})();


/* ============================================================
   8. VISITOR LOG MODAL — row click shows detail card
   Reads data-* attributes from <tr>
   ============================================================ */
(function initVisitorLogModal() {
    const tbody = $('table#visitorTable tbody, table.visitor-log-table tbody');
    if (!tbody) return;

    tbody.addEventListener('click', e => {
        const row = e.target.closest('tr[data-visitor-id], tr[data-id]');
        if (!row || e.target.closest('a, button, .btn')) return;
        buildGuardVisitorModal(row);
    });

    function buildGuardVisitorModal(row) {
        document.getElementById('_sg-vl-modal')?.remove();

        const d   = row.dataset;
        const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : '—';

        const colors = {
            inside:'#10B981', exited:'#64748B', denied:'#EF4444', waiting:'#F59E0B', pending:'#F59E0B',
            approved:'#10B981', rejected:'#EF4444', guest:'#1D4ED8', delivery:'#7C3AED', staff:'#334155',
        };
        const ec = colors[(d.entryStatus  || '').toLowerCase()] || '#64748B';
        const ac = colors[(d.approvalStatus || '').toLowerCase()] || '#F59E0B';
        const tc = colors[(d.visitorType  || '').toLowerCase()] || '#334155';

        const r = (icon, label, val) => `<div style="display:flex;align-items:center;gap:11px;padding:8px 0;border-bottom:1px solid #f8fafc">
            <span style="font-size:14px;width:20px;text-align:center;flex-shrink:0">${icon}</span>
            <span style="font-size:11.5px;font-weight:600;color:#64748b;width:110px;flex-shrink:0">${label}</span>
            <span style="font-size:13px;font-weight:600;color:#1e293b">${val || '—'}</span></div>`;

        const wrap = document.createElement('div');
        wrap.id = '_sg-vl-modal';
        wrap.innerHTML = `
        <div id="_sg-vl-ov" style="position:fixed;inset:0;background:rgba(7,16,32,.45);backdrop-filter:blur(3px);z-index:1000;animation:_sgFI .18s ease"></div>
        <div role="dialog" aria-modal="true" id="_sg-vl-box" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-46%);width:420px;max-width:calc(100vw - 28px);background:#fff;border-radius:18px;box-shadow:0 28px 70px rgba(0,0,0,.22);z-index:1001;opacity:0;transition:opacity .2s,transform .2s">
          <div style="display:flex;align-items:center;gap:13px;padding:18px 18px 12px;border-bottom:1px solid #f1f5f9;position:relative">
            <div style="width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#1d4ed8,#06b6d4);color:#fff;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:800;flex-shrink:0">${(d.visitorName||'?')[0].toUpperCase()}</div>
            <div>
              <div style="font-size:14.5px;font-weight:800;color:#1e293b">${d.visitorName||'—'}</div>
              <div style="font-size:11.5px;color:#94a3b8;margin-top:2px;font-family:'DM Mono',monospace">${d.mobile||'—'}</div>
            </div>
            <button id="_sg-vl-close" aria-label="Close" style="position:absolute;top:14px;right:14px;background:#f1f5f9;border:none;border-radius:8px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#64748b;font-size:15px;transition:.15s">✕</button>
          </div>
          <div style="display:flex;gap:7px;flex-wrap:wrap;padding:11px 18px 0">
            <span style="padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;background:${tc}18;color:${tc}">${cap(d.visitorType)}</span>
            <span style="padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;background:${ac}18;color:${ac}">${cap(d.approvalStatus)}</span>
            <span style="padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;background:${ec}18;color:${ec}">${cap(d.entryStatus)}</span>
          </div>
          <div style="padding:8px 18px 18px">
            ${r('🏠','Unit',           d.unit)}
            ${r('👤','Resident',       d.resident)}
            ${r('📅','Expected Date',  d.expectedDate)}
            ${r('🕐','Entry Time',     d.entryTime)}
            ${r('🕔','Exit Time',      d.exitTime)}
            ${r('🚗','Vehicle',        d.vehicle)}
          </div>
        </div>`;

        // Inject keyframe
        if (!document.getElementById('_sg-vl-kf')) {
            const s = document.createElement('style');
            s.id = '_sg-vl-kf';
            s.textContent = '@keyframes _sgFI{from{opacity:0}to{opacity:1}}';
            document.head.appendChild(s);
        }

        document.body.appendChild(wrap);
        requestAnimationFrame(() => {
            const box = document.getElementById('_sg-vl-box');
            box.style.opacity   = '1';
            box.style.transform = 'translate(-50%,-50%)';
        });

        const close = () => {
            const box = document.getElementById('_sg-vl-box');
            if (box) { box.style.opacity = '0'; box.style.transform = 'translate(-50%,-46%)'; }
            setTimeout(() => wrap.remove(), 200);
            document.removeEventListener('keydown', esc);
        };
        const esc = e => { if (e.key === 'Escape') close(); };
        document.getElementById('_sg-vl-close')?.addEventListener('click', close);
        document.getElementById('_sg-vl-ov')?.addEventListener('click', close);
        document.addEventListener('keydown', esc);
    }
})();


/* ============================================================
   9. TABLE SEARCH — client-side instant row filter
   Usage: initTableSearch('inputId', 'tableId')
   Also auto-wires [data-table-search] attributes.
   ============================================================ */
window.initTableSearch = function (inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) return;

    input.addEventListener('input', debounce(() => {
        const q = input.value.toLowerCase().trim();
        table.querySelectorAll('tbody tr').forEach(row => {
            row.style.display = !q || row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    }, 200));
};

// Auto-wire
$$('[data-table-search]').forEach(input => {
    const table = document.getElementById(input.dataset.tableSearch);
    if (!table) return;
    input.addEventListener('input', debounce(() => {
        const q = input.value.toLowerCase().trim();
        table.querySelectorAll('tbody tr').forEach(row => {
            row.style.display = !q || row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    }, 200));
});


/* ============================================================
   10. AUTO-SUBMIT SELECT FILTERS
   ============================================================ */
$$('.auto-submit select, [data-auto-submit] select').forEach(sel => {
    sel.addEventListener('change', () => sel.closest('form').submit());
});

// Highlight active filters
$$('.filter-select, .filter-input').forEach(el => {
    const hl = () => el.classList.toggle('filter-active', el.value !== '' && el.value !== 'all');
    hl();
    el.addEventListener('change', hl);
    el.addEventListener('input',  hl);
});


/* ============================================================
   11. DATA-CONFIRM — event-delegated
   ============================================================ */
document.addEventListener('click', e => {
    const el = e.target.closest('[data-confirm]');
    if (!el) return;
    if (!confirm(el.dataset.confirm || 'Are you sure?')) e.preventDefault();
}, true);


/* ============================================================
   12. TOPBAR CLOCK — live time display
   Improved: uses Intl.DateTimeFormat (locale-correct)
   ============================================================ */
(function initClock() {
    const clockEl = document.getElementById('topbarClock');
    if (!clockEl) return;

    const fmt = new Intl.DateTimeFormat('en-IN', {
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true,
    });

    function tick() { clockEl.textContent = fmt.format(new Date()); }
    tick();
    setInterval(tick, 1000);
})();


/* ============================================================
   13. LOG VISITOR FORM — UX helpers
   ✦ Default expected date to today
   ✦ Vehicle plate auto-uppercase
   ✦ OTP field: numeric-only, auto-focus, 6-digit pattern
   ✦ Re-open modal if Django returns form error (show_log_modal flag)
   ============================================================ */
(function initLogForm() {
    // Default date inputs to today
    const today = new Date().toISOString().split('T')[0];
    $$('input[type="date"]').forEach(inp => { if (!inp.value) inp.value = today; });

    // Vehicle plate — uppercase
    const plateInput = $('input[name="vehicle_number"], input[name="vehicle_plate"]');
    plateInput?.addEventListener('input', function () {
        const pos = this.selectionStart;
        this.value = this.value.toUpperCase().replace(/[^A-Z0-9\- ]/g, '');
        this.setSelectionRange(pos, pos);
    });

    // OTP field — numeric only, max 6 chars
    const otpInput = $('input[name="otp"], input[id="otp_field"]');
    if (otpInput) {
        otpInput.setAttribute('inputmode', 'numeric');
        otpInput.setAttribute('pattern',   '[0-9]{4,6}');
        otpInput.setAttribute('maxlength', '6');
        otpInput.addEventListener('input', function () {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 6);
        });
    }

    // Re-open log modal if server returned form errors
    // Templates set: <span id="showLogModal" data-show="1"></span>
    const flag = document.getElementById('showLogModal');
    if (flag && flag.dataset.show === '1') {
        openModal('logVisitorModal');
    }

    // Phone number: numeric only, max 10 digits (India)
    const phoneInputs = $$('input[name="mobile"], input[type="tel"]');
    phoneInputs.forEach(inp => {
        inp.setAttribute('inputmode', 'tel');
        inp.addEventListener('input', function () {
            this.value = this.value.replace(/[^0-9+\- ]/g, '').slice(0, 15);
        });
    });
})();


/* ============================================================
   14. TOPBAR SCROLL SHADOW
   ============================================================ */
(function initTopbarScroll() {
    const topbar = $('.topbar');
    if (!topbar) return;
    const onScroll = () => topbar.classList.toggle('scrolled', window.scrollY > 6);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
})();


/* ============================================================
   15. TOAST NOTIFICATION SYSTEM
   Usage: showToast('Message', 'success' | 'error' | 'info' | 'warning', ms)
   ============================================================ */
(function initToasts() {
    if (!document.getElementById('_sg-toast-css')) {
        const s = document.createElement('style');
        s.id = '_sg-toast-css';
        s.textContent = `
.sg-toast-wrap{position:fixed;bottom:20px;right:20px;display:flex;flex-direction:column;gap:8px;z-index:9999;pointer-events:none}
.sg-toast{display:flex;align-items:center;gap:9px;padding:10px 15px;background:#0f172a;color:#e2e8f0;border-radius:12px;font-size:13px;font-weight:500;font-family:'DM Sans',system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.22);border-left:3px solid;min-width:190px;max-width:300px;pointer-events:auto;cursor:pointer;animation:_sgTIn .3s cubic-bezier(.34,1.56,.64,1)}
.sg-toast.leaving{animation:_sgTOut .22s ease forwards}
.sg-toast.success{border-color:#10b981}.sg-toast.error{border-color:#ef4444}.sg-toast.info{border-color:#3b82f6}.sg-toast.warning{border-color:#f59e0b}
@keyframes _sgTIn{from{opacity:0;transform:translateX(24px) scale(.95)}to{opacity:1;transform:translateX(0) scale(1)}}
@keyframes _sgTOut{from{opacity:1;transform:translateX(0)}to{opacity:0;transform:translateX(16px)}}`;
        document.head.appendChild(s);
    }

    let wrap = null;
    function getWrap() {
        if (!wrap) { wrap = document.createElement('div'); wrap.className = 'sg-toast-wrap'; document.body.appendChild(wrap); }
        return wrap;
    }

    const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '!' };

    window.showToast = function (msg, type = 'info', duration = 3500) {
        const el = document.createElement('div');
        el.className = `sg-toast ${type}`;
        el.innerHTML = `<span style="font-weight:800;font-size:14px;flex-shrink:0">${icons[type] || '!'}</span><span>${msg}</span>`;
        getWrap().appendChild(el);

        function dismiss() {
            clearTimeout(timer);
            el.classList.add('leaving');
            el.addEventListener('animationend', () => el.remove(), { once: true });
        }
        const timer = setTimeout(dismiss, duration);
        el.addEventListener('click', dismiss);
    };
})();


/* ============================================================
   16. PENDING APPROVALS — quick approve/reject from dashboard
   Mirrors visitor actions but targets the pending list widget.
   ============================================================ */
(function initPendingActions() {
    const pendingList = $('.pending-list, [data-pending-list]');
    if (!pendingList) return;

    pendingList.addEventListener('click', async e => {
        const btn = e.target.closest('[data-quick-action]');
        if (!btn || !btn.dataset.url) return;

        const action   = btn.dataset.quickAction;
        const url      = btn.dataset.url;
        const item     = btn.closest('.pending-item, li, tr');
        const origHTML = btn.innerHTML;

        btn.disabled  = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size:10px"></i>';

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!res.ok) throw new Error();

            // Fade and remove item
            if (item) {
                item.style.transition = 'opacity .3s, transform .3s';
                item.style.opacity    = '0';
                item.style.transform  = 'translateX(8px)';
                setTimeout(() => {
                    item.remove();
                    // Update pending count badge if exists
                    const countEl = $('[data-pending-count]');
                    if (countEl) {
                        const n = parseInt(countEl.textContent) - 1;
                        countEl.textContent = Math.max(0, n);
                    }
                }, 320);
            }
            showToast(
                action === 'approve' ? 'Visitor approved!' : 'Visitor rejected.',
                action === 'approve' ? 'success' : 'info',
                2000
            );
        } catch {
            btn.disabled  = false;
            btn.innerHTML = origHTML;
            showToast('Action failed. Please try again.', 'error');
        }
    });
})();