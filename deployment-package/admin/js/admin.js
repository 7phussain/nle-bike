// Admin Dashboard JavaScript
// Author: MiniMax Agent

class AdminDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.charts = {};
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.initCharts();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.closest('.nav-link').dataset.section;
                this.showSection(section);
            });
        });

        // Manual sync button
        document.querySelector('.sync-inventory').addEventListener('click', () => {
            this.triggerManualSync();
        });

        // Settings tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.showSettingsTab(tab);
            });
        });

        // Save settings
        document.querySelector('.save-settings').addEventListener('click', () => {
            this.saveSettings();
        });

        // Filter changes
        document.querySelectorAll('.filter-select, .period-select').forEach(select => {
            select.addEventListener('change', (e) => {
                this.handleFilterChange(e.target);
            });
        });

        // Product actions
        document.addEventListener('click', (e) => {
            if (e.target.closest('.action-btn')) {
                this.handleActionClick(e.target.closest('.action-btn'));
            }
        });
    }

    showSection(sectionId) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionId}"]`).closest('.nav-item').classList.add('active');

        // Update content
        document.querySelectorAll('.admin-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionId).classList.add('active');

        this.currentSection = sectionId;
        this.loadSectionData(sectionId);
    }

    showSettingsTab(tabId) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.settings-content').forEach(content => {
            content.classList.add('hidden');
        });
        document.getElementById(`${tabId}-settings`).classList.remove('hidden');
    }

    async loadDashboardData() {
        try {
            this.showLoading(true);
            
            // Load stats
            const stats = await this.fetchStats();
            this.updateStats(stats);
            
            // Load recent activity
            const activities = await this.fetchRecentActivity();
            this.updateRecentActivity(activities);
            
            // Load top products
            const topProducts = await this.fetchTopProducts();
            this.updateTopProducts(topProducts);
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.showLoading(false);
        }
    }

    async fetchStats() {
        // In production, this would fetch from the API
        return {
            totalRevenue: 12450,
            totalOrders: 148,
            totalProducts: 42,
            totalCustomers: 1245,
            revenueChange: 12.5,
            ordersChange: 8.2,
            productsChange: 2,
            customersChange: 15.3
        };
    }

    async fetchRecentActivity() {
        return [
            {
                type: 'order',
                message: 'New order #ORD-2025-001',
                details: 'Customer: John Doe - €299.99',
                time: '2 minutes ago',
                icon: 'shopping-cart'
            },
            {
                type: 'sync',
                message: 'Inventory sync completed',
                details: '15 products updated',
                time: '10 minutes ago',
                icon: 'sync'
            },
            {
                type: 'customer',
                message: 'New customer registration',
                details: 'jane.smith@email.com',
                time: '15 minutes ago',
                icon: 'user-plus'
            },
            {
                type: 'product',
                message: 'Product price updated',
                details: 'Engine Pro 2.0 - New price: €1,399',
                time: '1 hour ago',
                icon: 'tag'
            }
        ];
    }

    async fetchTopProducts() {
        return [
            { rank: 1, name: 'Engine Pro 2.0', sales: '24 sales this week' },
            { rank: 2, name: 'L20 Boost', sales: '18 sales this week' },
            { rank: 3, name: 'ENGWE M20', sales: '15 sales this week' },
            { rank: 4, name: 'EP-2 Boost', sales: '12 sales this week' },
            { rank: 5, name: 'ENGWE P20', sales: '10 sales this week' }
        ];
    }

    updateStats(stats) {
        document.getElementById('total-revenue').textContent = `€${stats.totalRevenue.toLocaleString()}`;
        document.getElementById('total-orders').textContent = stats.totalOrders;
        document.getElementById('total-products').textContent = stats.totalProducts;
        document.getElementById('total-customers').textContent = stats.totalCustomers.toLocaleString();
    }

    updateRecentActivity(activities) {
        const container = document.getElementById('activity-list');
        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas fa-${activity.icon}"></i>
                </div>
                <div class="activity-content">
                    <p class="activity-text">${activity.message}</p>
                    <p class="activity-time">${activity.time}</p>
                </div>
            </div>
        `).join('');
    }

    updateTopProducts(products) {
        const container = document.getElementById('top-products-list');
        container.innerHTML = products.map(product => `
            <div class="top-product-item">
                <div class="product-rank">${product.rank}</div>
                <div class="product-info">
                    <p class="product-name">${product.name}</p>
                    <p class="product-sales">${product.sales}</p>
                </div>
            </div>
        `).join('');
    }

    initCharts() {
        this.initSalesChart();
        this.initRevenueChart();
        this.initTrafficChart();
    }

    initSalesChart() {
        const ctx = document.getElementById('sales-chart');
        if (!ctx) return;

        this.charts.sales = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                datasets: [{
                    label: 'Sales',
                    data: [12, 19, 15, 25, 22, 30, 28],
                    borderColor: 'rgb(37, 99, 235)',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    initRevenueChart() {
        const ctx = document.getElementById('revenue-chart');
        if (!ctx) return;

        this.charts.revenue = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Revenue (€)',
                    data: [2400, 3200, 2800, 3600],
                    backgroundColor: 'rgba(37, 99, 235, 0.8)',
                    borderColor: 'rgb(37, 99, 235)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    initTrafficChart() {
        const ctx = document.getElementById('traffic-chart');
        if (!ctx) return;

        this.charts.traffic = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Direct', 'Social Media', 'Search Engines', 'Email'],
                datasets: [{
                    data: [35, 25, 30, 10],
                    backgroundColor: [
                        'rgb(37, 99, 235)',
                        'rgb(245, 158, 11)',
                        'rgb(16, 185, 129)',
                        'rgb(239, 68, 68)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    async loadSectionData(sectionId) {
        switch (sectionId) {
            case 'products':
                await this.loadProducts();
                break;
            case 'orders':
                await this.loadOrders();
                break;
            case 'inventory':
                await this.loadInventoryData();
                break;
            case 'analytics':
                await this.loadAnalytics();
                break;
        }
    }

    async loadProducts() {
        try {
            // Fetch products from API
            const response = await fetch('/api/products?limit=100');
            const products = await response.json();
            this.renderProductsTable(products);
        } catch (error) {
            console.error('Error loading products:', error);
        }
    }

    renderProductsTable(products) {
        const tbody = document.getElementById('products-table-body');
        tbody.innerHTML = products.map(product => `
            <tr>
                <td>
                    <div class="product-info-table">
                        <img src="${product.image_url}" alt="${product.name}" class="product-image-small">
                        <div class="product-details">
                            <p class="product-title">${product.name}</p>
                            <p class="product-sku">SKU: ${product.id}</p>
                        </div>
                    </div>
                </td>
                <td>€${product.price}</td>
                <td>In Stock</td>
                <td><span class="status-badge active">${product.availability}</span></td>
                <td>${new Date(product.last_updated).toLocaleDateString()}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn edit" data-id="${product.id}" data-action="edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn view" data-id="${product.id}" data-action="view">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-btn delete" data-id="${product.id}" data-action="delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    async loadOrders() {
        try {
            // Mock order data
            const orders = [
                {
                    id: 'ORD-2025-001',
                    customer: 'John Doe',
                    products: 'Engine Pro 2.0',
                    total: 1499,
                    status: 'processing',
                    date: '2025-01-15'
                },
                {
                    id: 'ORD-2025-002',
                    customer: 'Jane Smith',
                    products: 'L20 Boost',
                    total: 1149,
                    status: 'shipped',
                    date: '2025-01-14'
                }
            ];
            this.renderOrdersTable(orders);
        } catch (error) {
            console.error('Error loading orders:', error);
        }
    }

    renderOrdersTable(orders) {
        const tbody = document.getElementById('orders-table-body');
        tbody.innerHTML = orders.map(order => `
            <tr>
                <td><strong>${order.id}</strong></td>
                <td>${order.customer}</td>
                <td>${order.products}</td>
                <td>€${order.total}</td>
                <td><span class="status-badge ${order.status}">${order.status}</span></td>
                <td>${new Date(order.date).toLocaleDateString()}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn view" data-id="${order.id}" data-action="view-order">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-btn edit" data-id="${order.id}" data-action="edit-order">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    async loadInventoryData() {
        try {
            const response = await fetch('/api/inventory/stats');
            const stats = await response.json();
            this.updateInventoryStats(stats);

            const logsResponse = await fetch('/api/inventory/sync-logs?limit=10');
            const logs = await logsResponse.json();
            this.updateSyncLogs(logs);
        } catch (error) {
            console.error('Error loading inventory data:', error);
        }
    }

    updateInventoryStats(stats) {
        if (stats.last_sync) {
            document.getElementById('last-sync-time').textContent = 
                new Date(stats.last_sync.sync_time).toLocaleString();
            document.getElementById('last-sync-status').textContent = stats.last_sync.status;
            document.getElementById('products-updated').textContent = stats.last_sync.products_updated;
        }

        // Calculate next sync time (30 minutes from last sync)
        if (stats.last_sync) {
            const nextSync = new Date(stats.last_sync.sync_time);
            nextSync.setMinutes(nextSync.getMinutes() + 30);
            const timeUntilNext = Math.max(0, nextSync.getTime() - new Date().getTime());
            const minutesUntilNext = Math.ceil(timeUntilNext / (1000 * 60));
            document.getElementById('next-sync-time').textContent = 
                minutesUntilNext > 0 ? `In ${minutesUntilNext} minutes` : 'Starting soon...';
        }
    }

    updateSyncLogs(logs) {
        const container = document.getElementById('sync-logs');
        container.innerHTML = logs.map(log => `
            <div class="log-item">
                <div class="log-info">
                    <p class="log-message">Sync ${log.status}</p>
                    <p class="log-details">
                        Updated: ${log.products_updated}, Added: ${log.products_added}, Errors: ${log.errors}
                    </p>
                </div>
                <div class="log-time">${new Date(log.sync_time).toLocaleString()}</div>
            </div>
        `).join('');
    }

    async triggerManualSync() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/sync-inventory', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ force: true })
            });
            
            const result = await response.json();
            if (result.status === 'success') {
                this.showSuccess('Inventory sync completed successfully');
                await this.loadInventoryData();
            } else {
                this.showError('Inventory sync failed');
            }
        } catch (error) {
            console.error('Error triggering sync:', error);
            this.showError('Failed to trigger inventory sync');
        } finally {
            this.showLoading(false);
        }
    }

    handleActionClick(button) {
        const action = button.dataset.action;
        const id = button.dataset.id;
        
        switch (action) {
            case 'edit':
                this.editProduct(id);
                break;
            case 'view':
                this.viewProduct(id);
                break;
            case 'delete':
                this.deleteProduct(id);
                break;
            case 'view-order':
                this.viewOrder(id);
                break;
            case 'edit-order':
                this.editOrder(id);
                break;
        }
    }

    editProduct(id) {
        // Implementation for editing product
        console.log('Edit product:', id);
    }

    viewProduct(id) {
        // Implementation for viewing product
        console.log('View product:', id);
    }

    deleteProduct(id) {
        if (confirm('Are you sure you want to delete this product?')) {
            // Implementation for deleting product
            console.log('Delete product:', id);
        }
    }

    viewOrder(id) {
        // Implementation for viewing order
        console.log('View order:', id);
    }

    editOrder(id) {
        // Implementation for editing order
        console.log('Edit order:', id);
    }

    saveSettings() {
        // Implementation for saving settings
        this.showSuccess('Settings saved successfully');
    }

    handleFilterChange(select) {
        // Implementation for filter changes
        console.log('Filter changed:', select.value);
    }

    startAutoRefresh() {
        // Refresh dashboard data every 5 minutes
        setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.loadDashboardData();
            }
        }, 300000); // 5 minutes
    }

    showLoading(show) {
        // Implementation for loading state
        if (show) {
            document.body.style.cursor = 'wait';
        } else {
            document.body.style.cursor = 'default';
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `admin-notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            border-radius: 0.5rem;
            color: white;
            font-weight: 500;
            z-index: 9999;
            animation: slideInFromRight 0.3s ease-out;
        `;
        
        switch (type) {
            case 'success':
                notification.style.background = 'var(--admin-success)';
                break;
            case 'error':
                notification.style.background = 'var(--admin-danger)';
                break;
            default:
                notification.style.background = 'var(--admin-info)';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideInFromRight 0.3s ease-out reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Initialize admin dashboard
document.addEventListener('DOMContentLoaded', () => {
    new AdminDashboard();
});