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

    async loadProducts(useCache = true) {
        this.showLoading(true);
        
        try {
            // Check if we should use cached products first
            if (useCache) {
                const cachedProducts = this.getCachedProducts();
                if (cachedProducts.length > 0) {
                    this.products = cachedProducts;
                    this.renderProducts(this.products);
                    
                    // Load fresh data in background
                    this.fetchProducts().then(freshProducts => {
                        if (freshProducts.length > 0) {
                            this.products = freshProducts;
                            this.cacheProducts(freshProducts);
                            this.renderProducts(this.products);
                        }
                    }).catch(console.error);
                    
                    return;
                }
            }
            
            // Load products from API
            this.products = await this.fetchProducts();
            if (this.products.length > 0) {
                this.cacheProducts(this.products);
            }
            this.renderProducts(this.products);
            
        } catch (error) {
            console.error('Error loading products:', error);
            this.showError('Failed to load products');
        } finally {
            this.showLoading(false);
        }
    }
    
    getCachedProducts() {
        try {
            const cached = localStorage.getItem('cachedProducts');
            const cacheTime = localStorage.getItem('cacheTime');
            
            if (cached && cacheTime) {
                const cacheAge = Date.now() - parseInt(cacheTime);
                const maxAge = 5 * 60 * 1000; // 5 minutes
                
                if (cacheAge < maxAge) {
                    return JSON.parse(cached);
                }
            }
        } catch (error) {
            console.error('Error reading cached products:', error);
        }
        return [];
    }
    
    cacheProducts(products) {
        try {
            localStorage.setItem('cachedProducts', JSON.stringify(products));
            localStorage.setItem('cacheTime', Date.now().toString());
        } catch (error) {
            console.error('Error caching products:', error);
        }
    }
    
    async refreshProducts() {
        console.log('Refreshing products from server...');
        return this.loadProducts(false); // Force fresh fetch
    }

    async fetchProducts() {
        try {
            // Fetch ALL products from the API
            const response = await fetch('/api/products/all?in_stock_only=false');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const products = await response.json();
            
            // Transform API data to match frontend format if needed
            return products.map(product => ({
                id: product.id,
                name: product.name,
                description: product.description,
                price: product.price,
                originalPrice: product.original_price,
                image: product.image_url || "https://images.unsplash.com/photo-1571068316344-75bc76f77890?w=400",
                category: product.category,
                colors: product.colors,
                availability: product.availability,
                badge: this.generateBadge(product),
                rating: product.rating || 4.5,
                reviews: product.reviews_count || 0,
                specifications: product.specifications,
                lastUpdated: product.last_updated
            }));
            
        } catch (error) {
            console.error('Error fetching products from API:', error);
            
            // Fallback: try to load from localStorage if API fails
            const cachedProducts = localStorage.getItem('cachedProducts');
            if (cachedProducts) {
                console.log('Loading cached products as fallback');
                return JSON.parse(cachedProducts);
            }
            
            // Ultimate fallback: return empty array
            console.warn('No products available - API failed and no cache found');
            return [];
        }
    }
    
    generateBadge(product) {
        // Generate appropriate badge based on product data
        if (product.availability === 'limited-stock') {
            return 'Limited Stock';
        } else if (product.original_price && product.price < product.original_price) {
            const discount = Math.round(((product.original_price - product.price) / product.original_price) * 100);
            if (discount >= 20) {
                return `${discount}% OFF`;
            }
        } else if (product.rating && product.rating >= 4.8) {
            return 'Top Rated';
        } else if (product.reviews_count && product.reviews_count > 100) {
            return 'Popular';
        } else if (this.isNewProduct(product.last_updated)) {
            return 'New';
        }
        return null;
    }
    
    isNewProduct(lastUpdated) {
        if (!lastUpdated) return false;
        const productDate = new Date(lastUpdated);
        const now = new Date();
        const daysDiff = (now - productDate) / (1000 * 60 * 60 * 24);
        return daysDiff <= 7; // Product is "new" if updated within last 7 days
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
        // Start periodic inventory updates (every 5 minutes for real-time stock)
        setInterval(() => {
            this.syncInventory();
        }, 300000); // Every 5 minutes
        
        // Start periodic product refresh (every 1 minute for real-time updates)
        setInterval(() => {
            this.refreshProducts();
        }, 60000); // Every 1 minute
        
        // Initial sync
        this.syncInventory();
    }

    async syncInventory() {
        try {
            console.log('Syncing inventory with ENGWE source site...');
            
            // Call the backend API to trigger inventory sync
            const response = await fetch('/api/sync-inventory', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source: 'https://engwe.com/',
                    force: false,
                    lastSync: localStorage.getItem('lastInventorySync')
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Inventory sync completed:', data);
                localStorage.setItem('lastInventorySync', new Date().toISOString());
                
                // Refresh products to show latest data
                setTimeout(() => {
                    this.refreshProducts();
                }, 2000); // Wait 2 seconds for sync to complete
                
                // Show notification if significant changes
                if (data.products_added > 0 || data.products_updated > 5) {
                    this.showNotification(
                        `Inventory updated: ${data.products_added} new products, ${data.products_updated} updated`,
                        'success'
                    );
                }
            }
        } catch (error) {
            console.log('Inventory sync handled by background service');
            // Backend service handles the sync automatically
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Close button functionality
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
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