// Patient Dashboard Analytics Controller

let trendsChart = null;
let pieChart = null;

async function loadDashboardData() {
    try {
        const response = await authorizedFetch(`${API_BASE}/api/predictions/history`);
        if (!response || !response.ok) return;

        const history = await response.json();
        
        // Populate stats counts
        const totalAssessments = history.length;
        document.getElementById("dashboard-total-tests").textContent = totalAssessments;
        
        if (totalAssessments === 0) {
            document.getElementById("dashboard-avg-glucose").innerHTML = `0 <span style="font-size: 1rem; font-weight: 500; color: var(--text-muted)">mg/dL</span>`;
            document.getElementById("dashboard-avg-bmi").textContent = "0.0";
            document.getElementById("dashboard-avg-rating").innerHTML = `0.0 <span style="font-size: 1rem; font-weight: 500; color: var(--text-muted)">/ 5</span>`;
            document.getElementById("dashboard-insights-text").textContent = "No predictions logged yet. Switch to 'Predict Risk' in the sidebar to run your first evaluation.";
            
            // Destroy existing charts if any
            if (trendsChart) trendsChart.destroy();
            if (pieChart) pieChart.destroy();
            return;
        }

        // Calculate Averages
        const sumGlucose = history.reduce((sum, item) => sum + item.glucose, 0);
        const avgGlucose = Math.round(sumGlucose / totalAssessments);

        const sumBmi = history.reduce((sum, item) => sum + item.bmi, 0);
        const avgBmi = (sumBmi / totalAssessments).toFixed(1);

        document.getElementById("dashboard-avg-glucose").innerHTML = `${avgGlucose} <span style="font-size: 1rem; font-weight: 500; color: var(--text-muted)">mg/dL</span>`;
        document.getElementById("dashboard-avg-bmi").textContent = avgBmi;

        // Dynamic Trend Indicators
        const glucoseTrend = document.getElementById("dashboard-glucose-trend");
        if (avgGlucose > 125) {
            glucoseTrend.className = "stat-trend trend-down";
            glucoseTrend.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Diabetic / Borderline`;
        } else if (avgGlucose > 100) {
            glucoseTrend.className = "stat-trend trend-warning";
            glucoseTrend.style.color = "var(--warning)";
            glucoseTrend.innerHTML = `<i class="fa-solid fa-circle-info"></i> Pre-diabetic levels`;
        } else {
            glucoseTrend.className = "stat-trend trend-up";
            glucoseTrend.innerHTML = `<i class="fa-solid fa-circle-check"></i> Healthy Range`;
        }

        const bmiTrend = document.getElementById("dashboard-bmi-trend");
        if (avgBmi > 30) {
            bmiTrend.className = "stat-trend trend-down";
            bmiTrend.innerHTML = `<i class="fa-solid fa-weight-scale"></i> Class Obese`;
        } else if (avgBmi > 25) {
            bmiTrend.className = "stat-trend trend-warning";
            bmiTrend.style.color = "var(--warning)";
            bmiTrend.innerHTML = `<i class="fa-solid fa-circle-info"></i> Overweight`;
        } else {
            bmiTrend.className = "stat-trend trend-up";
            bmiTrend.innerHTML = `<i class="fa-solid fa-circle-check"></i> Normal weight`;
        }

        // Total assessments trend
        document.getElementById("dashboard-total-trend").className = "stat-trend trend-up";
        document.getElementById("dashboard-total-trend").innerHTML = `<i class="fa-solid fa-clock-rotate-left"></i> History Logged`;

        // Render AI Insights
        generateDashboardInsights(history, avgGlucose, avgBmi);

        // Render Charts
        renderDashboardCharts(history);
        
    } catch (e) {
        console.error("Error loading dashboard data:", e);
    }
}

function generateDashboardInsights(history, avgGlucose, avgBmi) {
    const latest = history[0];
    let insightStr = "";

    if (latest.result_class === 1) {
        insightStr += `🚨 **Critical Note:** Your last assessment calculated an elevated risk outcome (${(latest.result_probability * 100).toFixed(1)}% probability). `;
    } else {
        insightStr += `💚 **Active Wellness:** Your last assessment calculated a healthy outcome (${(latest.result_probability * 100).toFixed(1)}% probability). `;
    }

    insightStr += `Your cumulative average glucose stands at **${avgGlucose} mg/dL** and your average BMI is **${avgBmi}**. `;

    if (avgGlucose > 120) {
        insightStr += `Since your glucose measurements reflect borderline/diabetic patterns, prioritizing fiber-rich nutrition, minimizing processed sugars, and tracking post-meal levels is highly recommended. `;
    } else {
        insightStr += `Keep doing what you're doing! Maintaining constant physical activity and moderate-carb intakes will continue to safeguard your insulin pathways. `;
    }

    // Convert simple markdown markers in this text for display
    document.getElementById("dashboard-insights-text").innerHTML = insightStr
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function renderDashboardCharts(history) {
    // Reverse history to show chronological timeline (left to right)
    const chronoHistory = [...history].reverse();
    
    // Limits datasets to last 10 entries for screen spacing
    const dataSlice = chronoHistory.slice(-10);
    
    const dates = dataSlice.map(item => new Date(item.created_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric'}));
    const glucoseValues = dataSlice.map(item => item.glucose);
    const bmiValues = dataSlice.map(item => item.bmi);
    
    const highRiskCount = history.filter(item => item.result_class === 1).length;
    const lowRiskCount = history.filter(item => item.result_class === 0).length;

    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    const gridColor = isDark ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)";
    const textColor = isDark ? "#94a3b8" : "#475569";

    // --- Line Chart (Glucose & BMI Trends) ---
    if (trendsChart) {
        trendsChart.destroy();
    }
    
    const ctxTrends = document.getElementById("patient-trends-chart").getContext("2d");
    trendsChart = new Chart(ctxTrends, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Glucose (mg/dL)',
                    data: glucoseValues,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y'
                },
                {
                    label: 'BMI',
                    data: bmiValues,
                    borderColor: '#14b8a6',
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    tension: 0.3,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: textColor, font: { family: 'Plus Jakarta Sans', weight: '600' } }
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: textColor }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: gridColor },
                    ticks: { color: textColor }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: textColor }
                }
            }
        }
    });

    // --- Pie Chart (Risk Distributions) ---
    if (pieChart) {
        pieChart.destroy();
    }
    
    const ctxPie = document.getElementById("patient-pie-chart").getContext("2d");
    pieChart = new Chart(ctxPie, {
        type: 'doughnut',
        data: {
            labels: ['Low Risk (Healthy)', 'High Risk (Elevated)'],
            datasets: [{
                data: [lowRiskCount, highRiskCount],
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: textColor, padding: 15, font: { family: 'Plus Jakarta Sans', weight: '600' } }
                }
            },
            cutout: '65%'
        }
    });
}

function refreshDashboardCharts(filterType) {
    // If user selects "Only High Risk", filter history and re-render
    authorizedFetch(`${API_BASE}/api/predictions/history`)
        .then(res => res.json())
        .then(history => {
            if (filterType === 'risk') {
                history = history.filter(item => item.result_class === 1);
            }
            renderDashboardCharts(history);
        });
}
