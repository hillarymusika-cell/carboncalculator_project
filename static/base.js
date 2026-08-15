(function () {
    const menu   = document.getElementById("menu");
    const recent = document.getElementById("recent");
    const historyPanel = document.getElementById("history-panel");
    const historyBody  = document.getElementById("history-body");
    const historyLatest = document.getElementById("history-latest-value");
    const nav    = document.getElementById("nav");
    const navBar = document.getElementById("nav-bar");
    const logoutBtn = document.getElementById("logout");
    const links  = nav ? nav.querySelectorAll("a") : [];
    let historyLoaded = false;

    const routes = window.APP_ROUTES || {};
    const csrfToken = window.CSRF_TOKEN || "";

    function openMenu() {
        navBar.classList.add("open");
        nav.setAttribute("aria-hidden", "false");
        menu.setAttribute("aria-expanded", "true");
        menu.innerHTML = "&times;";
        menu.setAttribute("aria-label", "Close menu");
    }

    function closeMenu() {
        navBar.classList.remove("open");
        nav.setAttribute("aria-hidden", "true");
        menu.setAttribute("aria-expanded", "false");
        menu.innerHTML = "&#9776;";
        menu.setAttribute("aria-label", "Open menu");
        if (historyPanel) {
            historyPanel.classList.remove("open");
            historyPanel.setAttribute("aria-hidden", "true");
            if (recent) recent.setAttribute("aria-expanded", "false");
        }
    }

    function toggleMenu() {
        navBar.classList.contains("open") ? closeMenu() : openMenu();
    }

    if (menu) menu.addEventListener("click", toggleMenu);

    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            fetch(routes.logoutUrl || "/auth/logout", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                }
            }).then(response => {
                if (response.ok) {
                    window.location.href = routes.loginUrl || "/auth/login";
                } else {
                    console.error("Logout failed");
                }
            }).catch(error => console.error("Error during logout:", error));
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && navBar.classList.contains("open")) closeMenu();
    });

    if (recent && historyPanel) {
        recent.addEventListener("click", async () => {
            const isOpen = historyPanel.classList.contains("open");
            if (isOpen) {
                historyPanel.classList.remove("open");
                historyPanel.setAttribute("aria-hidden", "true");
                recent.setAttribute("aria-expanded", "false");
                return;
            }
            historyPanel.classList.add("open");
            historyPanel.setAttribute("aria-hidden", "false");
            recent.setAttribute("aria-expanded", "true");
            if (historyLoaded) return;

            try {
                const response = await fetch(routes.historyUrl || "/history");
                if (!response.ok) throw new Error("Failed to load history");
                const data = await response.json();
                const entries = Array.isArray(data.history) ? data.history : [];

                if (entries.length === 0) {
                    historyLatest.textContent = "—";
                    historyBody.innerHTML = '<tr><td><small style="color:#c8e0de;">No recent emissions</small></td></tr>';
                    historyLoaded = true;
                    return;
                }

                const latestTotalKg = (entries[0].search && entries[0].search.total_kg_co2e) || 0;
                historyLatest.textContent = (latestTotalKg / 1000).toFixed(2) + " t CO₂e";

                historyBody.innerHTML = "";
                entries.slice(0, 5).forEach((entry) => {
                    const totalKg = (entry.search && entry.search.total_kg_co2e) || 0;
                    const date = entry.time ? new Date(entry.time).toLocaleDateString() : "N/A";
                    const row = document.createElement("tr");
                    row.innerHTML = `<td>${date}</td><td>${(totalKg / 1000).toFixed(2)} t</td>`;
                    row.style.cursor = "pointer";
                    row.addEventListener("click", () => {
                        window.location.href = (routes.dashboardUrl || "/dashboard") + "#history-view";
                    });
                    historyBody.appendChild(row);
                });
                historyLoaded = true;
            } catch (error) {
                console.error("Error loading recent emissions:", error);
                historyBody.innerHTML = '<tr><td><small style="color:#ffb3b3;">Could not load history</small></td></tr>';
            }
        });
    }

    const currentPath = window.location.pathname;
    links.forEach((link) => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }
        link.addEventListener("click", closeMenu);
    });
})();
