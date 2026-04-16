/**
 * admin.js — Admin Dashboard Logic
 * Handles real-time order updates, stats, and menu management.
 */
import api from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    const adminOrdersContainer = document.getElementById('admin-orders-container');
    const adminMenuGrid = document.getElementById('admin-menu-grid');
    const categoryForm = document.getElementById('category-form');
    const subFoodForm = document.getElementById('subfood-form');
    const foodSelect = document.getElementById('food-select');

    // Stats Elements
    const totalOrdersEl = document.getElementById('total-orders');
    const pendingOrdersEl = document.getElementById('pending-orders');
    const completedOrdersEl = document.getElementById('completed-orders');
    const totalRevenueEl = document.getElementById('total-revenue');

    let allOrders = [];
    let isInitialLoad = true;

    // 1. Load Orders & Stats
    async function loadOrders() {
        try {
            const freshOrders = await api.getAdminOrders();
            allOrders = freshOrders;
            updateStats(allOrders);
            
            // Check if user is currently interacting with any status dropdown
            const activeElement = document.activeElement;
            const isInteracting = activeElement && activeElement.classList.contains('status-select');
            
            // Prevent jitter: only re-render if not interacting and not recently updated
            const isJustUpdated = window.lastUpdate && (Date.now() - window.lastUpdate < 3000);
            
            if (isInitialLoad || (!isInteracting && !isJustUpdated)) {
                renderOrders(allOrders);
                isInitialLoad = false;
            }
        } catch (error) {
            console.error('Failed to load orders:', error);
            if (error.isAuthError) {
                // api.js handles redirect, but we stop execution here
                return;
            }
            if (error.isPermissionError) {
                alert('Access Denied: You do not have admin privileges.');
                window.location.href = 'home.html';
                return;
            }
        }
    }

    function updateStats(orders) {
        if (!totalOrdersEl) return;
        totalOrdersEl.textContent = orders.length;
        pendingOrdersEl.textContent = orders.filter(o => o.orderStatus === 'PENDING').length;
        completedOrdersEl.textContent = orders.filter(o => o.orderStatus === 'COMPLETED').length;

        const revenue = orders.reduce((sum, o) => sum + (o.totalPrice || 0), 0);
        totalRevenueEl.textContent = `Rs.${revenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
    }

    function renderOrders(orders) {
        if (!adminOrdersContainer) return;
        
        // Save current scroll position if list is long
        const scrollPos = window.scrollY;
        
        adminOrdersContainer.innerHTML = '';

        if (orders.length === 0) {
            adminOrdersContainer.innerHTML = '<p style="text-align: center; color: var(--text-gray); padding: 50px;">No orders found.</p>';
            return;
        }

        // Sort by ID descending (newest first)
        const sortedOrders = [...orders].sort((a, b) => b.id - a.id);
        
        sortedOrders.forEach(order => {
            const card = document.createElement('div');
            card.className = 'admin-order-card';

            const orderTime = new Date(order.orderTime || Date.now()).toLocaleString();
            const status = order.orderStatus || 'PENDING';

            card.innerHTML = `
                <div class="order-row-header">
                    <div class="cust-info">
                        <h3>#ORD-${order.id}</h3>
                        <p><i class="fa-regular fa-user"></i> ${order.userName || 'Guest'} | <i class="fa-regular fa-clock"></i> ${orderTime}</p>
                    </div>
                    <div class="order-actions">
                        <span style="font-weight: 700; color: var(--primary-pink); font-size: 18px;">Rs.${(order.totalPrice || 0).toFixed(2)}</span>
                        <div class="status-select-wrapper">
                            <select class="status-select" data-id="${order.id}">
                                <option value="PENDING" ${status === 'PENDING' ? 'selected' : ''}>Pending</option>
                                <option value="ACCEPTED" ${status === 'ACCEPTED' ? 'selected' : ''}>Accepted</option>
                                <option value="PREPARING" ${status === 'PREPARING' ? 'selected' : ''}>Preparing</option>
                                <option value="READY" ${status === 'READY' ? 'selected' : ''}>Ready</option>
                                <option value="COMPLETED" ${status === 'COMPLETED' ? 'selected' : ''}>Completed</option>
                            </select>
                        </div>
                        <button class="btn-primary update-btn" data-id="${order.id}" style="padding: 10px 20px; font-size: 14px;">Update</button>
                    </div>
                </div>
                <div class="order-items-minimal" style="color: var(--text-gray); font-size: 14px; margin-top: 10px;">
                    ${(order.orderItems || []).map(i => `<span style="background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 8px; margin-right: 8px; display: inline-block; margin-bottom: 5px;">${i.quantity}x ${i.foodName}</span>`).join('')}
                </div>
            `;
            adminOrdersContainer.appendChild(card);
        });

        // Add event listeners to newly rendered buttons
        adminOrdersContainer.querySelectorAll('.update-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.currentTarget.dataset.id;
                const statusSelect = adminOrdersContainer.querySelector(`.status-select[data-id="${id}"]`);
                const status = statusSelect.value;
                
                try {
                    btn.disabled = true;
                    const originalText = btn.textContent;
                    btn.textContent = 'Updating...';
                    
                    await api.updateOrderStatus(id, status);
                    
                    // Immediately update local data for "Instant" feel
                    const updatedOrder = allOrders.find(o => o.id == id);
                    if (updatedOrder) {
                        updatedOrder.orderStatus = status;
                        updateStats(allOrders);
                    }
                    
                    btn.textContent = 'Updated!';
                    btn.style.background = '#2ecc71';
                    window.lastUpdate = Date.now();
                    
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = 'Update';
                        btn.style.background = '';
                    }, 2000);
                } catch (error) {
                    btn.disabled = false;
                    btn.textContent = 'Update';
                    btn.style.background = '';
                    
                    if (error.isAuthError) return; // Handled by api.js
                    
                    alert('Status update failed: ' + error.message);
                }
            });
        });
    }

    // 2. Load Categories & Menu Grid
    async function loadMenu() {
        try {
            const categories = await api.getMenu();
            renderCategorySelect(categories);
            renderMenuGrid(categories);
        } catch (error) {
            console.error('Failed to load menu:', error);
        }
    }

    function renderCategorySelect(categories) {
        if (!foodSelect) return;
        const currentVal = foodSelect.value;
        foodSelect.innerHTML = '<option value="">Select Category</option>';
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat.id;
            opt.textContent = cat.foodName;
            foodSelect.appendChild(opt);
        });
        if (currentVal) foodSelect.value = currentVal;
    }

    function renderMenuGrid(categories) {
        if (!adminMenuGrid) return;
        adminMenuGrid.innerHTML = '';

        categories.forEach(cat => {
            // Category Header
            const catHeader = document.createElement('div');
            catHeader.style = 'grid-column: 1 / -1; margin-top: 30px; margin-bottom: 10px; display: flex; align-items: center; gap: 10px;';
            catHeader.innerHTML = `<h3 style="color: var(--primary-pink)">${cat.foodName}</h3> <span style="font-size: 12px; color: var(--text-gray);">(${cat.foodSubCat?.length || 0} items)</span>`;
            adminMenuGrid.appendChild(catHeader);

            if (cat.foodSubCat) {
                cat.foodSubCat.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'mgmt-food-card';
                    card.innerHTML = `
                        <img src="${item.imgUrl || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=200'}" class="mgmt-food-img" alt="${item.foodName}">
                        <div class="mgmt-food-info">
                            <h4>${item.foodName}</h4>
                            <span class="mgmt-food-price">Rs.${(item.price || 0).toFixed(2)}</span>
                        </div>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <button class="edit-item-btn" data-id="${item.id}" title="Edit Item" style="background: none; border: none; color: var(--text-gray); cursor: pointer; font-size: 16px;">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <label class="toggle-switch">
                                <input type="checkbox" class="avail-toggle" data-id="${item.id}" ${item.isAvailable ? 'checked' : ''}>
                                <span class="slider"></span>
                            </label>
                        </div>
                    `;
                    adminMenuGrid.appendChild(card);
                });
            }
        });

        // Add event listeners for edit buttons
        document.querySelectorAll('.edit-item-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                startEditItem(id);
            });
        });

        // Add event listeners for availability toggles
        document.querySelectorAll('.avail-toggle').forEach(chk => {
            chk.addEventListener('change', async () => {
                const id = chk.dataset.id;
                const originalState = chk.checked;
                try {
                    await api.updateSubFoodAvailability(id, originalState);
                } catch (e) {
                    if (e.isAuthError) return;
                    alert('Failed to update availability');
                    chk.checked = !originalState;
                }
            });
        });
    }

    function startEditItem(id) {
        api.getMenu().then(categories => {
            let itemToEdit = null;
            let catId = null;
            
            categories.forEach(cat => {
                const found = cat.foodSubCat?.find(i => i.id == id);
                if (found) {
                    itemToEdit = found;
                    catId = cat.id;
                }
            });

            if (itemToEdit) {
                document.getElementById('edit-item-id').value = itemToEdit.id;
                document.getElementById('food-select').value = catId;
                document.getElementById('sub-name').value = itemToEdit.foodName;
                document.getElementById('sub-price').value = itemToEdit.price;
                document.getElementById('sub-type').value = itemToEdit.vegOrNonVeg || 'Veg';
                document.getElementById('sub-img').value = itemToEdit.imgUrl || '';
                document.getElementById('sub-desc').value = itemToEdit.description || '';

                document.getElementById('form-mode-title').innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Edit Food Item';
                document.getElementById('subfood-submit-btn').textContent = 'Update Item';
                document.getElementById('cancel-edit-btn').style.display = 'block';

                document.querySelector('.mgmt-form-card').scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', () => {
            resetSubFoodForm();
        });
    }

    function resetSubFoodForm() {
        if (subFoodForm) subFoodForm.reset();
        document.getElementById('edit-item-id').value = '';
        document.getElementById('form-mode-title').innerHTML = '<i class="fa-solid fa-plate-wheat"></i> Add Food Item';
        document.getElementById('subfood-submit-btn').textContent = 'Add to Menu';
        document.getElementById('cancel-edit-btn').style.display = 'none';
    }

    // 3. Handle Add Category
    if (categoryForm) {
        categoryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const foodName = document.getElementById('cat-name').value;
            const btn = categoryForm.querySelector('button');
            try {
                btn.disabled = true;
                btn.textContent = 'Processing...';
                await api.addFood({ foodName, isAvailable: true });
                categoryForm.reset();
                loadMenu();
                // Success indicator instead of annoying alert if possible, but alert is fine for now
            } catch (error) {
                if (!error.isAuthError) alert('Failed to add category: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Create Category';
            }
        });
    }

    // 4. Handle Add/Update SubFood
    if (subFoodForm) {
        subFoodForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const editId = document.getElementById('edit-item-id').value;
            const btn = subFoodForm.querySelector('button[type="submit"]');
            
            const subFoodData = {
                foodName: document.getElementById('sub-name').value,
                description: document.getElementById('sub-desc').value,
                price: parseFloat(document.getElementById('sub-price').value),
                imgUrl: document.getElementById('sub-img').value,
                isAvailable: true,
                vegOrNonVeg: document.getElementById('sub-type').value,
                food: { id: parseInt(foodSelect.value) }
            };

            try {
                btn.disabled = true;
                btn.textContent = 'Processing...';
                
                if (editId) {
                    await api.updateSubFood(editId, subFoodData);
                    resetSubFoodForm();
                } else {
                    await api.addSubFood(subFoodData);
                    subFoodForm.reset();
                }
                
                loadMenu();
            } catch (error) {
                if (!error.isAuthError) alert('Operation failed: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = editId ? 'Update Item' : 'Add to Menu';
            }
        });
    }

    // Initial load
    await loadOrders();
    await loadMenu();

    // High-frequency polling for real-time feel (3.5 seconds to avoid sync issues)
    setInterval(loadOrders, 3500);
});
