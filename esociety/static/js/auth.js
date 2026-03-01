document.addEventListener("DOMContentLoaded", function () {

    const toggleBtns  = document.querySelectorAll(".toggle-btn");
    const slider      = document.querySelector(".slider");
    const formTrack   = document.querySelector(".form-track");
    const formSlider  = document.querySelector(".form-slider");
    const panelSignin = document.getElementById("panel-signin");
    const panelSignup = document.getElementById("panel-signup");
    const toggles = document.querySelectorAll(".toggle-password");

    /* ─────────────────────────────────────────
       Measure a panel's TRUE height in isolation.
       Temporarily make it position:absolute so it
       breaks out of the shared flex-row height.
    ───────────────────────────────────────── */
    function measurePanel(panel) {
        panel.style.position   = "absolute";
        panel.style.visibility = "hidden";
        panel.style.width      = formSlider.offsetWidth + "px";

        const h = panel.scrollHeight;

        panel.style.position   = "";
        panel.style.visibility = "";
        panel.style.width      = "";

        return h;
    }

    /* ── Animate slider height to active panel ── */
    function setHeight(panel) {
        formSlider.style.height = measurePanel(panel) + "px";
    }

    /* ── Switch helpers ── */
    function goToSignin() {
        formTrack.style.transform = "translateX(0%)";
        slider.classList.remove("move");
        toggleBtns[0].classList.add("active");
        toggleBtns[1].classList.remove("active");
        setHeight(panelSignin);
    }

    function goToSignup() {
        formTrack.style.transform = "translateX(-50%)";
        slider.classList.add("move");
        toggleBtns[1].classList.add("active");
        toggleBtns[0].classList.remove("active");
        setHeight(panelSignup);
    }
    toggles.forEach(toggle => {
        toggle.addEventListener("click", function () {

            const input = this.previousElementSibling;

            if (!input) return;

            const type = input.getAttribute("type") === "password" ? "text" : "password";
            input.setAttribute("type", type);

            this.classList.toggle("fa-eye");
            this.classList.toggle("fa-eye-slash");
        });
    });


    /* ── Set the correct panel position immediately (no animation) ── */
    const isSignup = window.location.pathname.includes("signup");

    if (isSignup) {
        goToSignup();
    } else {
        goToSignin();
    }

    /* ── Wait for full paint (fonts + layout) before measuring ── */
    window.addEventListener("load", function () {
        /* Disable transition for the initial snap */
        formSlider.style.transition = "none";
        if (isSignup) {
            setHeight(panelSignup);
        } else {
            setHeight(panelSignin);
        }

        /* Re-enable smooth transition after browser has painted */
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                formSlider.style.transition = "";
            });
        });
    });

    /* ── Top toggle bar clicks ── */
    toggleBtns.forEach((btn, index) => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            if (index === 1) {
                goToSignup();
                history.pushState({}, "", this.href);
            } else {
                goToSignin();
                history.pushState({}, "", this.href);
            }
        });
    });

    /* ── Bottom "Sign In / Sign Up" link clicks ── */
    document.querySelectorAll(".js-switch").forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            if (this.dataset.type === "signup") {
                goToSignup();
                history.pushState({}, "", this.href);
            } else {
                goToSignin();
                history.pushState({}, "", this.href);
            }
        });
    });

});

