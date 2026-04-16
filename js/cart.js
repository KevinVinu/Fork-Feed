const CART_KEY = 'food_square_cart';

const cart = {
    // Switch to sessionStorage for full isolation between tabs
    items: JSON.parse(sessionStorage.getItem(CART_KEY)) || [],

    addItem(food) {
        const token = sessionStorage.getItem('token');
        if (!token) {
            alert('Your plate is waiting! Please login first to start adding delicacies.');
            window.location.href = 'login.html';
            return;
        }

        const existingItem = this.items.find(item => item.id === food.id);
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.items.push({
                id: food.id,
                name: food.foodName,
                price: food.price,
                image: food.imgUrl, // Using backend imgUrl field
                quantity: 1
            });
        }
        this.save();
        this.updateUI();
    },

    removeItem(foodId) {
        this.items = this.items.filter(item => item.id !== foodId);
        this.save();
        this.updateUI();
    },

    updateQuantity(foodId, delta) {
        const item = this.items.find(item => item.id === foodId);
        if (item) {
            item.quantity += delta;
            if (item.quantity <= 0) {
                this.removeItem(foodId);
            } else {
                this.save();
                this.updateUI();
            }
        }
    },

    getTotal() {
        return this.items.reduce((total, item) => total + (item.price * item.quantity), 0);
    },

    clear() {
        this.items = [];
        this.save();
        this.updateUI();
    },

    save() {
        sessionStorage.setItem(CART_KEY, JSON.stringify(this.items));
    },

    updateUI() {
        // Update cart count in nav
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            const totalItems = this.items.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.textContent = totalItems;
        }

        // Emit custom event for pages that need to refresh cart view
        window.dispatchEvent(new CustomEvent('cartUpdated', { detail: this.items }));
    }
};

// Initialize UI
cart.updateUI();

export default cart;
