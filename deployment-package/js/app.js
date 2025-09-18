// Modern Drop Shipping Site - JavaScript
class NLEBikeApp {
    constructor() {
        this.products = [];
        this.cart = JSON.parse(localStorage.getItem('cart')) || [];
        this.currentFilter = 'all';
        this.theme = localStorage.getItem('theme') || 'light';
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProducts();
        this.updateCartCount();
        this.applyTheme();
        this.startInventorySync();
    }

    setupEventListeners() {
        // Theme toggle
        document.querySelector('.theme-toggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        // Mobile menu toggle
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        const mobileMenu = document.querySelector('.mobile-menu');
        
        mobileMenuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('active');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenu.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                mobileMenu.classList.remove('active');
            }
        });

        // Mobile dropdown functionality
        document.querySelectorAll('.mobile-dropdown-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                const dropdown = toggle.closest('.mobile-dropdown');
                const isActive = dropdown.classList.contains('active');
                
                // Close all other dropdowns
                document.querySelectorAll('.mobile-dropdown').forEach(d => {
                    d.classList.remove('active');
                });
                
                // Toggle current dropdown
                if (!isActive) {
                    dropdown.classList.add('active');
                }
            });
        });

        // Desktop mega menu accessibility (keyboard navigation)
        document.querySelectorAll('.mega-menu-item, .dropdown-item').forEach(item => {
            const link = item.querySelector('.nav-link');
            const menu = item.querySelector('.mega-menu, .dropdown-menu');
            
            if (link && menu) {
                link.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        menu.style.opacity = menu.style.opacity === '1' ? '0' : '1';
                        menu.style.visibility = menu.style.visibility === 'visible' ? 'hidden' : 'visible';
                    }
                });
                
                // Close menu when clicking outside
                document.addEventListener('click', (e) => {
                    if (!item.contains(e.target)) {
                        menu.style.opacity = '0';
                        menu.style.visibility = 'hidden';
                    }
                });
            }
        });

        // Product filters
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.filterProducts(e.target.dataset.filter);
            });
        });

        // Search functionality
        const searchInput = document.querySelector('.search-input');
        const searchBtn = document.querySelector('.search-btn');
        
        searchInput.addEventListener('input', (e) => {
            this.searchProducts(e.target.value);
        });
        
        searchBtn.addEventListener('click', () => {
            this.searchProducts(searchInput.value);
        });

        // Newsletter form
        document.querySelector('.newsletter-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleNewsletterSignup(e);
        });

        // Close promo banner
        document.querySelector('.close-banner').addEventListener('click', () => {
            document.querySelector('.header-top').style.display = 'none';
        });

        // Modal functionality
        document.querySelector('.close-modal').addEventListener('click', () => {
            this.closeModal();
        });

        // Load more products
        document.querySelector('.load-more-btn').addEventListener('click', () => {
            this.loadMoreProducts();
        });
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        localStorage.setItem('theme', this.theme);
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        const themeIcon = document.querySelector('.theme-toggle i');
        themeIcon.className = this.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }

    async loadProducts() {
        this.showLoading(true);
        
        try {
            // Load products from local data or API
            this.products = await this.fetchProducts();
            this.renderProducts(this.products);
        } catch (error) {
            console.error('Error loading products:', error);
            this.showError('Failed to load products');
        } finally {
            this.showLoading(false);
        }
    }

    async fetchProducts() {
        // In a real application, this would fetch from your API
        // For demo purposes, returning mock data based on ENGWE analysis
        return [
            {
                id: 1,
                name: "Engine Pro 2.0",
                description: "75Nm High Torque Outdoor Adventure Folding E-bike",
                price: 1499,
                originalPrice: 1799,
                image: "https://images.unsplash.com/photo-1571068316344-75bc76f77890?w=400",
                category: ["fat-tire", "folding"],
                colors: ["Mountain Green", "Space Black", "Midnight Blue"],
                availability: "in-stock",
                badge: "Best Seller",
                rating: 4.8,
                reviews: 124
            },
            {
                id: 2,
                name: "L20 Boost",
                description: "250W 126KM Range Torque Sensor Electric Fat Bike with Boost Button",
                price: 1149,
                originalPrice: 1299,
                image: "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400",
                category: ["fat-tire", "commuter"],
                colors: ["Black", "Sea Green", "Burgundy"],
                availability: "in-stock",
                badge: "New",
                rating: 4.6,
                reviews: 89
            },
            {
                id: 3,
                name: "ENGWE M20",
                description: "Full Suspension Fat E-bike That Looks Like a Motorcycle",
                price: 1099,
                originalPrice: 1199,
                image: "https://images.unsplash.com/photo-1544191696-15693072f0d8?w=400",
                category: ["fat-tire", "motorcycle"],
                colors: ["Black", "White", "Green"],
                availability: "in-stock",
                badge: "Popular",
                rating: 4.7,
                reviews: 156
            },
            {
                id: 4,
                name: "EP-2 Boost",
                description: "EU Legal 250W 120km Boost Power Torque Sensor All-Terrain E-Bike",
                price: 1099,
                originalPrice: 1299,
                image: "https://images.unsplash.com/photo-1571068316344-75bc76f77890?w=400",
                category: ["commuter", "fat-tire"],
                colors: ["Black", "Silver"],
                availability: "in-stock",
                badge: "Eco-Friendly",
                rating: 4.5,
                reviews: 78
            },
            {
                id: 5,
                name: "ENGWE P20",
                description: "Compact Folding Electric Bike for Urban Commuting",
                price: 1299,
                originalPrice: 1499,
                image: "https://images.unsplash.com/photo-1502744688674-c619d1586c9e?w=400",
                category: ["folding", "commuter"],
                colors: ["White", "Black", "Red"],
                availability: "in-stock",
                badge: "Compact",
                rating: 4.4,
                reviews: 92
            },
            {
                id: 6,
                name: "ENGWE E26",
                description: "Premium Electric Mountain Bike with Advanced Features",
                price: 1499,
                originalPrice: 1699,
                image: "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400",
                category: ["fat-tire", "motorcycle"],
                colors: ["Blue", "Black", "Orange"],
                availability: "in-stock",
                badge: "Premium",
                rating: 4.9,
                reviews: 203
            }
        ];
    }

    renderProducts(products) {
        const grid = document.getElementById('products-grid');
        grid.innerHTML = '';

        products.forEach(product => {
            const productCard = this.createProductCard(product);
            grid.appendChild(productCard);
        });

        // Add animation
        grid.querySelectorAll('.product-card').forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('fade-in-up');
        });
    }

    createProductCard(product) {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.dataset.category = product.category.join(' ');
        
        const discount = Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100);
        
        card.innerHTML = `
            <div class="product-image">
                <img src="${product.image}" alt="${product.name}" loading="lazy">
                ${product.badge ? `<div class="product-badge">${product.badge}</div>` : ''}
            </div>
            <div class="product-content">
                <h3 class="product-title">${product.name}</h3>
                <p class="product-description">${product.description}</p>
                <div class="product-rating">
                    ${this.generateStars(product.rating)}
                    <span class="rating-text">(${product.reviews} reviews)</span>
                </div>
                <div class="product-price">
                    <span class="current-price">€${product.price}</span>
                    ${product.originalPrice ? `<span class="original-price">€${product.originalPrice}</span>` : ''}
                    ${discount > 0 ? `<span class="discount">-${discount}%</span>` : ''}
                </div>
                <div class="product-actions">
                    <button class="btn btn-primary add-to-cart" data-product-id="${product.id}">
                        <i class="fas fa-cart-plus"></i> Add to Cart
                    </button>
                    <button class="quick-view" data-product-id="${product.id}" title="Quick View">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        card.querySelector('.add-to-cart').addEventListener('click', () => {
            this.addToCart(product.id);
        });

        card.querySelector('.quick-view').addEventListener('click', () => {
            this.showProductModal(product.id);
        });

        return card;
    }

    generateStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;
        let starsHTML = '';
        
        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<i class="fas fa-star"></i>';
        }
        
        if (hasHalfStar) {
            starsHTML += '<i class="fas fa-star-half-alt"></i>';
        }
        
        const emptyStars = 5 - Math.ceil(rating);
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<i class="far fa-star"></i>';
        }
        
        return `<div class="stars">${starsHTML}</div>`;
    }

    filterProducts(filter) {
        this.currentFilter = filter;
        
        // Update active filter button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
        
        // Filter products
        const filteredProducts = filter === 'all' 
            ? this.products 
            : this.products.filter(product => product.category.includes(filter));
        
        this.renderProducts(filteredProducts);
    }

    searchProducts(query) {
        if (!query.trim()) {
            this.renderProducts(this.products);
            return;
        }
        
        const searchResults = this.products.filter(product => 
            product.name.toLowerCase().includes(query.toLowerCase()) ||
            product.description.toLowerCase().includes(query.toLowerCase())
        );
        
        this.renderProducts(searchResults);
    }

    addToCart(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;
        
        const existingItem = this.cart.find(item => item.id === productId);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({ ...product, quantity: 1 });
        }
        
        this.saveCart();
        this.updateCartCount();
        this.showNotification(`${product.name} added to cart!`);
    }

    updateCartCount() {
        const count = this.cart.reduce((total, item) => total + item.quantity, 0);
        document.querySelector('.cart-count').textContent = count;
    }

    saveCart() {
        localStorage.setItem('cart', JSON.stringify(this.cart));
    }

    showProductModal(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;
        
        const modal = document.getElementById('product-modal');
        const modalBody = modal.querySelector('.modal-body');
        
        modalBody.innerHTML = `
            <div class="product-modal-content">
                <div class="product-modal-image">
                    <img src="${product.image}" alt="${product.name}">
                </div>
                <div class="product-modal-details">
                    <h2>${product.name}</h2>
                    <div class="product-rating">
                        ${this.generateStars(product.rating)}
                        <span class="rating-text">(${product.reviews} reviews)</span>
                    </div>
                    <p class="product-description">${product.description}</p>
                    <div class="product-price">
                        <span class="current-price">€${product.price}</span>
                        ${product.originalPrice ? `<span class="original-price">€${product.originalPrice}</span>` : ''}
                    </div>
                    <div class="product-colors">
                        <h4>Available Colors:</h4>
                        <div class="color-options">
                            ${product.colors.map(color => `<span class="color-option">${color}</span>`).join('')}
                        </div>
                    </div>
                    <div class="product-modal-actions">
                        <button class="btn btn-primary add-to-cart" data-product-id="${product.id}">
                            <i class="fas fa-cart-plus"></i> Add to Cart
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add event listener for modal add to cart
        modalBody.querySelector('.add-to-cart').addEventListener('click', () => {
            this.addToCart(product.id);
            this.closeModal();
        });
        
        modal.style.display = 'flex';
    }

    closeModal() {
        document.getElementById('product-modal').style.display = 'none';
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--primary-color);
            color: white;
            padding: 1rem 2rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            z-index: 3000;
            animation: fadeInUp 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'fadeIn 0.3s ease-out reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    showError(message) {
        this.showNotification(`Error: ${message}`);
    }

    handleNewsletterSignup(e) {
        const email = e.target.querySelector('input[type="email"]').value;
        
        if (!email) {
            this.showError('Please enter a valid email address');
            return;
        }
        
        // Simulate API call
        setTimeout(() => {
            this.showNotification('Thank you for subscribing!');
            e.target.reset();
        }, 1000);
    }

    loadMoreProducts() {
        // Simulate loading more products
        this.showNotification('Loading more products...');
        
        // In a real app, this would fetch more products from the API
        setTimeout(() => {
            this.showNotification('All products loaded!');
        }, 1500);
    }

    // Automated inventory synchronization
    startInventorySync() {
        // Start periodic inventory updates
        setInterval(() => {
            this.syncInventory();
        }, 300000); // Every 5 minutes
        
        // Initial sync
        this.syncInventory();
    }

    async syncInventory() {
        try {
            console.log('Syncing inventory with source site...');
            
            // In a real application, this would call your backend API
            // which scrapes the ENGWE site for updated inventory
            const response = await fetch('/api/sync-inventory', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source: 'https://engwe.com/',
                    lastSync: localStorage.getItem('lastInventorySync')
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Inventory sync completed:', data);
                localStorage.setItem('lastInventorySync', new Date().toISOString());
            }
        } catch (error) {
            console.log('Inventory sync will be handled by backend service');
            // In production, this would be handled by a separate backend service
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NLEBikeApp();
});

// Service Worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}