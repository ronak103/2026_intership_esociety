/**
 * admin.js — SocietySync Admin Panel
 * Skeleton CSS lives in Admin_base.html <head>.
 * Each template has its own <div class="sk-wrap"> + <div class="real-content">.
 * This function just handles the timed reveal.
 */

/* ═══════════════════════════════════════════════════════════════
   0. SKELETON REVEAL
   Called by each page template after its skeleton HTML is in place.
   MIN_MS = minimum time skeleton stays visible (so it's actually seen).
═══════════════════════════════════════════════════════════════ */
window.skeletonReveal = function (minMs) {
    minMs = minMs || 1500;
    var startTime = Date.now();

    function reveal() {
        var elapsed = Date.now() - startTime;
        var remaining = minMs - elapsed;
        setTimeout(function () {
            var pb = document.querySelector('.page-body, main');
            if (!pb) return;
            pb.classList.remove('sk-active');
            var rc = pb.querySelector('.real-content');
            if (rc) rc.classList.add('sk-revealed');
        }, Math.max(0, remaining));
    }

    if (document.readyState === 'complete') {
        reveal();
    } else {
        window.addEventListener('load', reveal);
    }
};


/* ═══════════════════════════════════════════════════════════════
   VISITOR LOG MODAL STYLES — injected early (before DOM ready)
═══════════════════════════════════════════════════════════════ */
(function injectVisitorModalStyles() {
    if (document.getElementById('vl-modal-styles')) return;
    const style = document.createElement('style');
    style.id = 'vl-modal-styles';
    style.textContent = `
        .vl-overlay {
            position:fixed; inset:0;
            background:rgba(7,16,32,.45);
            backdrop-filter:blur(3px);
            z-index:1000;
            animation:vlFadeIn .2s ease;
        }
        .vl-modal-box {
            position:fixed; top:50%; left:50%;
            transform:translate(-50%,-46%);
            width:420px; max-width:calc(100vw - 32px);
            background:#fff; border-radius:18px;
            box-shadow:0 28px 70px rgba(0,0,0,.22);
            z-index:1001; opacity:0;
            transition:opacity .2s ease, transform .2s ease;
        }
        .vl-modal-box.vl-modal-visible { opacity:1; transform:translate(-50%,-50%); }
        .vl-modal-header {
            display:flex; align-items:center; gap:14px;
            padding:22px 22px 16px;
            border-bottom:1px solid #F1F5F9;
            position:relative;
        }
        .vl-modal-avatar {
            width:46px; height:46px; border-radius:50%;
            background:#0F4C81; color:#fff;
            display:flex; align-items:center; justify-content:center;
            font-size:20px; font-weight:800; flex-shrink:0;
        }
        .vl-modal-name { font-size:16px; font-weight:800; color:#1E293B; }
        .vl-modal-sub  { font-size:12px; color:#94A3B8; margin-top:2px; font-family:'DM Mono',monospace; }
        .vl-close-btn {
            position:absolute; top:18px; right:18px;
            background:#F1F5F9; border:none; border-radius:8px;
            width:30px; height:30px;
            display:flex; align-items:center; justify-content:center;
            cursor:pointer; color:#64748B; transition:background .15s;
        }
        .vl-close-btn:hover { background:#E2E8F0; color:#1E293B; }
        .vl-modal-badges { display:flex; gap:8px; flex-wrap:wrap; padding:14px 22px 0; }
        .vl-chip { padding:4px 12px; border-radius:20px; font-size:11px; font-weight:700; }
        .vl-modal-grid { padding:14px 22px 22px; display:flex; flex-direction:column; gap:2px; }
        .vl-modal-row {
            display:flex; align-items:center; gap:12px;
            padding:9px 0; border-bottom:1px solid #F8FAFC;
        }
        .vl-modal-row:last-child { border-bottom:none; }
        .vl-modal-icon  { font-size:15px; width:22px; text-align:center; flex-shrink:0; }
        .vl-modal-label { font-size:12px; font-weight:600; color:#64748B; width:110px; flex-shrink:0; }
        .vl-modal-value { font-size:13px; font-weight:600; color:#1E293B; }
        .filter-active  { border-color:#0F4C81 !important; box-shadow:0 0 0 3px rgba(15,76,129,.1) !important; }
        tr[data-id]     { cursor:pointer; }
        @keyframes vlFadeIn { from{opacity:0} to{opacity:1} }
        @keyframes spin     { to{transform:rotate(360deg)} }
        @keyframes toastIn  { from{opacity:0;transform:translateX(30px)} to{opacity:1;transform:translateX(0)} }
    `;
    document.head.appendChild(style);
})();


/* ═══════════════════════════════════════════════════════════════
   DOM READY
═══════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function () {

    /* ──────────────────────────────────────────────────────────
       1. MODAL SYSTEM
    ────────────────────────────────────────────────────────── */
    window.openModal = function (id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.add('open');
        document.body.style.overflow = 'hidden';
        setTimeout(() => {
            const first = el.querySelector('input:not([type=hidden]), select, textarea');
            if (first) first.focus();
        }, 100);
    };

    window.closeModal = function (id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('open');
        document.body.style.overflow = '';
    };

    document.querySelectorAll('.modal-overlay').forEach(o => {
        o.addEventListener('click', e => {
            if (e.target === o) { o.classList.remove('open'); document.body.style.overflow = ''; }
        });
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.open').forEach(m => {
                m.classList.remove('open'); document.body.style.overflow = '';
            });
        }
    });


    /* ──────────────────────────────────────────────────────────
       2. COMPLAINTS — update modal pre-fill
    ────────────────────────────────────────────────────────── */
    window.openUpdateModal = function (id, status, staff) {
        const f = (elId, val) => { const el = document.getElementById(elId); if (el) el.value = val; };
        f('complaintIdField',    id);
        f('id_status',           status);
        f('id_assigned_staff',   staff || '');
        openModal('updateComplaintModal');
    };


    /* ──────────────────────────────────────────────────────────
       3. RESIDENTS — detail modal populate
    ────────────────────────────────────────────────────────── */
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


    /* ──────────────────────────────────────────────────────────
       4. TOAST NOTIFICATIONS
    ────────────────────────────────────────────────────────── */
    window.showToast = function (message, type = 'info', duration = 3500) {
        let box = document.getElementById('toast-container');
        if (!box) {
            box = document.createElement('div');
            box.id = 'toast-container';
            box.style.cssText = 'position:fixed;bottom:24px;right:24px;display:flex;flex-direction:column;gap:10px;z-index:9999;pointer-events:none;';
            document.body.appendChild(box);
        }
        const icons  = { success:'check-circle', error:'exclamation-circle', warning:'exclamation-triangle', info:'info-circle' };
        const colors = { success:'#22c55e', error:'#ef4444', warning:'#f59e0b', info:'#6366f1' };
        const t = document.createElement('div');
        t.style.cssText = `background:#1e293b;color:#e2e8f0;padding:12px 18px;border-radius:10px;
            display:flex;align-items:center;gap:10px;font-size:13.5px;font-weight:500;
            box-shadow:0 4px 20px rgba(0,0,0,.35);pointer-events:auto;cursor:pointer;
            border-left:4px solid ${colors[type]};animation:toastIn .25s ease;max-width:320px;`;
        t.innerHTML = `<i class="fas fa-${icons[type]}" style="color:${colors[type]};font-size:15px;flex-shrink:0;"></i>${message}`;
        box.appendChild(t);
        const dismiss = () => {
            t.style.cssText += 'opacity:0;transform:translateX(30px);transition:opacity .3s,transform .3s;';
            setTimeout(() => t.remove(), 300);
        };
        t.addEventListener('click', dismiss);
        setTimeout(dismiss, duration);
    };

    /* Convert Django messages → toasts */
    document.querySelectorAll('.messages-container .alert, .alert').forEach(alert => {
        const type = alert.classList.contains('alert-success') ? 'success'
                   : alert.classList.contains('alert-danger')  ? 'error'
                   : alert.classList.contains('alert-warning') ? 'warning' : 'info';
        const text = alert.textContent.trim().replace(/\s+/g, ' ');
        if (text) showToast(text, type);
        alert.remove();
    });


    /* ──────────────────────────────────────────────────────────
       5. INLINE CONFIRM — replaces browser confirm()
    ────────────────────────────────────────────────────────── */
    document.querySelectorAll('a[onclick*="confirm"]').forEach(link => {
        const match = link.getAttribute('onclick').match(/confirm\(['"](.+?)['"]\)/);
        const msg   = match ? match[1] : 'Are you sure?';
        const href  = link.href;
        link.removeAttribute('onclick');
        link.addEventListener('click', function (e) {
            e.preventDefault();
            if (link.dataset.confirming) return;
            link.dataset.confirming = '1';
            const orig = link.innerHTML;
            link.innerHTML = `<span style="font-size:11px;display:flex;align-items:center;gap:4px;white-space:nowrap;">
                ${msg}&nbsp;
                <button class="btn btn-success btn-xs" style="padding:2px 8px;">Yes</button>
                <button class="btn btn-outline  btn-xs" style="padding:2px 8px;">No</button>
            </span>`;
            link.querySelectorAll('button')[0].addEventListener('click', ev => { ev.stopPropagation(); window.location.href = href; });
            link.querySelectorAll('button')[1].addEventListener('click', ev => { ev.stopPropagation(); link.innerHTML = orig; delete link.dataset.confirming; });
        });
    });


    /* ──────────────────────────────────────────────────────────
       6. SORTABLE TABLE COLUMNS
    ────────────────────────────────────────────────────────── */
    document.querySelectorAll('.data-table, table').forEach(table => {
        table.querySelectorAll('th').forEach((th, colIdx) => {
            if (/^(actions?|#)?$/i.test(th.textContent.trim())) return;
            th.style.cursor = 'pointer';
            th.style.userSelect = 'none';
            th.title = 'Click to sort';
            let asc = true;
            th.addEventListener('click', () => {
                const tbody = table.querySelector('tbody');
                if (!tbody) return;
                Array.from(tbody.querySelectorAll('tr'))
                    .sort((a, b) => {
                        const aT = a.cells[colIdx]?.textContent.trim() || '';
                        const bT = b.cells[colIdx]?.textContent.trim() || '';
                        const aN = parseFloat(aT.replace(/[₹,]/g, ''));
                        const bN = parseFloat(bT.replace(/[₹,]/g, ''));
                        if (!isNaN(aN) && !isNaN(bN)) return asc ? aN - bN : bN - aN;
                        return asc ? aT.localeCompare(bT) : bT.localeCompare(aT);
                    })
                    .forEach(r => tbody.appendChild(r));
                table.querySelectorAll('.sort-icon').forEach(i => i.remove());
                const icon = document.createElement('i');
                icon.className = `fas fa-sort-${asc ? 'up' : 'down'} sort-icon`;
                icon.style.cssText = 'margin-left:5px;font-size:10px;opacity:.6;';
                th.appendChild(icon);
                asc = !asc;
            });
        });
    });


    /* ──────────────────────────────────────────────────────────
       7. STAT CARD COUNT-UP ANIMATION
    ────────────────────────────────────────────────────────── */
    document.querySelectorAll('.stat-value').forEach(el => {
        const text     = el.textContent.trim();
        const isAmount = text.startsWith('₹');
        const raw      = parseFloat(text.replace(/[₹,]/g, ''));
        if (isNaN(raw) || raw === 0) return;
        let count = 0;
        const steps = 40;
        const iv = setInterval(() => {
            count++;
            const cur = count >= steps ? raw : (raw / steps) * count;
            el.textContent = (isAmount ? '₹' : '') + Math.round(cur).toLocaleString('en-IN');
            if (count >= steps) clearInterval(iv);
        }, 25);
    });


    /* ──────────────────────────────────────────────────────────
       8. DATE INPUTS — default to today if empty
    ────────────────────────────────────────────────────────── */
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"]').forEach(inp => { if (!inp.value) inp.value = today; });


    /* ──────────────────────────────────────────────────────────
       9. COPY TRANSACTION IDs on click
    ────────────────────────────────────────────────────────── */
    document.querySelectorAll('td').forEach(td => {
        if (td.style.fontFamily?.includes('Mono') && td.textContent.trim() !== '—') {
            td.style.cursor = 'pointer';
            td.title = 'Click to copy';
            td.addEventListener('click', () => {
                navigator.clipboard?.writeText(td.textContent.trim())
                    .then(() => showToast('Transaction ID copied!', 'success', 1800));
            });
        }
    });


    /* ──────────────────────────────────────────────────────────
       10. TAB PILL ACTIVE STATE (client-side highlight)
    ────────────────────────────────────────────────────────── */
    document.querySelectorAll('.tab-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            pill.closest('.tab-pills')?.querySelectorAll('.tab-pill')
                .forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
        });
    });


    /* ══════════════════════════════════════════════════════════
       VISITOR LOGS — only active when filter-form is on page
    ══════════════════════════════════════════════════════════ */
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {

        /* Auto-submit dropdowns */
        filterForm.querySelectorAll("select[name='type'], select[name='status']")
            .forEach(el => el.addEventListener('change', () => filterForm.submit()));

        /* Live search debounce (450 ms) */
        const qInput = filterForm.querySelector("input[name='q']");
        let qTimer;
        if (qInput) {
            qInput.addEventListener('input', () => {
                clearTimeout(qTimer);
                qTimer = setTimeout(() => filterForm.submit(), 450);
            });
        }

        /* Highlight active filters */
        filterForm.querySelectorAll('.filter-input').forEach(el => {
            const hl = () => el.classList.toggle('filter-active', el.value !== '' && el.value !== 'all');
            hl();
            el.addEventListener('change', hl);
            el.addEventListener('input',  hl);
        });

        /* Results bar fade-in */
        const rb = document.querySelector('.results-bar');
        if (rb) { rb.style.opacity = '0'; rb.style.transition = 'opacity .3s'; setTimeout(() => rb.style.opacity = '1', 100); }

        /* Row click → visitor detail modal */
        const tbody = document.querySelector('table tbody');
        if (tbody) {
            tbody.addEventListener('click', e => {
                const row = e.target.closest('tr[data-id]');
                if (row) buildVisitorModal(row);
            });
        }

        /* Export button animation */
        const exportBtn = document.querySelector('.btn-export');
        if (exportBtn) {
            exportBtn.addEventListener('click', function () {
                const orig = exportBtn.innerHTML;
                exportBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                    style="animation:spin .7s linear infinite"><polyline points="23 4 23 10 17 10"/>
                    <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg> Exporting…`;
                exportBtn.style.opacity = '0.75';
                setTimeout(() => { exportBtn.innerHTML = orig; exportBtn.style.opacity = '1'; }, 2500);
            });
        }
    }


    /* ── VISITOR LOG: Build & show detail modal ────────────── */
    function buildVisitorModal(row) {
        document.getElementById('vl-modal')?.remove();

        const d = row.dataset;
        const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : '—';
        const statusColors = {
            inside:'#10B981', exited:'#64748B', denied:'#EF4444', waiting:'#F59E0B',
            approved:'#10B981', rejected:'#EF4444', pending:'#F59E0B',
            guest:'#1E40AF', delivery:'#5B21B6', maintenance:'#92400E', staff:'#334155',
        };
        const ec = statusColors[d.entryStatus]    || '#64748B';
        const ac = statusColors[d.approvalStatus] || '#F59E0B';
        const tc = statusColors[d.visitorType]    || '#334155';

        const r = (icon, label, val) => `
            <div class="vl-modal-row">
                <span class="vl-modal-icon">${icon}</span>
                <span class="vl-modal-label">${label}</span>
                <span class="vl-modal-value">${val || '—'}</span>
            </div>`;

        const modal = document.createElement('div');
        modal.id    = 'vl-modal';
        modal.innerHTML = `
            <div class="vl-overlay"  id="vl-overlay"></div>
            <div class="vl-modal-box" role="dialog" aria-modal="true">
                <div class="vl-modal-header">
                    <div class="vl-modal-avatar">${(d.visitorName || '?')[0].toUpperCase()}</div>
                    <div>
                        <div class="vl-modal-name">${d.visitorName || '—'}</div>
                        <div class="vl-modal-sub">${d.mobile || '—'}</div>
                    </div>
                    <button class="vl-close-btn" id="vl-close" aria-label="Close">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
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
                    ${r('🏠','Unit',          d.unit)}
                    ${r('👤','Resident',      d.resident)}
                    ${r('📅','Expected Date', d.expectedDate)}
                    ${r('🕐','Entry Time',    d.entryTime)}
                    ${r('🕔','Exit Time',     d.exitTime)}
                    ${r('🚗','Vehicle',       d.vehicle)}
                    ${r('👮','Guard',         d.guard)}
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
        document.getElementById('vl-close').addEventListener('click', close);
        document.getElementById('vl-overlay').addEventListener('click', close);
        document.addEventListener('keydown', esc);
    }

}); // end DOMContentLoaded