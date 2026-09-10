// ── Admin Dashboard JavaScript ────────────────────────────────────────────

/**
 * Toggle the admin sidebar open/closed on small screens.
 */
function toggleSidebar() {
    const sidebar = document.querySelector(".admin-sidebar");
    if (sidebar) {
        sidebar.classList.toggle("open");
    }
}

/**
 * Toggle the notifications dropdown panel.
 */
function toggleNotifications() {
    const panel = document.getElementById("notificationsPanel");
    if (panel) {
        const isVisible = panel.style.display === "block";
        panel.style.display = isVisible ? "none" : "block";
    }
}

// Close notifications panel when clicking outside it
document.addEventListener("click", function (e) {
    const panel = document.getElementById("notificationsPanel");
    const bell = document.querySelector(".notif-bell");
    if (panel && bell && !panel.contains(e.target) && !bell.contains(e.target)) {
        panel.style.display = "none";
    }
});

// ── Tab switching for admin dashboard ────────────────────────────────────
function showTab(tabId) {
    document.querySelectorAll(".admin-tab-content").forEach(function (tab) {
        tab.style.display = "none";
    });
    const target = document.getElementById(tabId);
    if (target) {
        target.style.display = "block";
    }
}

// ── Confirm before delete ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".delete-form").forEach(function (form) {
        form.addEventListener("submit", function (e) {
            if (!confirm("Are you sure you want to delete this record? This cannot be undone.")) {
                e.preventDefault();
            }
        });
    });
});
