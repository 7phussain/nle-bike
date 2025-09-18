// Enhanced Drop Shipping Application with Advanced Features
// Author: MiniMax Agent

class AdvancedDropShippingApp extends NLEBikeApp {
    constructor() {
        super();
        this.currency = localStorage.getItem('currency') || 'EUR';
        this.exchangeRates = {};
        this.abandonedCarts = JSON.parse(localStorage.getItem('abandonedCarts')) || [];
        this.wishlist = JSON.parse(localStorage.getItem('wishlist')) || [];
        this.chatWidget = null;
        this.emailSubscribers = JSON.parse(localStorage.getItem('emailSubscribers')) || [];
        
        this.initAdvancedFeatures();
    }

    initAdvancedFeatures() {
        this.loadExchangeRates();
        this.initSEOOptimization();
        this.initPaymentGateways();
        this.initSocialMediaIntegration();
        this.initLiveChat();
        this.initEmailMarketing();
        this.initAnalytics();
        this.initAbandonedCartRecovery();
        this.initCouponSystem();
        this.initReviewsSystem();
        this.initMultiCurrency();
        this.initShippingOptions();
        this.startPerformanceOptimization();
    }

    // Multi-Currency Support
    async loadExchangeRates() {
        try {
            // In production, use a real exchange rate API
            const mockRates = {
                'EUR': 1.0,
                'USD': 1.09,
                'GBP': 0.87,
                'JPY': 162.50,
                'CAD': 1.47,
                'AUD': 1.64,
                'CHF': 0.97
            };
            this.exchangeRates = mockRates;
            this.updateCurrencyDisplay();
        } catch (error) {
            console.error('Error loading exchange rates:', error);
        }
    }

    initMultiCurrency() {
        // Add currency selector to header
        const headerActions = document.querySelector('.header-actions');
        const currencySelector = document.createElement('div');
        currencySelector.className = 'currency-selector';
        currencySelector.innerHTML = `
            <select class="currency-select">
                <option value="EUR">EUR €</option>
                <option value="USD">USD $</option>
                <option value="GBP">GBP £</option>
                <option value="JPY">JPY ¥</option>
                <option value="CAD">CAD $</option>
                <option value="AUD">AUD $</option>
                <option value="CHF">CHF Fr</option>
            </select>
        `;
        headerActions.insertBefore(currencySelector, headerActions.firstChild);

        const select = currencySelector.querySelector('.currency-select');
        select.value = this.currency;
        select.addEventListener('change', (e) => {
            this.changeCurrency(e.target.value);
        });
    }

    changeCurrency(newCurrency) {
        this.currency = newCurrency;
        localStorage.setItem('currency', newCurrency);
        this.updateCurrencyDisplay();
        this.renderProducts(this.products);
    }

    convertPrice(price, fromCurrency = 'EUR', toCurrency = this.currency) {
        if (fromCurrency === toCurrency) return price;
        const rate = this.exchangeRates[toCurrency] / this.exchangeRates[fromCurrency];
        return (price * rate).toFixed(2);
    }

    formatPrice(price, currency = this.currency) {
        const symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'JPY': '¥',
            'CAD': 'C$',
            'AUD': 'A$',
            'CHF': 'Fr'
        };
        const convertedPrice = this.convertPrice(price);
        return `${symbols[currency]}${convertedPrice}`;
    }

    updateCurrencyDisplay() {
        document.querySelectorAll('.current-price, .original-price').forEach(elem => {
            const price = parseFloat(elem.dataset.basePrice || elem.textContent.replace(/[^0-9.]/g, ''));
            if (price) {
                elem.dataset.basePrice = price;
                elem.textContent = this.formatPrice(price);
            }
        });
    }

    // Payment Gateway Integration
    initPaymentGateways() {
        this.paymentMethods = {
            stripe: {
                name: 'Stripe',
                icon: 'fab fa-stripe',
                enabled: true
            },
            paypal: {
                name: 'PayPal',
                icon: 'fab fa-paypal',
                enabled: true
            },
            apple_pay: {
                name: 'Apple Pay',
                icon: 'fab fa-apple-pay',
                enabled: true
            },
            google_pay: {
                name: 'Google Pay',
                icon: 'fab fa-google-pay',
                enabled: true
            }
        };
    }

    // SEO Optimization
    initSEOOptimization() {
        // Add structured data
        this.addStructuredData();
        
        // Update meta tags dynamically
        this.updateMetaTags();
        
        // Add Open Graph tags
        this.addOpenGraphTags();
        
        // Generate sitemap
        this.generateSitemap();
    }

    addStructuredData() {
        const structuredData = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "NLE Bike",
            "url": window.location.origin,
            "description": "Premium Electric Bikes for Modern Urban Mobility",
            "potentialAction": {
                "@type": "SearchAction",
                "target": `${window.location.origin}/search?q={search_term_string}`,
                "query-input": "required name=search_term_string"
            }
        };

        const script = document.createElement('script');
        script.type = 'application/ld+json';
        script.textContent = JSON.stringify(structuredData);
        document.head.appendChild(script);
    }

    updateMetaTags() {
        const metaTags = {
            'description': 'Premium electric bikes with cutting-edge technology. Free shipping, 2-year warranty, and 24/7 support.',
            'keywords': 'electric bikes, e-bikes, electric bicycles, ebikes, electric scooters, urban mobility',
            'author': 'NLE Bike',
            'robots': 'index, follow',
            'viewport': 'width=device-width, initial-scale=1.0'
        };

        Object.entries(metaTags).forEach(([name, content]) => {
            let meta = document.querySelector(`meta[name="${name}"]`);
            if (!meta) {
                meta = document.createElement('meta');
                meta.name = name;
                document.head.appendChild(meta);
            }
            meta.content = content;
        });
    }

    addOpenGraphTags() {
        const ogTags = {
            'og:title': 'NLE Bike - Premium Electric Bikes',
            'og:description': 'Experience the future of urban mobility with our premium electric bikes',
            'og:image': `${window.location.origin}/images/hero-bike.jpg`,
            'og:url': window.location.href,
            'og:type': 'website',
            'og:site_name': 'NLE Bike'
        };

        Object.entries(ogTags).forEach(([property, content]) => {
            let meta = document.querySelector(`meta[property="${property}"]`);
            if (!meta) {
                meta = document.createElement('meta');
                meta.setAttribute('property', property);
                document.head.appendChild(meta);
            }
            meta.content = content;
        });
    }

    // Social Media Integration
    initSocialMediaIntegration() {
        this.addSocialButtons();
        this.initSocialPixels();
    }

    addSocialButtons() {
        const shareButtons = document.createElement('div');
        shareButtons.className = 'social-share-buttons';
        shareButtons.innerHTML = `
            <div class="share-dropdown">
                <button class="share-btn">
                    <i class="fas fa-share-alt"></i> Share
                </button>
                <div class="share-options">
                    <a href="#" class="share-facebook"><i class="fab fa-facebook"></i> Facebook</a>
                    <a href="#" class="share-twitter"><i class="fab fa-twitter"></i> Twitter</a>
                    <a href="#" class="share-instagram"><i class="fab fa-instagram"></i> Instagram</a>
                    <a href="#" class="share-whatsapp"><i class="fab fa-whatsapp"></i> WhatsApp</a>
                </div>
            </div>
        `;

        document.body.appendChild(shareButtons);
        this.setupSocialSharing(shareButtons);
    }

    setupSocialSharing(container) {
        container.querySelector('.share-facebook').addEventListener('click', (e) => {
            e.preventDefault();
            this.shareToFacebook();
        });

        container.querySelector('.share-twitter').addEventListener('click', (e) => {
            e.preventDefault();
            this.shareToTwitter();
        });

        container.querySelector('.share-whatsapp').addEventListener('click', (e) => {
            e.preventDefault();
            this.shareToWhatsApp();
        });
    }

    shareToFacebook() {
        const url = encodeURIComponent(window.location.href);
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank', 'width=600,height=400');
    }

    shareToTwitter() {
        const url = encodeURIComponent(window.location.href);
        const text = encodeURIComponent('Check out these amazing electric bikes!');
        window.open(`https://twitter.com/intent/tweet?url=${url}&text=${text}`, '_blank', 'width=600,height=400');
    }

    shareToWhatsApp() {
        const url = encodeURIComponent(window.location.href);
        const text = encodeURIComponent('Check out NLE Bike - Premium Electric Bikes!');
        window.open(`https://wa.me/?text=${text} ${url}`, '_blank');
    }

    initSocialPixels() {
        // Facebook Pixel (replace with your pixel ID)
        if (typeof fbq === 'undefined') {
            !function(f,b,e,v,n,t,s)
            {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)}(window, document,'script',
            'https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', 'YOUR_PIXEL_ID');
            fbq('track', 'PageView');
        }
    }

    // Live Chat Support
    initLiveChat() {
        const chatWidget = document.createElement('div');
        chatWidget.className = 'chat-widget';
        chatWidget.innerHTML = `
            <div class="chat-button" id="chat-toggle">
                <i class="fas fa-comments"></i>
                <span class="chat-notification">1</span>
            </div>
            <div class="chat-window" id="chat-window">
                <div class="chat-header">
                    <h4>Customer Support</h4>
                    <button class="chat-close">&times;</button>
                </div>
                <div class="chat-body">
                    <div class="chat-messages" id="chat-messages">
                        <div class="message bot-message">
                            <span class="message-text">Hi! How can I help you today?</span>
                            <span class="message-time">${new Date().toLocaleTimeString()}</span>
                        </div>
                    </div>
                    <div class="chat-input-container">
                        <input type="text" class="chat-input" placeholder="Type your message..." id="chat-input">
                        <button class="chat-send" id="chat-send">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(chatWidget);
        this.setupChatFunctionality();
    }

    setupChatFunctionality() {
        const chatToggle = document.getElementById('chat-toggle');
        const chatWindow = document.getElementById('chat-window');
        const chatClose = document.querySelector('.chat-close');
        const chatInput = document.getElementById('chat-input');
        const chatSend = document.getElementById('chat-send');
        const chatMessages = document.getElementById('chat-messages');

        chatToggle.addEventListener('click', () => {
            chatWindow.classList.toggle('active');
            document.querySelector('.chat-notification').style.display = 'none';
        });

        chatClose.addEventListener('click', () => {
            chatWindow.classList.remove('active');
        });

        const sendMessage = () => {
            const message = chatInput.value.trim();
            if (message) {
                this.addChatMessage(message, 'user');
                chatInput.value = '';
                
                // Simulate bot response
                setTimeout(() => {
                    this.addBotResponse(message);
                }, 1000);
            }
        };

        chatSend.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    addChatMessage(text, sender) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = `
            <span class="message-text">${text}</span>
            <span class="message-time">${new Date().toLocaleTimeString()}</span>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    addBotResponse(userMessage) {
        const responses = {
            'hello': 'Hello! Welcome to NLE Bike. How can I assist you today?',
            'price': 'Our electric bikes range from €599 to €1,799. Would you like to see our full catalog?',
            'shipping': 'We offer free shipping worldwide! Most orders arrive within 5-7 business days.',
            'warranty': 'All our bikes come with a 2-year warranty covering manufacturing defects.',
            'support': 'Our support team is available 24/7. You can also email us at support@nlebike.com',
            'default': 'Thank you for your question! Our support team will get back to you shortly. You can also browse our FAQ section for quick answers.'
        };

        const lowerMessage = userMessage.toLowerCase();
        let response = responses.default;

        for (const keyword in responses) {
            if (lowerMessage.includes(keyword)) {
                response = responses[keyword];
                break;
            }
        }

        this.addChatMessage(response, 'bot');
    }

    // Email Marketing Integration
    initEmailMarketing() {
        this.setupNewsletterCapture();
        this.initAbandonedCartEmails();
    }

    setupNewsletterCapture() {
        // Enhanced newsletter with incentives
        const newsletter = document.querySelector('.newsletter-form');
        if (newsletter) {
            newsletter.addEventListener('submit', (e) => {
                e.preventDefault();
                const email = newsletter.querySelector('input[type="email"]').value;
                this.subscribeToNewsletter(email);
            });
        }

        // Exit-intent popup
        this.initExitIntentPopup();
    }

    subscribeToNewsletter(email) {
        if (!this.emailSubscribers.includes(email)) {
            this.emailSubscribers.push({
                email,
                subscribed: new Date().toISOString(),
                source: 'newsletter'
            });
            localStorage.setItem('emailSubscribers', JSON.stringify(this.emailSubscribers));
            
            // Send welcome email (in production, this would be server-side)
            this.sendWelcomeEmail(email);
            this.showNotification('🎉 Welcome! Check your email for a 10% discount code!');
        }
    }

    initExitIntentPopup() {
        let hasShownPopup = localStorage.getItem('exitIntentShown');
        if (hasShownPopup) return;

        document.addEventListener('mouseleave', (e) => {
            if (e.clientY <= 0 && !hasShownPopup) {
                this.showExitIntentPopup();
                localStorage.setItem('exitIntentShown', 'true');
            }
        });
    }

    showExitIntentPopup() {
        const popup = document.createElement('div');
        popup.className = 'exit-intent-popup';
        popup.innerHTML = `
            <div class="popup-content">
                <button class="popup-close">&times;</button>
                <h3>Wait! Don't Leave Empty Handed!</h3>
                <p>Get 10% off your first order</p>
                <form class="popup-email-form">
                    <input type="email" placeholder="Enter your email" required>
                    <button type="submit" class="btn btn-primary">Get Discount</button>
                </form>
            </div>
        `;

        document.body.appendChild(popup);
        setTimeout(() => popup.classList.add('active'), 100);

        popup.querySelector('.popup-close').addEventListener('click', () => {
            popup.remove();
        });

        popup.querySelector('.popup-email-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const email = e.target.querySelector('input[type="email"]').value;
            this.subscribeToNewsletter(email);
            popup.remove();
        });
    }

    // Abandoned Cart Recovery
    initAbandonedCartRecovery() {
        setInterval(() => {
            this.checkAbandonedCarts();
        }, 60000); // Check every minute
    }

    checkAbandonedCarts() {
        if (this.cart.length > 0) {
            const lastActivity = localStorage.getItem('lastCartActivity');
            const now = new Date().getTime();
            const thirtyMinutes = 30 * 60 * 1000;

            if (lastActivity && (now - parseInt(lastActivity)) > thirtyMinutes) {
                this.showAbandonedCartPopup();
            }
        }
    }

    showAbandonedCartPopup() {
        if (document.querySelector('.abandoned-cart-popup')) return;

        const popup = document.createElement('div');
        popup.className = 'abandoned-cart-popup';
        popup.innerHTML = `
            <div class="popup-content">
                <button class="popup-close">&times;</button>
                <h3>🛒 You left items in your cart!</h3>
                <p>Complete your purchase and get free shipping!</p>
                <div class="cart-preview">
                    ${this.cart.map(item => `
                        <div class="cart-item-preview">
                            <span>${item.name}</span>
                            <span>${this.formatPrice(item.price)}</span>
                        </div>
                    `).join('')}
                </div>
                <button class="btn btn-primary complete-purchase">Complete Purchase</button>
                <button class="btn btn-outline save-for-later">Save for Later</button>
            </div>
        `;

        document.body.appendChild(popup);
        setTimeout(() => popup.classList.add('active'), 100);

        popup.querySelector('.popup-close').addEventListener('click', () => {
            popup.remove();
        });

        popup.querySelector('.complete-purchase').addEventListener('click', () => {
            this.showCheckout();
            popup.remove();
        });

        popup.querySelector('.save-for-later').addEventListener('click', () => {
            this.saveCartForLater();
            popup.remove();
        });
    }

    // Coupon and Discount System
    initCouponSystem() {
        this.coupons = {
            'WELCOME10': { discount: 0.10, type: 'percentage', minOrder: 0 },
            'SAVE20': { discount: 0.20, type: 'percentage', minOrder: 500 },
            'FREESHIP': { discount: 0, type: 'free_shipping', minOrder: 0 },
            'NEWBIE15': { discount: 0.15, type: 'percentage', minOrder: 200 }
        };
    }

    applyCoupon(code) {
        const coupon = this.coupons[code.toUpperCase()];
        if (!coupon) {
            this.showNotification('❌ Invalid coupon code');
            return false;
        }

        const total = this.calculateCartTotal();
        if (total < coupon.minOrder) {
            this.showNotification(`❌ Minimum order of ${this.formatPrice(coupon.minOrder)} required`);
            return false;
        }

        localStorage.setItem('appliedCoupon', code.toUpperCase());
        this.showNotification(`✅ Coupon applied! ${coupon.discount * 100}% off`);
        this.updateCartTotal();
        return true;
    }

    // Reviews and Ratings System
    initReviewsSystem() {
        this.reviews = JSON.parse(localStorage.getItem('productReviews')) || {};
        this.addReviewsToProducts();
    }

    addReviewsToProducts() {
        // Add review functionality to product cards
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-review-btn')) {
                const productId = e.target.dataset.productId;
                this.showReviewModal(productId);
            }
        });
    }

    showReviewModal(productId) {
        const modal = document.createElement('div');
        modal.className = 'review-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Write a Review</h3>
                <div class="rating-input">
                    <span>Rating:</span>
                    <div class="stars-input">
                        ${[1,2,3,4,5].map(i => `<i class="far fa-star" data-rating="${i}"></i>`).join('')}
                    </div>
                </div>
                <textarea placeholder="Share your experience..." class="review-text"></textarea>
                <input type="text" placeholder="Your name" class="reviewer-name">
                <div class="modal-actions">
                    <button class="btn btn-primary submit-review">Submit Review</button>
                    <button class="btn btn-outline cancel-review">Cancel</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.setupReviewModal(modal, productId);
    }

    // Performance Optimization
    startPerformanceOptimization() {
        // Lazy loading for images
        this.initLazyLoading();
        
        // Service Worker for caching
        this.registerServiceWorker();
        
        // Preload critical resources
        this.preloadCriticalResources();
    }

    initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(() => console.log('Service Worker registered'))
                .catch(err => console.log('Service Worker registration failed'));
        }
    }

    // Analytics Integration
    initAnalytics() {
        // Google Analytics (replace with your tracking ID)
        if (typeof gtag === 'undefined') {
            const script = document.createElement('script');
            script.async = true;
            script.src = 'https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID';
            document.head.appendChild(script);

            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'GA_MEASUREMENT_ID');
        }

        // Track custom events
        this.trackAnalyticsEvent('page_view', {
            page_title: document.title,
            page_location: window.location.href
        });
    }

    trackAnalyticsEvent(eventName, parameters) {
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, parameters);
        }
        
        // Also track to Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', eventName, parameters);
        }
    }

    // Override parent methods to add advanced features
    addToCart(productId) {
        super.addToCart(productId);
        localStorage.setItem('lastCartActivity', new Date().getTime().toString());
        
        // Track analytics
        this.trackAnalyticsEvent('add_to_cart', {
            currency: this.currency,
            value: this.calculateCartTotal(),
            items: [{ item_id: productId }]
        });
    }

    createProductCard(product) {
        const card = super.createProductCard(product);
        
        // Add review stars and wishlist button
        const content = card.querySelector('.product-content');
        const reviewSection = document.createElement('div');
        reviewSection.className = 'product-reviews';
        reviewSection.innerHTML = `
            <div class="review-stars">
                ${this.generateStars(product.rating || 4.5)}
                <span class="review-count">(${product.reviews_count || 0} reviews)</span>
            </div>
        `;
        
        const actions = card.querySelector('.product-actions');
        const wishlistBtn = document.createElement('button');
        wishlistBtn.className = 'wishlist-btn';
        wishlistBtn.innerHTML = '<i class="far fa-heart"></i>';
        wishlistBtn.title = 'Add to Wishlist';
        wishlistBtn.addEventListener('click', () => this.toggleWishlist(product.id));
        
        content.insertBefore(reviewSection, actions);
        actions.appendChild(wishlistBtn);
        
        return card;
    }

    toggleWishlist(productId) {
        const index = this.wishlist.indexOf(productId);
        if (index > -1) {
            this.wishlist.splice(index, 1);
            this.showNotification('💔 Removed from wishlist');
        } else {
            this.wishlist.push(productId);
            this.showNotification('💖 Added to wishlist');
        }
        localStorage.setItem('wishlist', JSON.stringify(this.wishlist));
        this.updateWishlistDisplay();
    }

    updateWishlistDisplay() {
        document.querySelectorAll('.wishlist-btn').forEach(btn => {
            const productId = btn.closest('.product-card').dataset.productId;
            const icon = btn.querySelector('i');
            if (this.wishlist.includes(productId)) {
                icon.className = 'fas fa-heart';
                btn.style.color = '#e74c3c';
            } else {
                icon.className = 'far fa-heart';
                btn.style.color = '';
            }
        });
    }
}

// Initialize the enhanced application
document.addEventListener('DOMContentLoaded', () => {
    new AdvancedDropShippingApp();
});