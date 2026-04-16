import api from './js/api.js';
import cart from './js/cart.js';

document.addEventListener('DOMContentLoaded', async () => {
    // Login enforcement
    const token = sessionStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const popularGrid = document.getElementById('popular-grid');
    const viewAllBtn = document.querySelector('.btn-view-all');
    // Handle Navbar state
    api.setupNavbar();

    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', () => {
            window.location.href = 'menu.html';
        });
    }

    async function loadPopularItems() {
        if (!popularGrid) return;
        try {
            const menu = await api.getMenu();
            // Flatten the menu to get sub-items
            let allItems = [];
            menu.forEach(category => {
                // Check if the category itself is available
                if (category.isAvailable && category.foodSubCat) {
                    category.foodSubCat.forEach(item => {
                        // Check if the individual item is available
                        if (item.isAvailable) {
                            allItems.push({
                                ...item,
                                categoryName: category.foodName
                            });
                        }
                    });
                }
            });

            // Take first 4 items as "popular" or filter based on criteria
            const popularItems = allItems.slice(0, 4);
            renderItems(popularItems);
        } catch (error) {
            console.error('Failed to load popular items:', error);
            popularGrid.innerHTML = '<p>Something went wrong. Please check back later.</p>';
        }
    }

    function renderItems(items) {
        popularGrid.innerHTML = '';
        items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'food-card';
            card.innerHTML = `
                <div class="card-img">
                    <span class="tag-left">${item.categoryName || 'FOOD'}</span>
                    ${item.isHot ? '<span class="tag-right">HOT</span>' : ''}
                    <img src="${item.imgUrl || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=500'}" alt="${item.foodName}">
                </div>
                <div class="card-body">
                    <div class="card-title-row">
                        <h3>${item.foodName}</h3>
                        <span class="card-rating">★ 4.8</span>
                    </div>
                    <p>${item.description || 'Delicate prepared dish.'}</p>
                    <div class="card-footer">
                        <span class="price">Rs.${item.price.toFixed(2)}</span>
                        <button class="add-btn" data-id="${item.id}"><i class="fa-solid fa-plus"></i></button>
                    </div>
                </div>
            `;

            card.querySelector('.add-btn').addEventListener('click', () => {
                cart.addItem(item);
                alert(`${item.foodName} added to cart!`);
            });

            popularGrid.appendChild(card);
        });
    }

    loadPopularItems();
});