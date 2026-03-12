'use strict';

/* same $ helper used in resident.js */
const _$ = (sel, ctx) => (ctx || document).querySelector(sel);

(function initSidebar() {
    const sidebar   = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle') ||
                      document.querySelector('.sidebar-toggle');
    const overlay   = document.getElementById('sidebarOverlay');
    const mainWrap  = document.getElementById('mainContent') ||
                      document.querySelector('.main-content');

    if (!sidebar || !toggleBtn) return;

    const MOBILE_BP = 1024;
    const STORE_KEY = 'adm_sidebar_collapsed';

    function isMobile() { return window.innerWidth <= MOBILE_BP; }

    function lockScroll(lock) {
        document.body.style.overflow = lock ? 'hidden' : '';
    }

    function setCollapsed(collapsed) {
        sidebar.classList.toggle('collapsed', collapsed);
        localStorage.setItem(STORE_KEY, collapsed);
        if (mainWrap && !isMobile() && !CSS.supports('selector(:has(*))')) {
            mainWrap.style.marginLeft = collapsed ? '0' : '';
        }
    }

    function setMobileOpen(open) {
        sidebar.classList.toggle('mobile-open', open);
        if (overlay) overlay.classList.toggle('active', open);
        lockScroll(open);
    }

    /* restore on load */
    if (!isMobile()) {
        setCollapsed(localStorage.getItem(STORE_KEY) === 'true');
    }

    toggleBtn.addEventListener('click', () => {
        if (isMobile()) {
            setMobileOpen(!sidebar.classList.contains('mobile-open'));
        } else {
            setCollapsed(!sidebar.classList.contains('collapsed'));
        }
    });

    if (overlay) overlay.addEventListener('click', () => setMobileOpen(false));

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
                if (overlay) overlay.classList.remove('active');
                lockScroll(false);
                if (mainWrap) mainWrap.style.marginLeft = '';
                setCollapsed(localStorage.getItem(STORE_KEY) === 'true');
            }
        }, 150);
    });

    /* active link highlight */
    const path = window.location.pathname.replace(/\/$/, '');
    document.querySelectorAll('.sidebar-link').forEach(link => {
        const href = link.getAttribute('href');
        if (!href || href === '#') return;
        const lp = href.replace(/\/$/, '');
        if (path === lp || (lp.length > 1 && path.startsWith(lp))) {
            link.closest('.sidebar-menu-item')?.classList.add('active');
        }
    });
})();