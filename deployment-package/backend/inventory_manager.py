#!/usr/bin/env python3
"""
Automated Inventory Management System for Drop Shipping Site
Author: MiniMax Agent

This system automatically scrapes product data from the source site (ENGWE)
and keeps the drop shipping inventory updated in real-time.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
import time
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/inventory_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Product:
    """Product data model"""
    id: str
    name: str
    description: str
    price: float
    original_price: Optional[float]
    image_url: str
    category: List[str]
    colors: List[str]
    availability: str
    specifications: Dict
    rating: Optional[float]
    reviews_count: Optional[int]
    source_url: str
    last_updated: str
    
class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        self.db_path = db_path
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    original_price REAL,
                    image_url TEXT,
                    category TEXT,
                    colors TEXT,
                    availability TEXT,
                    specifications TEXT,
                    rating REAL,
                    reviews_count INTEGER,
                    source_url TEXT,
                    last_updated TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    products_updated INTEGER,
                    products_added INTEGER,
                    errors INTEGER,
                    status TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT,
                    price REAL,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
    
    def save_product(self, product: Product):
        """Save or update a product in the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO products 
                (id, name, description, price, original_price, image_url, category, 
                 colors, availability, specifications, rating, reviews_count, 
                 source_url, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product.id, product.name, product.description, product.price,
                product.original_price, product.image_url, json.dumps(product.category),
                json.dumps(product.colors), product.availability, 
                json.dumps(product.specifications), product.rating, 
                product.reviews_count, product.source_url, product.last_updated
            ))
            
            # Record price history
            conn.execute("""
                INSERT INTO price_history (product_id, price)
                VALUES (?, ?)
            """, (product.id, product.price))
    
    def get_products(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get products from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM products 
                ORDER BY last_updated DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            products = []
            for row in cursor.fetchall():
                product = dict(row)
                product['category'] = json.loads(product['category'])
                product['colors'] = json.loads(product['colors'])
                product['specifications'] = json.loads(product['specifications'])
                products.append(product)
            
            return products
    
    def log_sync(self, updated: int, added: int, errors: int, status: str):
        """Log synchronization results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sync_logs (products_updated, products_added, errors, status)
                VALUES (?, ?, ?, ?)
            """, (updated, added, errors, status))

class InventoryScraper:
    """Scrapes inventory data from source websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_engwe_products(self) -> List[Product]:
        """Scrape products from ENGWE website"""
        try:
            logger.info("Starting ENGWE product scraping...")
            
            # Get main page
            response = self.session.get("https://engwe.com/")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Find product containers
            product_elements = soup.find_all('div', class_=['product-item', 'product-card', 'grid-product'])
            
            for element in product_elements:
                try:
                    product = self.parse_product_element(element)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing product element: {e}")
                    continue
            
            # Also scrape specific product pages
            product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
            
            for link in product_links[:20]:  # Limit to avoid overwhelming
                try:
                    product_url = f"https://engwe.com{link['href']}"
                    product = self.scrape_product_details(product_url)
                    if product and not any(p.id == product.id for p in products):
                        products.append(product)
                except Exception as e:
                    logger.error(f"Error scraping product details: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(products)} products from ENGWE")
            return products
            
        except Exception as e:
            logger.error(f"Error scraping ENGWE: {e}")
            return []
    
    def parse_product_element(self, element) -> Optional[Product]:
        """Parse a product element from the page"""
        try:
            # Extract product information
            name_elem = element.find(['h3', 'h4', '.product-title', '.product-name'])
            name = name_elem.get_text(strip=True) if name_elem else "Unknown Product"
            
            # Generate ID from name
            product_id = name.lower().replace(' ', '-').replace('.', '')
            
            # Extract price
            price_elem = element.find(['span', 'div'], class_=['price', 'product-price'])
            price = self.extract_price(price_elem.get_text() if price_elem else "0")
            
            # Extract image
            img_elem = element.find('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            if image_url and not image_url.startswith('http'):
                image_url = f"https://engwe.com{image_url}"
            
            # Extract description
            desc_elem = element.find(['p', '.product-description', '.product-summary'])
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return Product(
                id=product_id,
                name=name,
                description=description,
                price=price,
                original_price=None,
                image_url=image_url,
                category=['e-bike'],
                colors=[],
                availability='in-stock',
                specifications={},
                rating=None,
                reviews_count=None,
                source_url="https://engwe.com/",
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error parsing product element: {e}")
            return None
    
    def scrape_product_details(self, url: str) -> Optional[Product]:
        """Scrape detailed product information from product page"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract detailed product information
            name_elem = soup.find(['h1', '.product-title', '.product-name'])
            name = name_elem.get_text(strip=True) if name_elem else "Unknown Product"
            
            product_id = name.lower().replace(' ', '-').replace('.', '')
            
            # Extract price with more precision
            price_elem = soup.find(['span', 'div'], class_=['price', 'product-price', 'current-price'])
            price = self.extract_price(price_elem.get_text() if price_elem else "0")
            
            # Extract original price
            original_price_elem = soup.find(['span', 'div'], class_=['original-price', 'compare-price'])
            original_price = self.extract_price(original_price_elem.get_text() if original_price_elem else "0") if original_price_elem else None
            
            # Extract description
            desc_elem = soup.find(['div', '.product-description', '.product-content'])
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract specifications
            specs = {}
            spec_elements = soup.find_all(['li', 'tr'], string=lambda x: x and ':' in x)
            for spec in spec_elements:
                spec_text = spec.get_text(strip=True)
                if ':' in spec_text:
                    key, value = spec_text.split(':', 1)
                    specs[key.strip()] = value.strip()
            
            # Extract colors/variants
            color_elements = soup.find_all(['span', 'div'], class_=['color', 'variant', 'option'])
            colors = [elem.get_text(strip=True) for elem in color_elements if elem.get_text(strip=True)]
            
            # Extract categories
            breadcrumb = soup.find(['nav', '.breadcrumb', '.navigation'])
            categories = ['e-bike']
            if breadcrumb:
                category_links = breadcrumb.find_all('a')
                for link in category_links:
                    category = link.get_text(strip=True).lower()
                    if category not in ['home', 'products'] and category:
                        categories.append(category)
            
            return Product(
                id=product_id,
                name=name,
                description=description[:500],  # Limit description length
                price=price,
                original_price=original_price,
                image_url=self.extract_main_image(soup),
                category=categories,
                colors=colors[:5],  # Limit colors
                availability='in-stock',
                specifications=specs,
                rating=self.extract_rating(soup),
                reviews_count=self.extract_review_count(soup),
                source_url=url,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error scraping product details from {url}: {e}")
            return None
    
    def extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        import re
        # Remove currency symbols and extract number
        price_match = re.search(r'([0-9,]+\.?[0-9]*)', price_text.replace(',', ''))
        return float(price_match.group(1)) if price_match else 0.0
    
    def extract_main_image(self, soup) -> str:
        """Extract main product image URL"""
        img_selectors = [
            '.product-image img',
            '.product-gallery img',
            '.main-image img',
            'img[data-src]',
            'img'
        ]
        
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img:
                src = img.get('data-src') or img.get('src', '')
                if src and not src.startswith('data:'):
                    if not src.startswith('http'):
                        src = f"https://engwe.com{src}"
                    return src
        
        return ''
    
    def extract_rating(self, soup) -> Optional[float]:
        """Extract product rating"""
        rating_elem = soup.find(['span', 'div'], class_=['rating', 'stars', 'review-rating'])
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            import re
            rating_match = re.search(r'([0-9]\.?[0-9]*)', rating_text)
            if rating_match:
                return float(rating_match.group(1))
        return None
    
    def extract_review_count(self, soup) -> Optional[int]:
        """Extract review count"""
        review_elem = soup.find(['span', 'div'], string=lambda x: x and 'review' in x.lower())
        if review_elem:
            review_text = review_elem.get_text(strip=True)
            import re
            count_match = re.search(r'([0-9]+)', review_text)
            if count_match:
                return int(count_match.group(1))
        return None

class InventoryManager:
    """Main inventory management system"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = InventoryScraper()
        self.is_running = False
    
    def sync_inventory(self) -> Dict:
        """Synchronize inventory from source sites"""
        logger.info("Starting inventory synchronization...")
        
        try:
            # Scrape products from ENGWE
            products = self.scraper.scrape_engwe_products()
            
            updated_count = 0
            added_count = 0
            error_count = 0
            
            for product in products:
                try:
                    # Check if product exists
                    existing_products = self.db.get_products()
                    existing_ids = [p['id'] for p in existing_products]
                    
                    if product.id in existing_ids:
                        updated_count += 1
                    else:
                        added_count += 1
                    
                    self.db.save_product(product)
                    
                except Exception as e:
                    logger.error(f"Error saving product {product.id}: {e}")
                    error_count += 1
            
            # Log synchronization results
            status = "success" if error_count == 0 else "partial_success"
            self.db.log_sync(updated_count, added_count, error_count, status)
            
            result = {
                "status": status,
                "products_updated": updated_count,
                "products_added": added_count,
                "errors": error_count,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Inventory sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during inventory sync: {e}")
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.db.log_sync(0, 0, 1, "error")
            return error_result
    
    def start_scheduled_sync(self):
        """Start scheduled inventory synchronization"""
        logger.info("Starting scheduled inventory synchronization...")
        
        # Initialize APScheduler
        self.scheduler = BackgroundScheduler()
        
        # Schedule sync every 30 minutes
        self.scheduler.add_job(
            func=self.sync_inventory,
            trigger="interval",
            minutes=30,
            id='inventory_sync'
        )
        
        # Schedule daily comprehensive sync
        self.scheduler.add_job(
            func=self.comprehensive_sync,
            trigger="cron",
            hour=2,
            minute=0,
            id='comprehensive_sync'
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Scheduled synchronization started")
    
    def comprehensive_sync(self):
        """Perform comprehensive synchronization with additional checks"""
        logger.info("Starting comprehensive inventory sync...")
        
        # Sync inventory
        result = self.sync_inventory()
        
        # Additional tasks for comprehensive sync
        self.cleanup_old_price_history()
        self.check_price_changes()
        
        return result
    
    def cleanup_old_price_history(self):
        """Clean up old price history records"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    DELETE FROM price_history 
                    WHERE recorded_at < ?
                """, (cutoff_date,))
            logger.info("Cleaned up old price history records")
        except Exception as e:
            logger.error(f"Error cleaning up price history: {e}")
    
    def check_price_changes(self):
        """Check for significant price changes"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT p.id, p.name, p.price, 
                           AVG(ph.price) as avg_price
                    FROM products p
                    JOIN price_history ph ON p.id = ph.product_id
                    WHERE ph.recorded_at > datetime('now', '-7 days')
                    GROUP BY p.id, p.name, p.price
                """)
                
                for row in cursor.fetchall():
                    current_price = row['price']
                    avg_price = row['avg_price']
                    
                    if avg_price > 0:
                        change_percent = abs((current_price - avg_price) / avg_price) * 100
                        
                        if change_percent > 10:  # More than 10% change
                            logger.info(f"Significant price change detected: {row['name']} - {change_percent:.1f}%")
            
        except Exception as e:
            logger.error(f"Error checking price changes: {e}")
    
    def get_inventory_stats(self) -> Dict:
        """Get inventory statistics"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get product count
                total_products = conn.execute("SELECT COUNT(*) as count FROM products").fetchone()['count']
                
                # Get recent sync info
                recent_sync = conn.execute("""
                    SELECT * FROM sync_logs 
                    ORDER BY sync_time DESC 
                    LIMIT 1
                """).fetchone()
                
                # Get price range
                price_stats = conn.execute("""
                    SELECT MIN(price) as min_price, MAX(price) as max_price, AVG(price) as avg_price
                    FROM products
                """).fetchone()
                
                return {
                    "total_products": total_products,
                    "last_sync": dict(recent_sync) if recent_sync else None,
                    "price_range": {
                        "min": price_stats['min_price'],
                        "max": price_stats['max_price'],
                        "average": price_stats['avg_price']
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting inventory stats: {e}")
            return {}
    
    def stop(self):
        """Stop the inventory manager"""
        self.is_running = False
        if hasattr(self, 'scheduler'):
            self.scheduler.shutdown()
        logger.info("Inventory manager stopped")

if __name__ == "__main__":
    # Initialize and start inventory manager
    manager = InventoryManager()
    
    # Perform initial sync
    logger.info("Performing initial inventory sync...")
    result = manager.sync_inventory()
    print(f"Initial sync result: {result}")
    
    # Start scheduled synchronization
    manager.start_scheduled_sync()
    
    # Print inventory stats
    stats = manager.get_inventory_stats()
    print(f"Inventory stats: {stats}")
    
    try:
        # Keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down inventory manager...")
        manager.stop()