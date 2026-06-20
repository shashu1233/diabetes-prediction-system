// Risk Prediction Module

let activeRating = 0;
let lastPredictionId = null;

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("prediction-form");
    const toggleAdvanced = document.getElementById("toggle-advanced-inputs");
    const advancedContainer = document.getElementById("advanced-inputs-container");

    // Toggle advanced options panel
    toggleAdvanced.addEventListener("click", () => {
        if (advancedContainer.style.display === "none") {
            advancedContainer.style.display = "block";
            toggleAdvanced.innerHTML = `<i class="fa-solid fa-sliders"></i> Hide Advanced Parameters`;
        } else {
            advancedContainer.style.display = "none";
            toggleAdvanced.innerHTML = `<i class="fa-solid fa-sliders"></i> Show Advanced Parameters`;
        }
    });

    // Form Submit API dispatch
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const btnSubmit = document.getElementById("btn-predict-submit");
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing Diagnostics...`;

        const payload = {
            pregnancies: parseInt(document.getElementById("pred-pregnancies").value) || 0,
            glucose: parseInt(document.getElementById("pred-glucose").value),
            blood_pressure: parseInt(document.getElementById("pred-bp").value),
            skin_thickness: parseInt(document.getElementById("pred-skin").value) || 0,
            insulin: parseInt(document.getElementById("pred-insulin").value) || 0,
            bmi: parseFloat(document.getElementById("pred-bmi").value),
            pedigree_function: parseFloat(document.getElementById("pred-pedigree").value) || 0.47,
            age: parseInt(document.getElementById("pred-age").value)
        };

        try {
            const response = await authorizedFetch(`${API_BASE}/api/predictions/predict`, {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if (response && response.ok) {
                const result = await response.json();
                lastPredictionId = result.id;
                renderPredictionResult(result);
            } else {
                showToast("Failed to compile prediction metrics.", "error");
            }
        } catch (err) {
            console.error("Prediction Error:", err);
            showToast("Server connection error during prediction analysis.", "error");
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `<i class="fa-solid fa-microchip"></i> Analyze Vitals`;
        }
    });

    // Stars Rating Interaction
    const stars = document.querySelectorAll(".star");
    stars.forEach(star => {
        star.addEventListener("mouseover", () => {
            const val = parseInt(star.getAttribute("data-val"));
            highlightStars(val);
        });

        star.addEventListener("mouseout", () => {
            highlightStars(activeRating);
        });

        star.addEventListener("click", () => {
            activeRating = parseInt(star.getAttribute("data-val"));
            highlightStars(activeRating);
        });
    });

    // Submit Feedback button
    document.getElementById("btn-submit-feedback").addEventListener("click", async () => {
        if (activeRating === 0) {
            showToast("Please pick a rating score (1-5 stars).", "warning");
            return;
        }

        const comment = document.getElementById("feedback-comment").value.trim();

        try {
            const response = await authorizedFetch(`${API_BASE}/api/feedbacks`, {
                method: "POST",
                body: JSON.stringify({ rating: activeRating, comment })
            });

            if (response && response.ok) {
                showToast("Thank you for your feedback rating!", "success");
                // Reset rating inputs
                activeRating = 0;
                highlightStars(0);
                document.getElementById("feedback-comment").value = "";
            } else {
                showToast("Failed to record rating feedback.", "error");
            }
        } catch (e) {
            showToast("Server error during feedback dispatch.", "error");
        }
    });
});

function highlightStars(val) {
    const stars = document.querySelectorAll(".star");
    stars.forEach(star => {
        const starVal = parseInt(star.getAttribute("data-val"));
        if (starVal <= val) {
            star.className = "fa-solid fa-star star active";
        } else {
            star.className = "fa-regular fa-star star";
        }
    });
}

function renderPredictionResult(result) {
    // Show results containers
    document.getElementById("result-placeholder").style.display = "none";
    document.getElementById("result-active").style.display = "block";

    // Progress gauge configuration
    const prob = result.result_probability;
    const probPct = Math.round(prob * 100);
    const gauge = document.getElementById("result-gauge");
    const gaugeText = document.getElementById("result-probability-text");
    
    gaugeText.textContent = `${probPct}%`;

    // Apply color coordinates based on outcomes
    const strokeColor = Number(result.result_class) === 1 ? "var(--danger)" : "var(--success)";
    gauge.style.background = `conic-gradient(${strokeColor} ${probPct}%, rgba(255, 255, 255, 0.05) ${probPct}%)`;

    // Outcome Badge details
    const outcomeBadge = document.getElementById("result-outcome-badge");
    const descText = document.getElementById("result-description");
    
    if (Number(result.result_class) === 1) {
        outcomeBadge.textContent = "High Risk Detected";
        outcomeBadge.className = "result-status badge badge-danger";
        descText.textContent = "Your profile shows significant health risk correlation. Please review guidelines and consult a medical practitioner.";
    } else {
        outcomeBadge.textContent = "Low Risk Profile";
        outcomeBadge.className = "result-status badge badge-success";
        descText.textContent = "Your metrics fall within healthy margins. Maintain a balanced diet and regular activity levels to stay fit.";
    }

    // Set Gemini wellness suggestions (supports HTML translation)
    const geminiOutput = document.getElementById("gemini-suggestion-output");
    geminiOutput.innerHTML = parseMarkdownToHtml(result.gemini_suggestion);
}

// Basic custom markdown parser for clean presentation of LLM outputs
function parseMarkdownToHtml(markdown) {
    if (!markdown) return "<p>No recommendations available.</p>";
    
    return markdown
        .replace(/### (.*?)\n/g, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/-\s(.*?)(\n|$)/g, '<li>$1</li>')
        // Wrap adjacent li elements into ul
        .replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>')
        .replace(/<\/ul>\s*<ul>/g, '')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}
