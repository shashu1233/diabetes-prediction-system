// Global Application view coordinator & state manager

let currentView = "dashboard";

// Swaps active views on navigation click
function switchView(viewName) {
    // Guards to block authenticated views if token is missing
    const token = getAuthToken();
    if (!token) {
        showAuthScreen();
        return;
    }

    currentView = viewName;

    // Toggle active link styles
    const navLinks = ["dashboard", "predict", "history", "profile", "admin"];
    navLinks.forEach(item => {
        const link = document.getElementById(`nav-${item}`);
        if (link) {
            if (item === viewName) {
                link.classList.add("active");
            } else {
                link.classList.remove("active");
            }
        }
    });

    // Toggle view containers active status
    const views = ["dashboard", "predict", "history", "profile", "admin"];
    views.forEach(item => {
        const element = document.getElementById(`view-${item}`);
        if (element) {
            if (item === viewName) {
                element.classList.add("active-view");
            } else {
                element.classList.remove("active-view");
            }
        }
    });

    // Setup Header Text dynamically
    const title = document.getElementById("view-title");
    const subtitle = document.getElementById("view-subtitle");
    
    if (viewName === "dashboard") {
        title.textContent = "Health Dashboard";
        subtitle.textContent = "Overview of health metrics, assessment logs, and quick AI insights.";
        loadDashboardData();
    } else if (viewName === "predict") {
        title.textContent = "AI Risk Predictor";
        subtitle.textContent = "Enter clinical vitals to run Random Forest diagnostics and load Gemini guidelines.";
    } else if (viewName === "history") {
        title.textContent = "Assessment History";
        subtitle.textContent = "Browse, filter, and search your recorded diagnostics reports.";
        loadHistoryData();
    } else if (viewName === "profile") {
        title.textContent = "Profile Settings";
        subtitle.textContent = "Keep your demographic and physical health profile records up to date.";
        loadProfileData();
    } else if (viewName === "admin") {
        title.textContent = "Executive Analytics Workspace";
        subtitle.textContent = "DirectQuery interactive charts detailing system performance & patient audit logs.";
        refreshAdminStats();
    }
}

// --- ASSESSMENT HISTORY DATA LOAD ---
async function loadHistoryData(filters = "") {
    const tbody = document.getElementById("history-table-body");
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center;"><i class="fa-solid fa-spinner fa-spin"></i> Fetching records...</td></tr>`;

    try {
        const response = await authorizedFetch(`${API_BASE}/api/predictions/history?${filters}`);
        if (!response || !response.ok) return;

        const data = await response.json();
        
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">No matching prediction records found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(item => {
            const riskProb = Math.round(item.result_probability * 100);
            const badgeClass = item.result_class === 1 ? "badge-danger" : "badge-success";
            const badgeText = item.result_class === 1 ? "High Risk" : "Low Risk";
            
            return `
                <tr>
                    <td style="font-weight: 500;">${new Date(item.created_at).toLocaleDateString()}</td>
                    <td>${item.age}</td>
                    <td style="font-weight: 600;">${item.glucose} <span style="font-size: 0.75rem; color: var(--text-muted)">mg/dL</span></td>
                    <td>${item.blood_pressure}</td>
                    <td>${item.bmi.toFixed(1)}</td>
                    <td>${item.insulin}</td>
                    <td style="font-weight: 700; color: ${item.result_class === 1 ? 'var(--danger)' : 'var(--success)'}">${riskProb}%</td>
                    <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                    <td>
                        <button class="btn btn-secondary" onclick="viewAiSuggestionAlert('${item.id}')" style="padding: 6px 10px; font-size: 0.75rem;">
                            <i class="fa-solid fa-sparkles" style="color: var(--secondary);"></i> Advice
                        </button>
                        <div id="ai-text-store-${item.id}" style="display: none;">${item.gemini_suggestion || "No advice plan saved."}</div>
                    </td>
                </tr>
            `;
        }).join("");
        
    } catch (e) {
        console.error("Error loading history list:", e);
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--danger)">Failed to load history report.</td></tr>`;
    }
}

// Dynamic display of generative advice inside a modal/alert popup
function viewAiSuggestionAlert(predId) {
    const rawMarkdown = document.getElementById(`ai-text-store-${predId}`).innerHTML;
    
    // Create simple full screen overlay modal dynamically
    const modal = document.createElement("div");
    modal.style.position = "fixed";
    modal.style.top = "0";
    modal.style.left = "0";
    modal.style.width = "100%";
    modal.style.height = "100%";
    modal.style.background = "rgba(0,0,0,0.6)";
    modal.style.backdropFilter = "blur(8px)";
    modal.style.zIndex = "10000";
    modal.style.display = "flex";
    modal.style.alignItems = "center";
    modal.style.justifyContent = "center";
    modal.style.padding = "20px";

    const contentCard = document.createElement("div");
    contentCard.className = "glass-card";
    contentCard.style.maxWidth = "600px";
    contentCard.style.width = "100%";
    contentCard.style.maxHeight = "85vh";
    contentCard.style.overflowY = "auto";
    contentCard.style.padding = "32px";
    contentCard.style.background = "var(--bg-surface-hover)";

    // Markdown parser in predict.js can be reused
    const adviceHtml = parseMarkdownToHtml(rawMarkdown);

    contentCard.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;">
            <h3 style="font-weight: 700; color: var(--secondary);"><i class="fa-solid fa-sparkles"></i> AI Health Advice</h3>
            <button class="btn btn-secondary" id="modal-close-btn" style="padding: 6px 12px; font-size: 0.8rem;">Close</button>
        </div>
        <div class="gemini-body">${adviceHtml}</div>
    `;

    modal.appendChild(contentCard);
    document.body.appendChild(modal);

    const closeModal = () => modal.remove();
    document.getElementById("modal-close-btn").addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });
}

// History table filters
function applyHistoryFilters() {
    const glucMin = document.getElementById("filter-glucose-min").value;
    const glucMax = document.getElementById("filter-glucose-max").value;
    const bmiMin = document.getElementById("filter-bmi-min").value;
    const bmiMax = document.getElementById("filter-bmi-max").value;
    const outcome = document.getElementById("filter-outcome").value;

    let params = [];
    if (glucMin) params.push(`glucose_min=${glucMin}`);
    if (glucMax) params.push(`glucose_max=${glucMax}`);
    if (bmiMin) params.push(`bmi_min=${bmiMin}`);
    if (bmiMax) params.push(`bmi_max=${bmiMax}`);
    if (outcome !== "") params.push(`outcome=${outcome}`);

    loadHistoryData(params.join("&"));
}

function clearHistoryFilters() {
    document.getElementById("filter-glucose-min").value = "";
    document.getElementById("filter-glucose-max").value = "";
    document.getElementById("filter-bmi-min").value = "";
    document.getElementById("filter-bmi-max").value = "";
    document.getElementById("filter-outcome").value = "";
    loadHistoryData();
}

// --- PROFILE SECTION CONTROLS ---
async function loadProfileData() {
    try {
        const response = await authorizedFetch(`${API_BASE}/api/profile`);
        if (!response || !response.ok) return;

        const profile = await response.json();
        
        document.getElementById("profile-name").value = profile.full_name || "";
        document.getElementById("profile-age").value = profile.age || 30;
        document.getElementById("profile-gender").value = profile.gender || "other";
        document.getElementById("profile-height").value = profile.height || "";
        document.getElementById("profile-weight").value = profile.weight || "";
        document.getElementById("profile-phone").value = profile.phone || "";
        
    } catch (e) {
        console.error("Error loading profile inputs:", e);
    }
}

// Profile submission
document.addEventListener("DOMContentLoaded", () => {
    const profileForm = document.getElementById("profile-form");
    profileForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            full_name: document.getElementById("profile-name").value.trim(),
            age: parseInt(document.getElementById("profile-age").value),
            gender: document.getElementById("profile-gender").value,
            height: parseFloat(document.getElementById("profile-height").value) || null,
            weight: parseFloat(document.getElementById("profile-weight").value) || null,
            phone: document.getElementById("profile-phone").value.trim() || null
        };

        try {
            const response = await authorizedFetch(`${API_BASE}/api/profile`, {
                method: "PUT",
                body: JSON.stringify(payload)
            });

            if (response && response.ok) {
                showToast("Profile details updated successfully.", "success");
                
                // Update username displays on the sidebar badge
                document.getElementById("user-display-name").textContent = payload.full_name;
                
                // Re-fetch profile to sync state
                loadProfileData();
            } else {
                showToast("Failed to save profile changes.", "error");
            }
        } catch (err) {
            showToast("Server error occurred saving profile details.", "error");
        }
    });

    // --- SYSTEM CLOCK TIMESTAMPS ---
    const timeDisplay = document.getElementById("live-time-display");
    function updateClock() {
        const now = new Date();
        timeDisplay.innerHTML = `<i class="fa-regular fa-clock"></i> ${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
    }
    updateClock();
    setInterval(updateClock, 1000);

    // --- THEME STATE MANAGER ---
    const themeBtn = document.getElementById("theme-toggle");
    const localTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", localTheme);
    updateThemeIcon(localTheme);

    themeBtn.addEventListener("click", () => {
        const activeTheme = document.documentElement.getAttribute("data-theme");
        const nextTheme = activeTheme === "dark" ? "light" : "dark";
        
        document.documentElement.setAttribute("data-theme", nextTheme);
        localStorage.setItem("theme", nextTheme);
        updateThemeIcon(nextTheme);
        
        // Refresh active views charts to reload grids/label colors
        if (currentView === "dashboard") {
            loadDashboardData();
        } else if (currentView === "admin") {
            refreshAdminStats();
        }
    });

    function updateThemeIcon(theme) {
        const icon = themeBtn.querySelector("i");
        if (theme === "light") {
            icon.className = "fa-solid fa-sun";
            themeBtn.querySelector("span").textContent = "Light Mode";
        } else {
            icon.className = "fa-solid fa-moon";
            themeBtn.querySelector("span").textContent = "Dark Mode";
        }
    }

    // Run active auth verification at startup
    checkAuthStatus();
});
