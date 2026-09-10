console.log("Medical Clinic Django Site Loaded");

// ── Auto-sliding banner (home page only) ──────────────────────────────────
const slides = document.querySelector(".slides");

if (slides) {
    const slideItems = document.querySelectorAll(".slide");
    const totalSlides = slideItems.length;
    let currentSlide = 0;

    function autoSlide() {
        currentSlide = (currentSlide + 1) % totalSlides;
        slides.style.transform = `translateX(-${currentSlide * 100}%)`;
    }

    if (totalSlides > 1) {
        setInterval(autoSlide, 5000);
    }
}

// ── Flash message auto-dismiss ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.opacity = "0";
            alert.style.transition = "opacity 0.5s ease";
            setTimeout(function () { alert.remove(); }, 500);
        }, 4000);
    });
});
