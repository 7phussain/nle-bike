# NLE Bike - Modern Drop Shipping Site

**Author:** MiniMax Agent  
**Version:** 1.0.0  
**Created:** 2025-09-18

A fully automated, modern drop shipping e-commerce site inspired by ENGWE.com with real-time inventory synchronization.

## 🚀 Features

### Frontend
- **Modern Design**: Clean, responsive UI with dark/light theme support
- **Mobile-First**: Optimized for all devices and screen sizes
- **Advanced Search**: Real-time search with filtering and categorization
- **Product Catalog**: Dynamic product grid with filters and sorting
- **Shopping Cart**: Full cart functionality with local storage
- **Product Recommendations**: AI-powered product suggestions
- **Performance Optimized**: Lazy loading, animations, and smooth transitions

### Backend
- **Automated Inventory Sync**: Real-time synchronization with source site (ENGWE)
- **RESTful API**: Complete API for all e-commerce operations
- **Price Monitoring**: Automatic price change detection and history
- **Database Management**: SQLite database with automated cleanup
- **Background Tasks**: Scheduled inventory updates and maintenance
- **Search Engine**: Advanced search with relevance scoring
- **Analytics**: Comprehensive inventory statistics and reporting

### Automation
- **Scheduled Sync**: Automatic inventory updates every 30 minutes
- **Price History**: Track price changes over time
- **Error Handling**: Robust error handling and logging
- **Health Monitoring**: API health checks and status monitoring

## 📁 Project Structure

```
electroride-pro/
├── index.html              # Main website
├── css/
│   └── style.css          # Modern responsive styles
├── js/
│   └── app.js            # Frontend JavaScript application
├── backend/
│   ├── inventory_manager.py   # Automated inventory synchronization
│   ├── api_server.py          # FastAPI backend server
│   └── requirements.txt       # Python dependencies
├── data/
│   └── inventory.db          # SQLite database
├── logs/
│   └── inventory_sync.log    # Application logs
├── setup.sh                  # Automated setup script
├── start.sh                  # Production start script
├── dev.sh                    # Development start script
└── README.md                 # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git
- Optional: Node.js and npm

### Quick Setup

1. **Clone or download the project files**

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Start the application:**
   ```bash
   # Development mode (with hot reload)
   ./dev.sh
   
   # Or production mode
   ./start.sh
   ```

4. **Access the site:**
   - Website: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Admin Stats: http://localhost:8000/api/inventory/stats

### Manual Installation

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Initialize database:**
   ```bash
   python inventory_manager.py
   ```

4. **Start the API server:**
   ```bash
   python api_server.py
   ```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
DATABASE_PATH=data/inventory.db
LOG_LEVEL=INFO
SYNC_INTERVAL_MINUTES=30
SOURCE_SITE_URL=https://engwe.com/
APP_NAME=NLE Bike
APP_VERSION=1.0.0
```

### Customization

#### Change Source Site
To scrape from a different site, modify the `scrape_engwe_products()` method in `backend/inventory_manager.py`:

```python
def scrape_your_site_products(self) -> List[Product]:
    # Implement your custom scraping logic
    pass
```

#### Styling
Customize the appearance by modifying `css/style.css`. The CSS uses CSS custom properties for easy theming:

```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #f59e0b;
  /* Add your colors */
}
```

#### Product Categories
Update product categories in `js/app.js`:

```javascript
const categories = [
    'fat-tire',
    'folding',
    'commuter',
    'motorcycle'
    // Add your categories
];
```

## 📊 API Endpoints

### Products
- `GET /api/products` - List products with filtering
- `GET /api/products/{id}` - Get specific product
- `GET /api/categories` - Get all categories
- `GET /api/search?q={query}` - Search products
- `GET /api/recommendations/{id}` - Get product recommendations

### Inventory Management
- `POST /api/sync-inventory` - Trigger inventory sync
- `GET /api/inventory/stats` - Get inventory statistics
- `GET /api/inventory/sync-logs` - Get sync history
- `GET /api/price-history/{id}` - Get price history

### Orders
- `POST /api/orders` - Create new order

### System
- `GET /api/health` - Health check

## 🔄 Automated Inventory Sync

The system automatically:

1. **Scrapes the source site** every 30 minutes
2. **Updates product information** (prices, availability, descriptions)
3. **Tracks price changes** with historical data
4. **Logs all operations** for monitoring
5. **Handles errors gracefully** with retry logic

### Sync Process

1. Fetch product pages from source site
2. Parse product information (name, price, images, etc.)
3. Compare with existing database records
4. Update changed products
5. Add new products
6. Log sync statistics
7. Clean up old data

## 🎨 Frontend Features

### Modern UI Components
- Responsive navigation with mobile menu
- Hero section with animated elements
- Product grid with hover effects
- Advanced filtering and search
- Shopping cart with persistent storage
- Product modals with detailed views
- Dark/light theme toggle
- Loading states and animations

### Performance Optimizations
- Lazy loading for images
- Debounced search input
- Efficient filtering algorithms
- Minimal DOM manipulation
- CSS animations with GPU acceleration

## 🔐 Security Considerations

- Input validation on all API endpoints
- SQL injection prevention with parameterized queries
- CORS configuration for production
- Rate limiting (implement as needed)
- Secure session handling
- Environment-based configuration

## 📈 Monitoring and Analytics

### Built-in Monitoring
- Health check endpoint
- Sync operation logging
- Error tracking and reporting
- Performance metrics
- Database statistics

### Logging
- Structured logging with timestamps
- Configurable log levels
- File and console output
- Error stack traces
- Sync operation details

## 🚀 Deployment

### Development
```bash
./dev.sh
```

### Production

1. **Using systemd (Linux):**
   ```bash
   sudo systemctl enable electroride-pro
   sudo systemctl start electroride-pro
   ```

2. **Using Docker (optional):**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r backend/requirements.txt
   EXPOSE 8000
   CMD ["python", "backend/api_server.py"]
   ```

3. **Using reverse proxy (nginx):**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill the process
   kill -9 <PID>
   ```

2. **Database permission errors:**
   ```bash
   chmod 755 data/
   chmod 644 data/inventory.db
   ```

3. **Python module not found:**
   ```bash
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```

4. **Sync not working:**
   - Check logs in `logs/inventory_sync.log`
   - Verify source site accessibility
   - Check internet connection

### Debug Mode
Enable debug mode by setting `DEBUG=true` in `.env`

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is created for educational and commercial use. Feel free to modify and distribute according to your needs.

## 🆘 Support

For support and questions:
- Check the logs in `logs/inventory_sync.log`
- Review API documentation at `/docs`
- Monitor health status at `/api/health`

## 🔮 Future Enhancements

- [ ] Multi-vendor support
- [ ] Advanced analytics dashboard
- [ ] Email notifications for price changes
- [ ] Webhook integrations
- [ ] Redis caching
- [ ] Elasticsearch integration
- [ ] Customer reviews system
- [ ] Wishlist functionality
- [ ] Multi-language support
- [ ] Payment gateway integration

---

**Created by MiniMax Agent** - A modern, automated drop shipping solution for the future of e-commerce.