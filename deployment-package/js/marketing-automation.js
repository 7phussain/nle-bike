/**
 * Advanced Marketing Automation & Customer Behavior Tracking
 * Author: MiniMax Agent
 * 
 * This script handles:
 * - Customer behavior tracking
 * - Cart abandonment detection
 * - Wishlist management
 * - Push notification integration
 * - Email marketing automation
 * - WhatsApp integration
 * - Real-time analytics
 */

class MarketingAutomationClient {
    constructor() {
        this.userId = this.getUserId();
        this.sessionId = this.getSessionId();
        this.cart = this.loadCart();
        this.wishlist = this.loadWishlist();
        this.notifications = [];
        this.behaviorQueue = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupCartAbandonment();
        this.setupPushNotifications();
        this.trackPageView();
        this.setupHeartbeat();
        
        console.log('🚀 NLE Bike Marketing Automation initialized');
    }
    
    // User & Session Management
    getUserId() {
        let userId = localStorage.getItem('nle_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('nle_user_id', userId);
        }
        return userId;
    }
    
    getSessionId() {
        let sessionId = sessionStorage.getItem('nle_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('nle_session_id', sessionId);
        }
        return sessionId;
    }
    
    // Behavior Tracking
    trackBehavior(eventType, eventData = {}) {
        const behaviorData = {
            userId: this.userId,
            sessionId: this.sessionId,
            eventType: eventType,
            eventData: eventData,
            timestamp: new Date().toISOString(),
            pageUrl: window.location.href,
            userAgent: navigator.userAgent,
            referrer: document.referrer,
            deviceType: this.getDeviceType(),
            screenResolution: `${screen.width}x${screen.height}`
        };
        
        // Add to queue for batch sending
        this.behaviorQueue.push(behaviorData);
        
        // Send immediately for critical events
        if (this.isCriticalEvent(eventType)) {
            this.sendBehaviorData([behaviorData]);
        }
        
        // Process event for real-time automation
        this.processEvent(eventType, eventData);
        
        console.log('📊 Tracked behavior:', eventType, eventData);
    }
    
    isCriticalEvent(eventType) {
        return ['add_to_cart', 'remove_from_cart', 'purchase', 'cart_abandonment'].includes(eventType);
    }
    
    processEvent(eventType, eventData) {
        switch (eventType) {
            case 'add_to_cart':
                this.handleAddToCart(eventData);
                break;
            case 'remove_from_cart':
                this.handleRemoveFromCart(eventData);
                break;
            case 'wishlist_add':
                this.handleWishlistAdd(eventData);
                break;
            case 'product_view':
                this.handleProductView(eventData);
                break;
            case 'page_exit':
                this.handlePageExit(eventData);
                break;
        }
    }
    
    // Cart Management
    handleAddToCart(productData) {
        const cartItem = {
            productId: productData.productId,
            productName: productData.productName,
            price: productData.price,
            quantity: productData.quantity || 1,
            imageUrl: productData.imageUrl,
            addedAt: new Date().toISOString()
        };
        
        // Update cart
        const existingItem = this.cart.find(item => item.productId === productData.productId);
        if (existingItem) {
            existingItem.quantity += cartItem.quantity;
        } else {
            this.cart.push(cartItem);
        }
        
        this.saveCart();
        this.updateCartUI();
        
        // Schedule cart abandonment tracking
        this.scheduleCartAbandonmentCheck();
        
        // Show add to cart notification
        this.showNotification('✅ Added to cart!', `${productData.productName} added successfully`, 'success');
        
        // Track for analytics
        this.trackBehavior('cart_updated', {
            action: 'add',
            productId: productData.productId,
            cartTotal: this.getCartTotal(),
            cartItemCount: this.cart.length
        });
    }
    
    handleRemoveFromCart(productData) {
        this.cart = this.cart.filter(item => item.productId !== productData.productId);
        this.saveCart();
        this.updateCartUI();
        
        this.showNotification('🗑️ Removed from cart', `${productData.productName} removed`, 'info');
    }
    
    // Wishlist Management
    handleWishlistAdd(productData) {
        const wishlistItem = {
            productId: productData.productId,
            productName: productData.productName,
            price: productData.price,
            imageUrl: productData.imageUrl,
            addedAt: new Date().toISOString()
        };
        
        // Check if already in wishlist
        if (!this.wishlist.find(item => item.productId === productData.productId)) {
            this.wishlist.push(wishlistItem);
            this.saveWishlist();
            this.updateWishlistUI();
            
            this.showNotification('❤️ Added to wishlist!', `We'll notify you about price drops for ${productData.productName}`, 'success');
            
            // Send wishlist confirmation email
            this.sendWishlistConfirmation(productData);
        } else {
            this.showNotification('ℹ️ Already in wishlist', `${productData.productName} is already saved`, 'info');
        }
    }
    
    handleProductView(productData) {
        // Track product interest for personalization
        this.trackBehavior('product_interest', {
            productId: productData.productId,
            category: productData.category,
            price: productData.price,
            timeSpent: this.getTimeOnPage()
        });
        
        // Check for price drop notifications
        this.checkPriceDropNotifications(productData);
        
        // Show related products notification after some time
        setTimeout(() => {
            this.showRelatedProductsNotification(productData);
        }, 30000); // After 30 seconds
    }
    
    // Cart Abandonment
    setupCartAbandonment() {
        // Track when user leaves page with items in cart
        window.addEventListener('beforeunload', () => {
            if (this.cart.length > 0) {
                this.trackBehavior('cart_abandonment', {
                    cartItems: this.cart,
                    cartTotal: this.getCartTotal(),
                    timeSpentOnSite: this.getTimeSpentOnSite()
                });
            }
        });
        
        // Track page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.cart.length > 0) {
                this.scheduleCartAbandonmentEmail();
            }
        });
    }
    
    scheduleCartAbandonmentCheck() {
        // Clear any existing timeout
        if (this.cartAbandonmentTimeout) {
            clearTimeout(this.cartAbandonmentTimeout);
        }
        
        // Schedule check for 30 minutes
        this.cartAbandonmentTimeout = setTimeout(() => {
            if (this.cart.length > 0) {
                this.triggerCartAbandonmentFlow();
            }
        }, 30 * 60 * 1000); // 30 minutes
    }
    
    triggerCartAbandonmentFlow() {
        // Send immediate recovery email
        this.sendCartAbandonmentEmail('immediate');
        
        // Schedule follow-up emails
        setTimeout(() => {
            if (this.cart.length > 0) {
                this.sendCartAbandonmentEmail('24hour');
            }
        }, 24 * 60 * 60 * 1000); // 24 hours
        
        setTimeout(() => {
            if (this.cart.length > 0) {
                this.sendCartAbandonmentEmail('final');
            }
        }, 72 * 60 * 60 * 1000); // 72 hours
    }
    
    // Push Notifications
    setupPushNotifications() {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            this.initializePushNotifications();
        }
    }
    
    async initializePushNotifications() {
        try {
            // Register service worker
            const registration = await navigator.serviceWorker.register('/sw.js');
            
            // Request notification permission
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                // Subscribe to push notifications
                const subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.getVapidKey()
                });
                
                // Send subscription to server
                this.sendPushSubscription(subscription);
                
                console.log('✅ Push notifications enabled');
            }
        } catch (error) {
            console.log('❌ Push notification setup failed:', error);
        }
    }
    
    sendPushNotification(title, message, actionUrl = null) {
        if (Notification.permission === 'granted') {
            const notification = new Notification(title, {
                body: message,
                icon: '/images/logo-notification.png',
                badge: '/images/badge.png',
                tag: 'nle-bike-notification',
                requireInteraction: true,
                actions: actionUrl ? [
                    { action: 'view', title: 'View Details' },
                    { action: 'dismiss', title: 'Dismiss' }
                ] : []
            });
            
            notification.onclick = () => {
                if (actionUrl) {
                    window.open(actionUrl);
                }
                notification.close();
            };
        }
    }
    
    // Email Marketing Integration
    sendCartAbandonmentEmail(type) {
        const emailData = {
            userId: this.userId,
            type: 'cart_abandonment',
            template: type,
            cartData: this.cart,
            cartTotal: this.getCartTotal(),
            timestamp: new Date().toISOString()
        };
        
        this.sendToServer('/api/marketing/send-email', emailData);
        
        // Show recovery notification
        this.showCartRecoveryNotification(type);
    }
    
    sendWishlistConfirmation(productData) {
        const emailData = {
            userId: this.userId,
            type: 'wishlist_confirmation',
            productData: productData,
            timestamp: new Date().toISOString()
        };
        
        this.sendToServer('/api/marketing/send-email', emailData);
    }
    
    sendPriceDropAlert(productData, oldPrice, newPrice) {
        const emailData = {
            userId: this.userId,
            type: 'price_drop',
            productData: productData,
            oldPrice: oldPrice,
            newPrice: newPrice,
            savings: oldPrice - newPrice,
            timestamp: new Date().toISOString()
        };
        
        this.sendToServer('/api/marketing/send-email', emailData);
        
        // Show browser notification
        this.sendPushNotification(
            '💰 Price Drop Alert!',
            `${productData.productName} is now $${newPrice} (was $${oldPrice})`,
            `/product/${productData.productId}`
        );
    }
    
    // WhatsApp Integration
    sendWhatsAppMessage(message, phoneNumber = null) {
        const whatsappData = {
            userId: this.userId,
            message: message,
            phoneNumber: phoneNumber,
            timestamp: new Date().toISOString()
        };
        
        this.sendToServer('/api/marketing/send-whatsapp', whatsappData);
    }
    
    // Notification System
    showNotification(title, message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        // Add styles if not already added
        if (!document.getElementById('notification-styles')) {
            this.addNotificationStyles();
        }
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
        
        // Track notification display
        this.trackBehavior('notification_shown', {
            title: title,
            type: type,
            timestamp: new Date().toISOString()
        });
    }
    
    showCartRecoveryNotification(type) {
        const messages = {
            immediate: {
                title: '🛒 Don\'t forget your cart!',
                message: 'Your ENGWE e-bike is waiting. Complete your purchase now!'
            },
            '24hour': {
                title: '⏰ Still thinking it over?',
                message: 'Your cart expires soon. These bikes won\'t last long!'
            },
            final: {
                title: '🚨 Last chance!',
                message: 'Use code SAVE10 for 10% off before your cart expires!'
            }
        };
        
        const notif = messages[type];
        if (notif) {
            this.showNotification(notif.title, notif.message, 'warning', 8000);
        }
    }
    
    showRelatedProductsNotification(currentProduct) {
        // Find related products (simplified logic)
        const relatedMessage = `Customers also viewed other ${currentProduct.category} bikes. Check them out!`;
        
        this.showNotification(
            '🚴‍♂️ You might also like',
            relatedMessage,
            'info',
            6000
        );
    }
    
    // Price Drop Monitoring
    checkPriceDropNotifications(productData) {
        // Check if product is in wishlist and price has dropped
        const wishlistItem = this.wishlist.find(item => item.productId === productData.productId);
        
        if (wishlistItem && productData.price < wishlistItem.price) {
            this.sendPriceDropAlert(productData, wishlistItem.price, productData.price);
            
            // Update wishlist with new price
            wishlistItem.price = productData.price;
            this.saveWishlist();
        }
    }
    
    // Analytics & Utilities
    getTimeOnPage() {
        return Date.now() - this.pageLoadTime;
    }
    
    getTimeSpentOnSite() {
        const sessionStart = sessionStorage.getItem('nle_session_start');
        return sessionStart ? Date.now() - parseInt(sessionStart) : 0;
    }
    
    getDeviceType() {
        const width = window.innerWidth;
        if (width <= 768) return 'mobile';
        if (width <= 1024) return 'tablet';
        return 'desktop';
    }
    
    getCartTotal() {
        return this.cart.reduce((total, item) => total + (item.price * item.quantity), 0);
    }
    
    // Data Persistence
    loadCart() {
        const saved = localStorage.getItem('nle_cart');
        return saved ? JSON.parse(saved) : [];
    }
    
    saveCart() {
        localStorage.setItem('nle_cart', JSON.stringify(this.cart));
    }
    
    loadWishlist() {
        const saved = localStorage.getItem('nle_wishlist');
        return saved ? JSON.parse(saved) : [];
    }
    
    saveWishlist() {
        localStorage.setItem('nle_wishlist', JSON.stringify(this.wishlist));
    }
    
    // UI Updates
    updateCartUI() {
        const cartCount = document.getElementById('cart-count');
        if (cartCount) {
            cartCount.textContent = this.cart.reduce((total, item) => total + item.quantity, 0);
        }
        
        // Update cart page if we're on it
        if (window.location.pathname.includes('cart')) {
            this.refreshCartPage();
        }
    }
    
    updateWishlistUI() {
        const wishlistCount = document.getElementById('wishlist-count');
        if (wishlistCount) {
            wishlistCount.textContent = this.wishlist.length;
        }
    }
    
    // Server Communication
    sendBehaviorData(behaviors) {
        this.sendToServer('/api/marketing/track-behavior', {
            behaviors: behaviors,
            userId: this.userId,
            sessionId: this.sessionId
        });
    }
    
    sendToServer(endpoint, data) {
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        }).catch(error => {
            console.log('Network error:', error);
            // Queue for retry
            this.queueForRetry(endpoint, data);
        });
    }
    
    queueForRetry(endpoint, data) {
        const retryQueue = JSON.parse(localStorage.getItem('nle_retry_queue') || '[]');
        retryQueue.push({ endpoint, data, timestamp: Date.now() });
        localStorage.setItem('nle_retry_queue', JSON.stringify(retryQueue));
    }
    
    // Event Listeners
    setupEventListeners() {
        // Track page views
        this.trackPageView();
        
        // Track clicks on products
        document.addEventListener('click', (e) => {
            if (e.target.closest('.product-card')) {
                const productElement = e.target.closest('.product-card');
                this.trackProductClick(productElement);
            }
            
            // Track CTA clicks
            if (e.target.closest('.btn-primary, .btn-secondary')) {
                this.trackBehavior('cta_click', {
                    buttonText: e.target.textContent,
                    location: window.location.pathname
                });
            }
        });
        
        // Track form interactions
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'contact-form') {
                this.trackBehavior('contact_form_submit', {
                    formData: new FormData(e.target)
                });
            }
        });
        
        // Track scroll depth
        this.setupScrollTracking();
        
        // Set up session tracking
        if (!sessionStorage.getItem('nle_session_start')) {
            sessionStorage.setItem('nle_session_start', Date.now().toString());
        }
        
        this.pageLoadTime = Date.now();
    }
    
    trackPageView() {
        this.trackBehavior('page_view', {
            page: window.location.pathname,
            title: document.title,
            referrer: document.referrer,
            timestamp: new Date().toISOString()
        });
    }
    
    trackProductClick(productElement) {
        const productId = productElement.dataset.productId;
        const productName = productElement.querySelector('.product-name')?.textContent;
        const productPrice = productElement.querySelector('.product-price')?.textContent;
        
        this.trackBehavior('product_click', {
            productId: productId,
            productName: productName,
            productPrice: productPrice,
            position: Array.from(productElement.parentElement.children).indexOf(productElement)
        });
    }
    
    setupScrollTracking() {
        let maxScroll = 0;
        const milestones = [25, 50, 75, 100];
        const tracked = new Set();
        
        window.addEventListener('scroll', () => {
            const scrollPercent = Math.round((window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100);
            
            if (scrollPercent > maxScroll) {
                maxScroll = scrollPercent;
                
                milestones.forEach(milestone => {
                    if (scrollPercent >= milestone && !tracked.has(milestone)) {
                        tracked.add(milestone);
                        this.trackBehavior('scroll_depth', {
                            percentage: milestone,
                            page: window.location.pathname
                        });
                    }
                });
            }
        });
    }
    
    setupHeartbeat() {
        // Send queued behavior data every 30 seconds
        setInterval(() => {
            if (this.behaviorQueue.length > 0) {
                this.sendBehaviorData([...this.behaviorQueue]);
                this.behaviorQueue = [];
            }
        }, 30000);
        
        // Process retry queue
        setInterval(() => {
            this.processRetryQueue();
        }, 60000);
    }
    
    processRetryQueue() {
        const retryQueue = JSON.parse(localStorage.getItem('nle_retry_queue') || '[]');
        if (retryQueue.length > 0) {
            retryQueue.forEach(item => {
                this.sendToServer(item.endpoint, item.data);
            });
            localStorage.removeItem('nle_retry_queue');
        }
    }
    
    // Helper methods for other scripts
    addToCart(productData) {
        this.handleAddToCart(productData);
    }
    
    removeFromCart(productId) {
        const product = this.cart.find(item => item.productId === productId);
        if (product) {
            this.handleRemoveFromCart(product);
        }
    }
    
    addToWishlist(productData) {
        this.handleWishlistAdd(productData);
    }
    
    // Notification Styles
    addNotificationStyles() {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                padding: 16px;
                max-width: 350px;
                z-index: 10000;
                display: flex;
                align-items: center;
                gap: 12px;
                animation: slideIn 0.3s ease;
            }
            
            .notification-success { border-left: 4px solid #28a745; }
            .notification-warning { border-left: 4px solid #ffc107; }
            .notification-error { border-left: 4px solid #dc3545; }
            .notification-info { border-left: 4px solid #007bff; }
            
            .notification-content {
                flex: 1;
            }
            
            .notification-title {
                font-weight: 600;
                margin-bottom: 4px;
            }
            
            .notification-message {
                font-size: 14px;
                color: #666;
            }
            
            .notification-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #999;
                padding: 0;
                width: 20px;
                height: 20px;
            }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(styles);
    }
    
    getVapidKey() {
        // Replace with your actual VAPID key
        return 'BEl62iUYgUivxIkv69yViEuiBIa40HI80NM9wSqVxmPwvxIL0jtUX_XCWlWAj5Jn6D7G7Q_KWJZNj_Y8x1_z-Ww';
    }
}

// Global functions for easy access
let marketingAutomation;

function trackBehavior(eventType, eventData) {
    if (marketingAutomation) {
        marketingAutomation.trackBehavior(eventType, eventData);
    }
}

function addToCart(productData) {
    if (marketingAutomation) {
        marketingAutomation.addToCart(productData);
    }
}

function removeFromCart(productId) {
    if (marketingAutomation) {
        marketingAutomation.removeFromCart(productId);
    }
}

function addToWishlist(productData) {
    if (marketingAutomation) {
        marketingAutomation.addToWishlist(productData);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    marketingAutomation = new MarketingAutomationClient();
    
    // Make available globally for debugging
    window.marketingAutomation = marketingAutomation;
    window.trackBehavior = trackBehavior;
    window.addToCart = addToCart;
    window.removeFromCart = removeFromCart;
    window.addToWishlist = addToWishlist;
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MarketingAutomationClient, trackBehavior, addToCart, removeFromCart, addToWishlist };
}
