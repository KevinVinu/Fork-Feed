import api from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    // Login enforcement
    const token = sessionStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    api.setupNavbar();

    const ordersList = document.querySelector('.orders-list');
    const refreshInterval = 3000; // 3 seconds

    async function loadOrders() {
        try {
            const orders = await api.getUserOrders();
            renderOrders(orders);
        } catch (error) {
            console.error('Failed to load orders:', error);
            if (ordersList) {
                ordersList.innerHTML = `<p class="error-msg">Failed to load orders. Please login to see your history.</p>`;
            }
        }
    }

    function renderOrders(orders) {
        if (!ordersList) return;

        ordersList.innerHTML = '';
        if (orders.length === 0) {
            ordersList.innerHTML = '<p class="no-results">You haven\'t placed any orders yet.</p>';
            return;
        }

        orders.forEach(order => {
            const card = document.createElement('div');
            card.className = 'order-card';

            const statusClass = `status-${order.orderStatus.toLowerCase()}`;
            const orderTime = new Date(order.orderTime || Date.now()).toLocaleString();

            card.innerHTML = `
                <div class="order-card-header">
                    <div class="order-id-section">
                        <h2>#ORD-${order.id}</h2>
                        <div class="order-meta">
                            <i class="fa-regular fa-clock"></i>
                            <span>${orderTime}</span>
                        </div>
                    </div>
                    <div class="status-badge ${statusClass}">
                        <i class="fa-solid ${getStatusIcon(order.orderStatus)}"></i> ${order.orderStatus}
                    </div>
                </div>
                
                <div class="order-items">
                    ${order.orderItems.map(item => `
                        <div class="item-row">
                            <span class="item-name">${item.quantity}x ${item.foodName || 'Item'}</span>
                            <span class="item-price">Rs.${(item.price * item.quantity).toFixed(2)}</span>
                        </div>
                    `).join('')}
                </div>

                <div class="order-footer">
                    <span class="total-label">Total</span>
                    <span class="total-amount">Rs.${order.totalPrice.toFixed(2)}</span>
                </div>
            `;

            ordersList.appendChild(card);
        });
    }

    function getStatusIcon(status) {
        const icons = {
            'PENDING': 'fa-clock',
            'ACCEPTED': 'fa-check',
            'PREPARING': 'fa-fire-burner',
            'READY': 'fa-bell',
            'COMPLETED': 'fa-circle-check'
        };
        return icons[status] || 'fa-info-circle';
    }

    // Initial load
    loadOrders();

    // Auto refresh every 3 seconds for real-time feel
    setInterval(loadOrders, 3000);
});
