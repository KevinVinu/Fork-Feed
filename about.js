import api from './js/api.js';

document.addEventListener('DOMContentLoaded', () => {
    api.setupNavbar();
    
    const counters = document.querySelectorAll('.counter');
    const speed = 1000;

    const animateCounters = () => {
        counters.forEach(counter => {
            const updateCount = () => {
                const target = +counter.getAttribute('data-target');
                const count = +counter.innerText;
                const inc = target / speed;

                if (count < target) {
                    counter.innerText = Math.ceil(count + inc);
                    setTimeout(updateCount, 1);
                } else {
                    counter.innerText = target + "+";
                }
            };
            updateCount();
        });
    };

    // Trigger animation when section is in view
    const observer = new IntersectionObserver((entries) => {
        if(entries[0].isIntersecting){
            animateCounters();
            observer.disconnect();
        }
    }, { threshold: 0.5 });

    if(counters.length > 0) {
        observer.observe(document.querySelector('.about-stats'));
    }
});