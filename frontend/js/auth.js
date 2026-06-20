// Authentication Controller Module

const API_BASE = window.location.origin;

// Helper to check authentication state
function getAuthToken() {
    return localStorage.getItem("dia_token");
}

function setAuthToken(token) {
    if (token) {
        localStorage.setItem("dia_token", token);
    } else {
        localStorage.removeItem("dia_token");
    }
}

// Fetch helper with Authorization header pre-applied
async function authorizedFetch(url, options = {}) {
    const token = getAuthToken();
    if (!token) {
        showToast("Session expired or missing. Please sign in.", "error");
        logoutUser();
        return null;
    }

    const headers = {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    try {
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            showToast("Invalid authorization. Please re-authenticate.", "error");
            logoutUser();
            return null;
        }
        return response;
    } catch (err) {
        console.error("Network error on authorized request:", err);
        showToast("Server connection error.", "error");
        return null;
    }
}

// Handles user profile retrieval
async function checkAuthStatus() {
    const token = getAuthToken();
    if (!token) {
        showAuthScreen();
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (response.ok) {
            const userData = await response.json();
            loginUserSuccess(userData);
        } else {
            setAuthToken(null);
            showAuthScreen();
        }
    } catch (e) {
        console.error("Error verifying authentication token:", e);
        setAuthToken(null);
        showAuthScreen();
    }
}

// UI updates on successful authentication
function loginUserSuccess(user) {
    document.getElementById("auth-page").style.display = "none";
    document.getElementById("app-portal").style.display = "flex";
    
    // Update User Badges in Sidebar
    const avatar = document.getElementById("user-avatar");
    avatar.textContent = user.username.substring(0, 2).toUpperCase();
    document.getElementById("user-display-name").textContent = user.username;
    document.getElementById("user-display-role").textContent = user.role;
    
    // Handle admin panel navigation item visibility
    const adminNavItem = document.getElementById("admin-nav-item");
    if (user.role === "admin") {
        adminNavItem.style.display = "block";
    } else {
        adminNavItem.style.display = "none";
    }

    // Set greeting context
    showToast(`Logged in as ${user.username}`, "success");
    
    // Default: switch to dashboard view and load statistics
    switchView("dashboard");
}

function showAuthScreen() {
    document.getElementById("app-portal").style.display = "none";
    document.getElementById("auth-page").style.display = "flex";
}

function logoutUser() {
    setAuthToken(null);
    showAuthScreen();
    showToast("Signed out successfully.", "success");
}

// Toast alerts mechanism
function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconClass = "fa-circle-check";
    if (type === "error") iconClass = "fa-circle-exclamation";
    if (type === "warning") iconClass = "fa-triangle-exclamation";

    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Fade and remove
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(50px)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Wire forms
document.addEventListener("DOMContentLoaded", () => {
    // Navigate between Auth states
    document.getElementById("go-to-signup").addEventListener("click", () => {
        document.getElementById("login-form-container").style.display = "none";
        document.getElementById("signup-form-container").style.display = "block";
    });

    document.getElementById("go-to-login").addEventListener("click", () => {
        document.getElementById("signup-form-container").style.display = "none";
        document.getElementById("login-form-container").style.display = "block";
    });

    // Login Form Submit handler
    document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("login-username").value.trim();
        const password = document.getElementById("login-password").value;

        try {
            const response = await fetch(`${API_BASE}/api/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password, email: "user@example.com" }) // API matches credentials schema
            });

            const data = await response.json();
            if (response.ok) {
                setAuthToken(data.access_token);
                checkAuthStatus();
            } else {
                showToast(data.detail || "Authentication failed. Try again.", "error");
            }
        } catch (err) {
            console.error("Login Error:", err);
            showToast("Failed to connect to authentication server.", "error");
        }
    });

    // Registration Form Submit handler
    document.getElementById("signup-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("signup-username").value.trim();
        const email = document.getElementById("signup-email").value.trim();
        const password = document.getElementById("signup-password").value;
        const role = document.getElementById("signup-role").value;

        try {
            const response = await fetch(`${API_BASE}/api/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, password, role })
            });

            const data = await response.json();
            if (response.ok) {
                showToast("Registration successful! Proceed to Sign In.", "success");
                document.getElementById("signup-form-container").style.display = "none";
                document.getElementById("login-form-container").style.display = "block";
            } else {
                showToast(data.detail || "Registration failed. Try again.", "error");
            }
        } catch (err) {
            console.error("Signup Error:", err);
            showToast("Server connection error.", "error");
        }
    });

    // Sign out button
    document.getElementById("btn-logout").addEventListener("click", (e) => {
        e.preventDefault();
        logoutUser();
    });
});
