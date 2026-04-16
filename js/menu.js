import api from './api.js';
import cart from './cart.js';

document.addEventListener('DOMContentLoaded', async () => {
    // Login enforcement
    const token = sessionStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    api.setupNavbar();

    const categoryList = document.getElementById('category-list');
    const foodGrid = document.getElementById('menu-food-grid');
    const menuTitle = document.getElementById('menu-title');
    const menuCount = document.getElementById('menu-count');
    const searchInput = document.querySelector('.search-container input');

    let allFoodData = [];
    let currentCategory = 'all';

    async function loadMenu() {
        try {
            allFoodData = await api.getMenu();
            renderCategories(allFoodData);
            renderItems('all');
        } catch (error) {
            console.error('Failed to load menu:', error);
            foodGrid.innerHTML = '<p>Failed to load menu. Please try again later.</p>';
        }
    }

    function renderCategories(categories) {
        categoryList.innerHTML = `
            <div class="cat-item active" data-id="all">
                <div class="cat-icon">🍴</div>
                <div class="cat-info">
                    <span class="cat-name">All Items</span>
                    <span class="cat-count">Everything</span>
                </div>
                <i class="fa-solid fa-chevron-right"></i>
            </div>
        `;

        categories.forEach(cat => {
            if (!cat.isAvailable) return;
            
            const itemCount = cat.foodSubCat ? cat.foodSubCat.filter(i => i.isAvailable).length : 0;
            const div = document.createElement('div');
            div.className = 'cat-item';
            div.dataset.id = cat.id;
            div.innerHTML = `
                <div class="cat-icon">${getIconForCategory(cat.foodName)}</div>
                <div class="cat-info">
                    <span class="cat-name">${cat.foodName}</span>
                    <span class="cat-count">${itemCount} options</span>
                </div>
                <i class="fa-solid fa-chevron-right"></i>
            `;
            categoryList.appendChild(div);
        });

        // Add click listeners
        document.querySelectorAll('.cat-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.cat-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                currentCategory = item.dataset.id;
                renderItems(currentCategory);
            });
        });
    }

    function renderItems(categoryId, searchTerm = '') {
        foodGrid.innerHTML = '';
        let itemsToDisplay = [];

        if (categoryId === 'all') {
            allFoodData.forEach(cat => {
                // Category availability check
                if (cat.isAvailable && cat.foodSubCat) {
                    cat.foodSubCat.forEach(item => {
                        // Item availability check
                        if (item.isAvailable) {
                            itemsToDisplay.push({ ...item, categoryName: cat.foodName });
                        }
                    });
                }
            });
            menuTitle.textContent = 'All Specialties';
        } else {
            const category = allFoodData.find(c => c.id == categoryId);
            if (category && category.isAvailable && category.foodSubCat) {
                itemsToDisplay = category.foodSubCat
                    .filter(item => item.isAvailable)
                    .map(item => ({ ...item, categoryName: category.foodName }));
                menuTitle.textContent = category.foodName;
            }
        }

        if (searchTerm) {
            itemsToDisplay = itemsToDisplay.filter(item =>
                item.foodName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                item.description?.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        menuCount.textContent = `Found ${itemsToDisplay.length} delicacies`;

        itemsToDisplay.forEach(item => {
            const card = document.createElement('div');
            card.className = 'food-card';
            card.innerHTML = `
                <div class="card-img">
                    <span class="tag-left">${item.categoryName}</span>
                    <img src="${item.imgUrl || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=500'}" alt="${item.foodName}">
                </div>
                <div class="card-body">
                    <div class="card-header">
                        <h3>${item.foodName}</h3>
                        <span class="rating">★ 4.8</span>
                    </div>
                    <p>${item.description || 'No description available.'}</p>
                    <div class="card-footer">
                        <span class="price">Rs.${item.price.toFixed(2)}</span>
                        <button class="add-btn"><i class="fa-solid fa-plus"></i></button>
                    </div>
                </div>
            `;

            card.querySelector('.add-btn').addEventListener('click', () => {
                cart.addItem(item);
                alert(`${item.foodName} added to cart!`);
            });

            foodGrid.appendChild(card);
        });
    }

    function getIconForCategory(name) {
        const lower = name.toLowerCase();
        if (lower.includes('pizza')) return '🍕';
        if (lower.includes('burger')) return '🍔';
        if (lower.includes('momo')) return '🥟';
        if (lower.includes('biryani') || lower.includes('rice')) return '🍚';
        if (lower.includes('roll')) return '🌯';
        if (lower.includes('chinese')) return '🥢';
        if (lower.includes('dessert') || lower.includes('sweet')) return '🍰';
        return '🍲';
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            renderItems(currentCategory, e.target.value);
        });
    }

    loadMenu();
});
