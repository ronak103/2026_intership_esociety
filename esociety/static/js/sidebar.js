document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('sidebarOverlay');
    const MOBILE_BREAKPOINT = 1024;

    if (!sidebar || !toggleBtn) return;

    function isMobile() {
        return window.innerWidth <= MOBILE_BREAKPOINT;
    }

    // Toggle sidebar
    toggleBtn.addEventListener('click', function () {
        if (isMobile()) {
            sidebar.classList.toggle('mobile-open');
            overlay.classList.toggle('active');
        } else {
            sidebar.classList.toggle('collapsed');
        }
    });

    // Close sidebar when clicking overlay (mobile)
    if (overlay) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
        });
    }

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            if (!isMobile()) {
                sidebar.classList.remove('mobile-open');
                overlay.classList.remove('active');
            }
        }, 150);
    });

    // Close mobile sidebar on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && isMobile() && sidebar.classList.contains('mobile-open')) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
        }
    });
});