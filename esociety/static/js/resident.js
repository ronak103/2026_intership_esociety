/**
 * SocietySync — resident.js  (IMPROVED)
 * Single file for ALL resident pages.
 *
 * REPLACES: app.js (the old 30-line stub)
 *
 * MODULES:
 *  1. Sidebar — mobile drawer + desktop collapse + localStorage
 *  2. Notification bell dropdown + AJAX mark-all-read
 *  3. Modal system — open / close / ESC / click-outside / focus trap
 *  4. Django message auto-dismiss with progress drain
 *  5. Alert close buttons
 *  6. Poll voting — animated progress bars
 *  7. Facility booking — date/time slot availability
 *  8. Visitor pass — approve / reject AJAX with optimistic UI
 *  9. Filter + search — debounced live filter for tables
 * 10. Complaint form — character counter on textarea
 * 11. Payment copy — click to copy transaction IDs
 * 12. Skeleton reveal — compatible with resident pages
 * 13. Topbar scroll shadow
 * 14. Auto-submit select filters
 * 15. Active nav link highlight from URL
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

async function postJson(url, data = {}) {
    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrf(),
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(data),
    });
    return res.json();
}

/* ============================================================
   1. SIDEBAR
   Supports .app-shell layout (resident) and .admin-layout.
   Desktop: full collapse (icon-only at 68px) persisted to localStorage.
   Mobile: drawer overlay.
   ============================================================ */
(function initSidebar() {
    const sidebar   = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle') ||
                      document.querySelector('.sidebar-toggle');
    const overlay   = document.getElementById('sidebarOverlay');
    const mainWrap  = document.getElementById('mainContent') || $('.main-content');

    if (!sidebar || !toggleBtn) return;

    const MOBILE_BP = 1024;
    const STORE_KEY = 'res_sidebar_collapsed';

    function isMobile() { return window.innerWidth <= MOBILE_BP; }

    function lockScroll(lock) {
        document.body.style.overflow = lock ? 'hidden' : '';
    }

    function setCollapsed(collapsed) {
        sidebar.classList.toggle('collapsed', collapsed);
        localStorage.setItem(STORE_KEY, collapsed);

        if (mainWrap && !isMobile()) {
            // Fallback margin for browsers without CSS :has()
            if (!CSS.supports('selector(:has(*))')) {
                mainWrap.style.marginLeft = collapsed ? '0' : '';
            }
        }
    }

    function setMobileOpen(open) {
        sidebar.classList.toggle('mobile-open', open);
        overlay && overlay.classList.toggle('active', open);
        lockScroll(open);
    }

    // Restore desktop state
    if (!isMobile()) {
        const saved = localStorage.getItem(STORE_KEY) === 'true';
        setCollapsed(saved);
    }

    toggleBtn.addEventListener('click', () => {
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

    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (!isMobile()) {
                sidebar.classList.remove('mobile-open');
                overlay && overlay.classList.remove('active');
                lockScroll(false);
                if (mainWrap) mainWrap.style.marginLeft = '';
                setCollapsed(localStorage.getItem(STORE_KEY) === 'true');
            }
        }, 150);
    });

    // Auto-highlight active nav link from current URL
    const currentPath = window.location.pathname.replace(/\/$/, '');
    $$('.sidebar-link, .nav-item[data-href]').forEach(link => {
        const href = link.getAttribute('href') || link.dataset.href;
        if (!href || href === '#') return;
        const lp = href.replace(/\/$/, '');
        if (currentPath === lp || (lp.length > 1 && currentPath.startsWith(lp))) {
            link.closest('.sidebar-menu-item, .nav-item')?.classList.add('active');
        }
    });
})();


/* ============================================================
   2. NOTIFICATION BELL DROPDOWN + AJAX MARK-ALL-READ
   ============================================================ */
(function initNotifBell() {
    const btn      = document.getElementById('notifBtn');
    const dropdown = document.getElementById('notifDropdown');
    if (!btn || !dropdown) return;

    // FIX: Old Resident_base.html had inline style="display:none" on the dropdown.
    // Inline styles always beat CSS class rules, so toggling .open never worked.
    // Solution: remove the inline style on init so the CSS class .open takes over.
    dropdown.style.removeProperty('display');

    btn.addEventListener('click', e => {
        e.stopPropagation();
        const isOpen = dropdown.classList.toggle('open');
        btn.setAttribute('aria-expanded', isOpen);
        // Fallback for older base templates that still use inline display
        dropdown.style.display = isOpen ? 'block' : 'none';
    });

    document.addEventListener('click', e => {
        if (!dropdown.contains(e.target) && e.target !== btn) {
            dropdown.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
            dropdown.style.display = 'none';
        }
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            dropdown.classList.remove('open');
            btn.setAttribute('aria-expanded', 'false');
            dropdown.style.display = 'none';
        }
    });

    // Mark all read
    const markAllBtn = document.getElementById('markAllRead');
    if (!markAllBtn) return;

    markAllBtn.addEventListener('click', async e => {
        e.preventDefault();
        const url = markAllBtn.dataset.url || markAllBtn.getAttribute('href');
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
            showToast('All notifications marked as read', 'success');
        } catch {
            window.location.href = url;
        }
    });
})();


/* ============================================================
   3. MODAL SYSTEM
   Usage:  openModal('modalId')  /  closeModal('modalId')
   Features: ESC key, click-outside, body scroll lock, focus trap
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

    // Click outside to close
    document.addEventListener('click', e => {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.classList.remove('open');
            e.target.style.display = '';
            document.body.style.overflow = '';
        }
    });

    // ESC to close
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            $$('.modal-overlay.open').forEach(m => {
                m.classList.remove('open');
                m.style.display = '';
                document.body.style.overflow = '';
            });
        }
    });

    // [data-dismiss="modal"] buttons
    document.addEventListener('click', e => {
        const btn = e.target.closest('[data-dismiss="modal"]');
        if (btn) {
            const modal = btn.closest('.modal-overlay');
            if (modal) { modal.classList.remove('open'); modal.style.display = ''; document.body.style.overflow = ''; }
        }
    });
})();


/* ============================================================
   4. DJANGO MESSAGES AUTO-DISMISS
   Adds a draining progress bar and fades out after 5s.
   ============================================================ */
(function initMessages() {
    // Inject keyframe once
    if (!document.getElementById('_res-kf')) {
        const s = document.createElement('style');
        s.id = '_res-kf';
        s.textContent = '@keyframes _drain{from{transform:scaleX(1)}to{transform:scaleX(0)}}';
        document.head.appendChild(s);
    }

    $$('.alert, .msg-alert, .messages-wrap .alert').forEach(el => {
        const DELAY = 5000;

        // Progress drain bar
        const bar = document.createElement('div');
        bar.style.cssText = `position:absolute;bottom:0;left:0;height:2px;width:100%;background:currentColor;opacity:.25;border-radius:0 0 6px 6px;transform-origin:left;animation:_drain ${DELAY}ms linear forwards;`;
        if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
        el.appendChild(bar);

        setTimeout(() => {
            el.style.transition = 'opacity .4s ease, transform .4s ease, max-height .35s ease, padding .35s ease, margin .35s ease';
            el.style.opacity    = '0';
            el.style.transform  = 'translateX(8px)';
            setTimeout(() => el.remove(), 420);
        }, DELAY);
    });
})();


/* ============================================================
   5. ALERT CLOSE BUTTONS
   ============================================================ */
document.addEventListener('click', e => {
    const btn = e.target.closest('.alert-close, [data-close-alert]');
    if (!btn) return;
    const alert = btn.closest('.alert, .msg-alert');
    if (!alert) return;
    alert.style.transition = 'opacity .3s, transform .3s';
    alert.style.opacity    = '0';
    alert.style.transform  = 'translateX(8px)';
    setTimeout(() => alert.remove(), 320);
});


/* ============================================================
   6. POLL VOTING — animated progress bars
   Expects:
     <form data-poll-form data-poll-id="X" action="/.../">
       <button name="choice" value="yes">Yes</button>
       <button name="choice" value="no">No</button>
     </form>
     <div class="poll-result" data-poll-result="X">
       <div class="poll-bar yes" style="width:0%"></div>
       <span class="poll-pct yes">0%</span>
       <div class="poll-bar no"  style="width:0%"></div>
       <span class="poll-pct no">0%</span>
     </div>
   ============================================================ */
(function initPolls() {
    $$('[data-poll-form]').forEach(form => {
        form.addEventListener('submit', async e => {
            e.preventDefault();

            // FIX: FormData does NOT include the clicked submit button's value when
            // e.preventDefault() is called — fd.get('choice') is always null.
            // e.submitter is the specific button that was clicked, so we read its value directly.
            const submitter = e.submitter;
            const choice    = submitter ? submitter.value : null;
            if (!choice) {
                showToast('Please click Yes or No to vote.', 'error');
                return;
            }

            // Optimistic — disable buttons
            form.querySelectorAll('button').forEach(b => {
                b.disabled = true;
                if (b.value === choice) b.classList.add('voted');
            });

            // Build FormData and set choice explicitly so Django receives it
            const fd = new FormData(form);
            fd.set('choice', choice);

            // Use formaction attribute on No button if present, otherwise form.action
            const actionUrl = submitter.getAttribute('formaction') || form.action;

            try {
                const res = await fetch(actionUrl, {
                    method: 'POST',
                    body: fd,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                });

                if (!res.ok) throw new Error('Server error ' + res.status);

                const data = await res.json(); // {yes_pct, no_pct, yes_count, no_count, total}

                // Animate bars
                const pollId = form.dataset.pollId;
                const result = $(`[data-poll-result="${pollId}"]`);
                if (result && data.yes_pct !== undefined) {
                    const yesPct = data.yes_pct ?? 0;
                    const noPct  = data.no_pct  ?? 0;
                    const total  = data.total   ?? ((data.yes_count ?? 0) + (data.no_count ?? 0));
                    const yBar   = result.querySelector('.poll-bar.yes');
                    const nBar   = result.querySelector('.poll-bar.no');
                    const yPct   = result.querySelector('.poll-pct.yes');
                    const nPct   = result.querySelector('.poll-pct.no');
                    const tot    = result.querySelector('.poll-total-votes');
                    if (yBar) yBar.style.width = yesPct + '%';
                    if (nBar) nBar.style.width = noPct  + '%';
                    if (yPct) yPct.textContent = yesPct + '%';
                    if (nPct) nPct.textContent = noPct  + '%';
                    if (tot)  tot.textContent  = total + ' vote' + (total !== 1 ? 's' : '');
                    result.style.display = 'block';
                }

                // Hide the vote buttons after successful vote
                form.style.display = 'none';

                showToast('Vote submitted!', 'success', 2000);
            } catch {
                form.querySelectorAll('button').forEach(b => { b.disabled = false; b.classList.remove('voted'); });
                showToast('Could not submit vote. Please try again.', 'error');
            }
        });
    });
})();


/* ============================================================
   7. VISITOR PASS — APPROVE / REJECT (AJAX with optimistic UI)
   Expects buttons:
     <button data-action="approve" data-url="/..." data-visitor-id="X">Approve</button>
     <button data-action="reject"  data-url="/..." data-visitor-id="X">Reject</button>
   ============================================================ */
(function initVisitorActions() {
    document.addEventListener('click', async e => {
        const btn = e.target.closest('[data-action="approve"], [data-action="reject"]');
        if (!btn || !btn.dataset.url) return;

        const action = btn.dataset.action;
        const url    = btn.dataset.url;
        const card   = btn.closest('.approval-card, .visitor-card, tr');

        // Confirm reject
        if (action === 'reject') {
            if (!confirm('Reject this visitor request?')) return;
        }

        btn.disabled = true;
        const orig   = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrf(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            if (!res.ok) throw new Error();

            // Optimistic removal with fade
            if (card) {
                card.style.transition = 'opacity .35s, transform .35s';
                card.style.opacity    = '0';
                card.style.transform  = 'translateX(8px)';
                setTimeout(() => card.remove(), 380);
            }
            showToast(
                action === 'approve' ? 'Visitor approved successfully!' : 'Visitor request rejected.',
                action === 'approve' ? 'success' : 'info',
                2500
            );
        } catch {
            btn.disabled = false;
            btn.innerHTML = orig;
            showToast('Action failed. Please refresh and try again.', 'error');
        }
    });
})();


/* ============================================================
   8. FILTER + SEARCH — live table filter (client-side)
   Usage: <input data-table-search="myTableId" placeholder="Search…">
   Also handles server-side: debounced form submit on input.
   ============================================================ */
(function initSearch() {
    // Client-side instant filter
    $$('[data-table-search]').forEach(input => {
        const tableId = input.dataset.tableSearch;
        const table   = document.getElementById(tableId);
        if (!table) return;

        input.addEventListener('input', debounce(() => {
            const q = input.value.toLowerCase().trim();
            table.querySelectorAll('tbody tr').forEach(row => {
                row.style.display = !q || row.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        }, 200));
    });

    // Server-side: debounced submit on search input
    $$('[data-search-form] input[name="q"], .search-form input[name="q"]').forEach(input => {
        const form = input.closest('form');
        if (!form) return;
        input.addEventListener('input', debounce(() => form.submit(), 450));
    });
})();


/* ============================================================
   9. AUTO-SUBMIT SELECT FILTERS
   ============================================================ */
$$('.auto-submit select, [data-auto-submit] select').forEach(sel => {
    sel.addEventListener('change', () => sel.closest('form').submit());
});

// Also highlight active filters
$$('.filter-select, .filter-input').forEach(el => {
    const hl = () => el.classList.toggle('filter-active', el.value !== '' && el.value !== 'all');
    hl();
    el.addEventListener('change', hl);
    el.addEventListener('input',  hl);
});


/* ============================================================
   10. COMPLAINT FORM — character counter + preview
   ============================================================ */
(function initComplaintForm() {
    $$('textarea[maxlength], textarea[data-counter]').forEach(ta => {
        const max = parseInt(ta.getAttribute('maxlength') || ta.dataset.maxLen || 500);
        ta.setAttribute('maxlength', max);

        // Build counter element
        const counter = document.createElement('div');
        counter.style.cssText = 'font-size:11px;color:#94a3b8;text-align:right;margin-top:3px;font-family:DM Mono,monospace;';
        counter.textContent = `0 / ${max}`;
        ta.after(counter);

        ta.addEventListener('input', () => {
            const len = ta.value.length;
            counter.textContent = `${len} / ${max}`;
            counter.style.color = len > max * 0.9 ? '#ef4444' : len > max * 0.75 ? '#f59e0b' : '#94a3b8';
        });
    });
})();


/* ============================================================
   11. PAYMENT — click to copy transaction ID
   ============================================================ */
$$('.td-mono[data-copy], td.td-mono').forEach(td => {
    if (!td.textContent.trim() || td.textContent.trim() === '—') return;
    td.style.cursor = 'pointer';
    td.title = 'Click to copy';
    td.addEventListener('click', () => {
        navigator.clipboard?.writeText(td.textContent.trim())
            .then(() => showToast('Copied to clipboard', 'success', 1500));
    });
});


/* ============================================================
   12. SKELETON REVEAL
   Called from templates: skeletonReveal(minMs)
   ============================================================ */
window.skeletonReveal = function (minMs = 1000) {
    const start = Date.now();
    function reveal() {
        const wait = Math.max(0, minMs - (Date.now() - start));
        setTimeout(() => {
            // Target .page-content (resident) or .page-body (admin/security) — whichever is present
            const pb = document.querySelector('.page-content') ||
                       document.querySelector('.page-body') ||
                       document.querySelector('main');
            pb?.classList.remove('sk-active', 'page-loading');
            document.querySelectorAll('.real-content').forEach(el => el.classList.add('sk-revealed'));
        }, wait);
    }
    if (document.readyState === 'complete') reveal();
    else window.addEventListener('load', reveal);
};


/* ============================================================
   13. TOPBAR SCROLL SHADOW
   ============================================================ */
(function initTopbarScroll() {
    const topbar = $('.topbar');
    if (!topbar) return;
    const onScroll = () => topbar.classList.toggle('scrolled', window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
})();


/* ============================================================
   14. DATA-CONFIRM — event-delegated confirmation
   ============================================================ */
document.addEventListener('click', e => {
    const el = e.target.closest('[data-confirm]');
    if (!el) return;
    if (!confirm(el.dataset.confirm || 'Are you sure?')) e.preventDefault();
}, true);


/* ============================================================
   15. TOAST NOTIFICATION SYSTEM
   Usage: showToast('Message', 'success' | 'error' | 'info' | 'warning', durationMs)
   ============================================================ */
(function initToasts() {
    // Inject styles once
    if (!document.getElementById('_res-toast-css')) {
        const s = document.createElement('style');
        s.id = '_res-toast-css';
        s.textContent = `
.res-toast-wrap{position:fixed;bottom:20px;right:20px;display:flex;flex-direction:column;gap:8px;z-index:9999;pointer-events:none}
.res-toast{display:flex;align-items:center;gap:9px;padding:10px 15px;background:#0f172a;color:#e2e8f0;border-radius:12px;font-size:13px;font-weight:500;font-family:'DM Sans',system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.22);border-left:3px solid;min-width:190px;max-width:300px;pointer-events:auto;cursor:pointer;animation:_rToastIn .3s cubic-bezier(.34,1.56,.64,1)}
.res-toast.leaving{animation:_rToastOut .22s ease forwards}
.res-toast.success{border-color:#10b981}.res-toast.error{border-color:#ef4444}.res-toast.info{border-color:#3b82f6}.res-toast.warning{border-color:#f59e0b}
@keyframes _rToastIn{from{opacity:0;transform:translateX(24px) scale(.95)}to{opacity:1;transform:translateX(0) scale(1)}}
@keyframes _rToastOut{from{opacity:1;transform:translateX(0)}to{opacity:0;transform:translateX(16px)}}`;
        document.head.appendChild(s);
    }

    let wrap = null;
    function getWrap() {
        if (!wrap) { wrap = document.createElement('div'); wrap.className = 'res-toast-wrap'; document.body.appendChild(wrap); }
        return wrap;
    }

    const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '!' };

    window.showToast = function (msg, type = 'info', duration = 3500) {
        const el = document.createElement('div');
        el.className = `res-toast ${type}`;
        el.innerHTML = `<span style="font-weight:800;font-size:14px;flex-shrink:0">${icons[type]||'!'}</span><span>${msg}</span>`;
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
   16. FACILITY BOOKING — slot UI helpers
   When a facility is selected, show its available time slots.
   ============================================================ */
(function initFacilityBooking() {
    const facilitySelect = $('select[name="facility"]');
    const slotContainer  = document.getElementById('slotContainer');
    const dateInput      = $('input[name="booking_date"]');

    // Set today as minimum date
    if (dateInput && !dateInput.min) {
        dateInput.min = new Date().toISOString().split('T')[0];
    }

    // Animate facility cards on hover
    $$('.facility-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform    = 'translateY(-4px)';
            card.style.boxShadow    = '0 10px 28px rgba(0,0,0,.12)';
            card.style.transition   = 'all .2s ease';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            card.style.boxShadow = '';
        });
    });

    if (!facilitySelect || !slotContainer) return;

    facilitySelect.addEventListener('change', async () => {
        const id   = facilitySelect.value;
        const date = dateInput?.value;
        if (!id) { slotContainer.innerHTML = ''; return; }

        slotContainer.innerHTML = '<p style="font-size:13px;color:#94a3b8;padding:12px 0">Loading slots…</p>';
        try {
            const url = `/resident/facility-slots/?facility=${id}${date ? '&date=' + date : ''}`;
            const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            if (!res.ok) throw new Error();
            slotContainer.innerHTML = await res.text();
        } catch {
            slotContainer.innerHTML = '<p style="font-size:13px;color:#ef4444;padding:12px 0">Could not load slots. Please refresh.</p>';
        }
    });
})();


/* ============================================================
   17. NOTICE LIST — expand long notices on click
   ============================================================ */
(function initNoticeExpand() {
    $$('.notice-item[data-expandable]').forEach(item => {
        const body = item.querySelector('.notice-body');
        if (!body || body.scrollHeight <= body.clientHeight + 4) return;

        const toggle = document.createElement('button');
        toggle.textContent = 'Show more';
        toggle.style.cssText = 'background:none;border:none;color:#2563eb;font-size:12px;font-weight:600;cursor:pointer;padding:4px 0;font-family:inherit';
        body.after(toggle);

        let expanded = false;
        toggle.addEventListener('click', () => {
            expanded = !expanded;
            body.style.maxHeight   = expanded ? body.scrollHeight + 'px' : '';
            body.style.overflow    = expanded ? 'visible' : 'hidden';
            toggle.textContent     = expanded ? 'Show less' : 'Show more';
        });
    });
})();


/* ============================================================
   18. FORM VALIDATION HELPERS
   Shows inline errors from Django form field errors.
   Adds red ring to invalid fields on submit attempt.
   ============================================================ */
(function initFormValidation() {
    // Auto-style existing .field-error elements
    $$('.field-error, .errorlist').forEach(err => {
        const input = err.previousElementSibling || err.closest('.form-group')?.querySelector('input, select, textarea');
        if (input) {
            input.style.borderColor = '#ef4444';
            input.style.boxShadow   = '0 0 0 3px rgba(239,68,68,.12)';
        }
    });

    // Inline validation on blur
    $$('input[required], select[required], textarea[required]').forEach(input => {
        input.addEventListener('blur', () => {
            const empty = !input.value.trim();
            input.style.borderColor = empty ? '#ef4444' : '';
            input.style.boxShadow   = empty ? '0 0 0 3px rgba(239,68,68,.1)' : '';
        });
        input.addEventListener('input', () => {
            input.style.borderColor = '';
            input.style.boxShadow   = '';
        });
    });
})();