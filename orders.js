// Add this to your existing script.js
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.order-card');
    
    // Simple entry animation for order cards
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index);
    });
});