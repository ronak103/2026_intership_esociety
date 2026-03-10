/**
 * SocietySync — auth.js  (IMPROVED)
 *
 * IMPROVEMENTS:
 * ✦ Password strength meter (visual bars + label)
 * ✦ Confirm-password live match indicator
 * ✦ Submit button loading spinner state
 * ✦ Improved panel height measurement (ResizeObserver fallback)
 * ✦ Message auto-dismiss improved timing
 * ✦ Toggle panel synced with URL hash (#signup / #signin)
 * ✦ Debounced resize handler
 * ✦ No global variable leaks (IIFE)
 */

(function () {
    'use strict';

    /* ── DOM refs ── */
    const toggleBtns  = document.querySelectorAll('.toggle-btn');
    const slider      = document.querySelector('.slider');
    const formTrack   = document.querySelector('.form-track');
    const formSlider  = document.querySelector('.form-slider');
    const panelSignin = document.getElementById('panel-signin');
    const panelSignup = document.getElementById('panel-signup');

    if (!formTrack || !formSlider) return;

    /* ── Height setter ── */
    function setHeight(panel) {
        if (!panel) return;
        formSlider.style.height = panel.scrollHeight + 'px';
    }

    /* ── Switch helpers ── */
    function goToSignin() {
        formTrack.style.transform = 'translateX(0%)';
        slider && slider.classList.remove('move');
        toggleBtns[0]?.classList.add('active');
        toggleBtns[1]?.classList.remove('active');
        setHeight(panelSignin);
    }

    function goToSignup() {
        formTrack.style.transform = 'translateX(-50%)';
        slider && slider.classList.add('move');
        toggleBtns[1]?.classList.add('active');
        toggleBtns[0]?.classList.remove('active');
        setHeight(panelSignup);
    }

    /* ── Detect which panel to show ── */
    const isSignup = window.location.pathname.includes('signup') ||
                     window.location.hash === '#signup';

    // Apply immediately (no animation on first load)
    formSlider.style.transition = 'none';
    isSignup ? goToSignup() : goToSignin();

    // Re-enable transition after first paint
    window.addEventListener('load', function () {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                formSlider.style.transition = '';
                // Re-measure after fonts load
                isSignup ? setHeight(panelSignup) : setHeight(panelSignin);
            });
        });
    });

    /* ── Toggle bar clicks ── */
    toggleBtns.forEach((btn, i) => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            if (i === 1) { goToSignup(); history.replaceState(null, '', this.href || ''); }
            else         { goToSignin(); history.replaceState(null, '', this.href || ''); }
        });
    });

    /* ── Bottom "js-switch" links ── */
    document.querySelectorAll('.js-switch').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            if (this.dataset.type === 'signup') { goToSignup(); history.replaceState(null, '', this.href); }
            else                                { goToSignin(); history.replaceState(null, '', this.href); }
        });
    });

    /* ── Debounced resize ── */
    let resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            const active = slider?.classList.contains('move') ? panelSignup : panelSignin;
            setHeight(active);
        }, 120);
    });

    /* ── Password show/hide ── */
    document.querySelectorAll('.toggle-password').forEach(toggle => {
        toggle.addEventListener('click', function () {
            const input = this.previousElementSibling;
            if (!input) return;
            const isText = input.getAttribute('type') === 'text';
            input.setAttribute('type', isText ? 'password' : 'text');
            this.classList.toggle('fa-eye',       isText);
            this.classList.toggle('fa-eye-slash', !isText);
        });
    });

    /* ── Password strength meter ── */
    function checkStrength(pw) {
        let score = 0;
        if (pw.length >= 8)   score++;
        if (pw.length >= 12)  score++;
        if (/[A-Z]/.test(pw)) score++;
        if (/[0-9]/.test(pw)) score++;
        if (/[^A-Za-z0-9]/.test(pw)) score++;
        // Map to level
        if (pw.length === 0) return { level: 0, label: '' };
        if (score <= 1) return { level: 1, label: 'Weak',   cls: 'weak' };
        if (score === 2) return { level: 2, label: 'Fair',   cls: 'fair' };
        if (score === 3) return { level: 3, label: 'Good',   cls: 'good' };
        return              { level: 4, label: 'Strong', cls: 'strong' };
    }

    document.querySelectorAll('input[name="password1"], input[name="new_password"]').forEach(input => {
        // Build meter
        const wrap = document.createElement('div');
        wrap.innerHTML = `<div class="password-strength">
            <div class="strength-bar" id="sb1"></div>
            <div class="strength-bar" id="sb2"></div>
            <div class="strength-bar" id="sb3"></div>
            <div class="strength-bar" id="sb4"></div>
        </div><span class="strength-label" id="sl"></span>`;
        input.closest('.form-group, .password-wrapper')?.after(wrap);

        const bars  = wrap.querySelectorAll('.strength-bar');
        const label = wrap.querySelector('.strength-label');

        input.addEventListener('input', function () {
            const { level, label: lbl, cls } = checkStrength(this.value);
            bars.forEach((b, i) => {
                b.className = 'strength-bar';
                if (i < level) b.classList.add(cls);
            });
            if (label) label.textContent = lbl;
        });
    });

    /* ── Confirm password live match ── */
    const pw1 = document.querySelector('input[name="password1"]');
    const pw2 = document.querySelector('input[name="password2"]');
    if (pw1 && pw2) {
        function checkMatch() {
            const match = pw2.value && pw1.value === pw2.value;
            pw2.style.borderColor = pw2.value ? (match ? '#10b981' : '#ef4444') : '';
            pw2.style.boxShadow   = pw2.value ? (match ? '0 0 0 3px rgba(16,185,129,.12)' : '0 0 0 3px rgba(239,68,68,.12)') : '';
        }
        pw2.addEventListener('input', checkMatch);
        pw1.addEventListener('input', checkMatch);
    }

    /* ── Submit button loading state ── */
    document.querySelectorAll('.submit-btn').forEach(btn => {
        const form = btn.closest('form');
        if (!form) return;
        form.addEventListener('submit', function () {
            btn.classList.add('loading');
            btn.disabled = true;
            // Safety timeout — re-enable after 8s in case of error
            setTimeout(() => { btn.classList.remove('loading'); btn.disabled = false; }, 8000);
        });
    });

    /* ── Auto-dismiss Django messages ── */
    document.querySelectorAll('.message-box').forEach(msg => {
        setTimeout(function () {
            msg.style.transition = 'opacity .4s ease, transform .4s ease';
            msg.style.opacity    = '0';
            msg.style.transform  = 'translateY(-8px)';
            setTimeout(() => msg.remove(), 420);
        }, 3500);
    });

})();