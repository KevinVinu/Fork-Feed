import api from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    // Login enforcement
    const token = sessionStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    api.setupNavbar();

    const profileContainer = document.querySelector('.profile-details');
    const orderHistorySummary = document.querySelector('.order-summary-grid');

    async function loadProfile() {
        try {
            const user = await api.getUserProfile();
            renderProfile(user);
            loadOrderHistorySummary();
        } catch (error) {
            console.error('Failed to load profile:', error);
            if (profileContainer) {
                profileContainer.innerHTML = `<p class="error-msg">Please login to view your profile.</p>`;
            }
        }
    }

    function renderProfile(user) {
        if (!profileContainer) return;

        profileContainer.innerHTML = `
            <div class="profile-field">
                <label>Full Name</label>
                <p>${user.firstName} ${user.lastName || ''}</p>
            </div>
            <div class="profile-field">
                <label>Email Address</label>
                <p>${user.email || 'N/A'}</p>
            </div>
            <div class="profile-field">
                <label>Phone Number</label>
                <p>${user.phone || 'N/A'}</p>
            </div>
            <div class="profile-field">
                <label>Username</label>
                <p>@${user.userName}</p>
            </div>
            <div class="profile-field">
                <label>Member Since</label>
                <p>${new Date(user.createAt).toLocaleDateString()}</p>
            </div>
        `;
    }

    async function loadOrderHistorySummary() {
        if (!orderHistorySummary) return;

        try {
            const orders = await api.getUserOrders();
            const stats = {
                total: orders.length,
                completed: orders.filter(o => o.orderStatus === 'COMPLETED').length,
                pending: orders.filter(o => o.orderStatus !== 'COMPLETED').length
            };

            orderHistorySummary.innerHTML = `
                <div class="stat-card">
                    <h3>${stats.total}</h3>
                    <p>Total Orders</p>
                </div>
                <div class="stat-card">
                    <h3>${stats.completed}</h3>
                    <p>Delivered</p>
                </div>
                <div class="stat-card">
                    <h3>${stats.pending}</h3>
                    <p>Active Orders</p>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load order stats:', error);
        }
    }

    loadProfile();
});
