/**
 * api.js  —  Frontend API layer (Session Isolation Version)
 * 
 * Uses sessionStorage instead of localStorage to allow side-by-side 
 * testing of different accounts (e.g. User and Admin) in different tabs.
 */

const BASE_URL = ''; 
const AUTH_ERRORS = ['TOKEN_EXPIRED', 'INVALID_TOKEN', 'MISSING_TOKEN', 'REVOKED_TOKEN'];
let isRedirecting = false;

// ── helpers ──────────────────────────────────────────────────────────────────

function getHeaders(isJson = true) {
    // Switch to sessionStorage for tab-level isolation
    const token = sessionStorage.getItem('token');
    const h = {};
    if (isJson) h['Content-Type'] = 'application/json';
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
}

function handleAuthFailure(message) {
    if (isRedirecting) return;
    isRedirecting = true;
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('username');
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 100);
}

async function handleResponse(res, skipAuthRedirect = false) {
    const text = await res.text();
    if (!res.ok) {
        let errorCode = null;
        let msg = text || `HTTP ${res.status}`;
        try {
            const json = JSON.parse(text);
            errorCode = json.error || null;
            msg = json.message || json.error || json.msg || msg;
        } catch (_) { }

        if (res.status === 401 && !skipAuthRedirect) {
            handleAuthFailure(msg);
            const err = new Error(msg);
            err.isAuthError = true;
            throw err;
        }

        if (res.status === 403) {
            const err = new Error(msg);
            err.isPermissionError = true;
            throw err;
        }

        throw new Error(msg);
    }
    try { return JSON.parse(text); } catch (_) { return text; }
}

// ── API Object ────────────────────────────────────────────────────────────────

const api = {

    async login(username, password) {
        const res = await fetch(`${BASE_URL}/public/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userName: username, password })
        });
        if (!res.ok) {
            const msg = await res.text();
            throw new Error(msg || 'Invalid username or password');
        }
        const token = await res.text();
        
        // Use sessionStorage for tab isolation
        sessionStorage.setItem('token', token);
        sessionStorage.setItem('username', username);
        
        isRedirecting = false; 
        return token;
    },

    async signup(userData) {
        const res = await fetch(`${BASE_URL}/public/signUp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        if (!res.ok) {
            const msg = await res.text();
            throw new Error(msg || 'Signup failed');
        }
        return await res.text();
    },

    logout() {
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('username');
        window.location.href = 'login.html';
    },

    async verifyToken() {
        const token = sessionStorage.getItem('token');
        if (!token) return null;
        try {
            const res = await fetch(`${BASE_URL}/api/auth/verify`, {
                headers: getHeaders()
            });
            return await handleResponse(res, true);
        } catch (_) {
            return null;
        }
    },

    async refreshToken() {
        const res = await fetch(`${BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (!res.ok) return false;
        const newToken = await res.text();
        sessionStorage.setItem('token', newToken);
        return true;
    },

    isLoggedIn() {
        return !!sessionStorage.getItem('token');
    },

    // ── USER PROFILE ──────────────────────────────────────────────────────────

    async getUserProfile(usernameParam) {
        const username = usernameParam || sessionStorage.getItem('username');
        if (!username) throw new Error('No user logged in');

        const res = await fetch(`${BASE_URL}/api/users/${username}`, {
            headers: getHeaders()
        });
        return handleResponse(res);
    },

    // ── MENU ──────────────────────────────────────────────────────────────────

    async getMenu() {
        const res = await fetch(`${BASE_URL}/Food/food`, {
            headers: getHeaders()
        });
        return handleResponse(res);
    },

    async addFood(foodData) {
        const res = await fetch(`${BASE_URL}/Food/food`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(foodData)
        });
        return handleResponse(res);
    },

    async addSubFood(subFoodData) {
        const res = await fetch(`${BASE_URL}/Food/subfood`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(subFoodData)
        });
        return handleResponse(res);
    },

    async updateFoodAvailability(foodId, available) {
        const res = await fetch(`${BASE_URL}/Food/id/${foodId}/${available}`, {
            method: 'PATCH',
            headers: getHeaders()
        });
        return handleResponse(res);
    },

    async updateSubFoodAvailability(subId, available) {
        const res = await fetch(`${BASE_URL}/Food/subfood/id/${subId}/${available}`, {
            method: 'PATCH',
            headers: getHeaders()
        });
        return handleResponse(res);
    },

    async updateSubFood(subId, foodData) {
        const res = await fetch(`${BASE_URL}/Food/subfood/id/${subId}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(foodData)
        });
        return handleResponse(res);
    },

    // ── ORDERS ────────────────────────────────────────────────────────────────

    async placeOrder(orderData) {
        const res = await fetch(`${BASE_URL}/Order`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(orderData)
        });
        return handleResponse(res);
    },

    async getUserOrders() {
        const res = await fetch(`${BASE_URL}/Order/getUserAll`, {
            headers: getHeaders()
        });
        return handleResponse(res);
    },

    async getAdminOrders() {
        const res = await fetch(`${BASE_URL}/Order/getAll`, {
            headers: getHeaders()
        });
        return handleResponse(res);
    },

    async updateOrderStatus(orderId, status) {
        const res = await fetch(`${BASE_URL}/Order/id/${orderId}/${status}`, {
            method: 'PATCH',
            headers: getHeaders()
        });
        return handleResponse(res);
    },

    setupNavbar() {
        const token = sessionStorage.getItem('token');
        const authBtn = document.getElementById('nav-auth-btn');
        const logoutBtn = document.getElementById('nav-logout-btn');

        if (token && authBtn && logoutBtn) {
            authBtn.textContent = 'Profile';
            authBtn.onclick = () => window.location.href = 'profile.html';
            logoutBtn.style.display = 'block';
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        } else if (!token && authBtn) {
            authBtn.textContent = 'Sign Up';
            authBtn.onclick = () => window.location.href = 'signup.html';
            if (logoutBtn) logoutBtn.style.display = 'none';
        }
    }
};

export default api;
