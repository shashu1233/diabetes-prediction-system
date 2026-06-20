// Admin Panel and Power BI Analytics Controller

let pbiGrowthChart = null;
let pbiRiskChart = null;

async function refreshAdminStats() {
    try {
        const response = await authorizedFetch(`${API_BASE}/api/admin/stats`);
        if (!response || !response.ok) return;

        const stats = await response.json();

        // Populate Power BI KPI cards
        document.getElementById("pbi-total-users").textContent = stats.total_users;
        document.getElementById("pbi-total-preds").textContent = stats.total_predictions;
        document.getElementById("pbi-accuracy").textContent = `${(stats.model_accuracy * 100).toFixed(1)}%`;
        document.getElementById("pbi-feedback").textContent = `${stats.avg_rating.toFixed(1)} / 5`;

        // Render Power BI charts
        renderPbiCharts(stats);

        // Load active tab data
        loadActiveAdminTab();
        
    } catch (e) {
        console.error("Error retrieving admin stats:", e);
    }
}

function renderPbiCharts(stats) {
    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    const gridColor = isDark ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)";
    const textColor = isDark ? "#94a3b8" : "#475569";

    // --- Activity Growth Chart (Signups vs predictions over 7 days) ---
    if (pbiGrowthChart) {
        pbiGrowthChart.destroy();
    }
    
    const dates = stats.user_growth.map(d => d.date);
    const signups = stats.user_growth.map(d => d.count);
    const predictions = stats.prediction_growth.map(d => d.count);

    const ctxGrowth = document.getElementById("pbi-growth-chart").getContext("2d");
    pbiGrowthChart = new Chart(ctxGrowth, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'New Patients Signups',
                    data: signups,
                    backgroundColor: 'rgba(99, 102, 241, 0.7)',
                    borderColor: '#6366f1',
                    borderWidth: 1
                },
                {
                    label: 'Vitals Assessments',
                    data: predictions,
                    backgroundColor: 'rgba(20, 184, 166, 0.7)',
                    borderColor: '#14b8a6',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: textColor, font: { family: 'Plus Jakarta Sans', weight: '600' } } }
            },
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: textColor } },
                y: { 
                    grid: { color: gridColor }, 
                    ticks: { color: textColor, stepSize: 1 },
                    beginAtZero: true
                }
            }
        }
    });

    // --- Risk Outcome Chart (Pie) ---
    if (pbiRiskChart) {
        pbiRiskChart.destroy();
    }
    
    const highRisk = stats.risk_distribution.high_risk;
    const lowRisk = stats.risk_distribution.low_risk;

    const ctxRisk = document.getElementById("pbi-risk-chart").getContext("2d");
    pbiRiskChart = new Chart(ctxRisk, {
        type: 'pie',
        data: {
            labels: ['Low Risk Outcome', 'High Risk Outcome'],
            datasets: [{
                data: [lowRisk, highRisk],
                backgroundColor: ['#10b981', '#ef4444'],
                borderColor: isDark ? '#111424' : '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'right',
                    labels: { color: textColor, font: { family: 'Plus Jakarta Sans', weight: '600' } }
                }
            }
        }
    });
}

// Sub-tabs management
let currentAdminTab = "users";

function switchAdminTab(tabName) {
    currentAdminTab = tabName;
    
    // Toggle active tab buttons layout
    const tabs = ["users", "notifications", "feedbacks"];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const view = document.getElementById(`admin-tab-${t}`);
        
        if (t === tabName) {
            btn.style.color = "var(--primary)";
            btn.style.fontWeight = "700";
            view.style.display = "block";
        } else {
            btn.style.color = "var(--text-secondary)";
            btn.style.fontWeight = "600";
            view.style.display = "none";
        }
    });

    loadActiveAdminTab();
}

function loadActiveAdminTab() {
    if (currentAdminTab === "users") {
        loadUsersTable();
    } else if (currentAdminTab === "notifications") {
        loadNotificationsTable();
    } else if (currentAdminTab === "feedbacks") {
        loadFeedbacksTable();
    }
}

async function loadUsersTable() {
    const tbody = document.getElementById("admin-users-body");
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;"><i class="fa-solid fa-spinner fa-spin"></i> Fetching users...</td></tr>`;

    try {
        const res = await authorizedFetch(`${API_BASE}/api/admin/users`);
        if (!res || !res.ok) return;

        const users = await res.json();
        if (users.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted)">No users found in database.</td></tr>`;
            return;
        }

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td style="font-weight: 600;">${user.username}</td>
                <td>${user.email}</td>
                <td><span class="badge ${user.role === 'admin' ? 'badge-warning' : 'badge-success'}">${user.role}</span></td>
                <td>${new Date(user.created_at).toLocaleDateString()}</td>
            </tr>
        `).join("");

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger)">Error fetching user records.</td></tr>`;
    }
}

async function loadNotificationsTable() {
    const tbody = document.getElementById("admin-notifications-body");
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;"><i class="fa-solid fa-spinner fa-spin"></i> Fetching audits...</td></tr>`;

    try {
        const res = await authorizedFetch(`${API_BASE}/api/admin/notifications`);
        if (!res || !res.ok) return;

        const logs = await res.json();
        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted)">No notifications sent yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>User #${log.user_id}</td>
                <td style="text-transform: uppercase; font-weight: 600; font-size: 0.8rem;">
                    <i class="${getChannelIcon(log.notification_type)}"></i> ${log.notification_type}
                </td>
                <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${log.content}</td>
                <td><span class="badge badge-success">${log.status}</span></td>
                <td>${new Date(log.sent_at).toLocaleString()}</td>
            </tr>
        `).join("");

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger)">Error loading notification logs.</td></tr>`;
    }
}

function getChannelIcon(channel) {
    if (channel === "email") return "fa-solid fa-envelope";
    if (channel === "sms") return "fa-solid fa-sms";
    if (channel === "whatsapp") return "fa-brands fa-whatsapp";
    return "fa-solid fa-bell";
}

async function loadFeedbacksTable() {
    const tbody = document.getElementById("admin-feedbacks-body");
    tbody.innerHTML = `<tr><td colspan="4" style="text-align: center;"><i class="fa-solid fa-spinner fa-spin"></i> Fetching ratings...</td></tr>`;

    try {
        const res = await authorizedFetch(`${API_BASE}/api/feedbacks`);
        if (!res || !res.ok) return;

        const feedbacks = await res.json();
        if (feedbacks.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted)">No feedbacks submitted yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = feedbacks.map(f => `
            <tr>
                <td style="font-weight: 600;">${f.username}</td>
                <td style="color: var(--warning);">${"★".repeat(f.rating)}${"☆".repeat(5-f.rating)}</td>
                <td>${f.comment || "<span style='color: var(--text-muted); font-style: italic;'>No text provided</span>"}</td>
                <td>${new Date(f.created_at).toLocaleDateString()}</td>
            </tr>
        `).join("");

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--danger)">Error loading user ratings.</td></tr>`;
    }
}
