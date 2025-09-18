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
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
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
    
    def get_products(self, limit: int = 1000, offset: int = 0) -> List[Dict]:
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
    
    def get_all_products(self) -> List[Dict]:
        """Get ALL products from database without limit"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM products 
                ORDER BY last_updated DESC
            """)
            
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
        """Scrape ALL products from ENGWE website with real-time stock"""
        try:
            logger.info("Starting comprehensive ENGWE product scraping...")
            all_products = []
            
            # Get all product URLs by exploring the sitemap and category pages
            product_urls = self.discover_all_product_urls()
            
            logger.info(f"Discovered {len(product_urls)} product URLs to scrape")
            
            # Scrape each product page for complete information
            for i, product_url in enumerate(product_urls):
                try:
                    logger.info(f"Scraping product {i+1}/{len(product_urls)}: {product_url}")
                    product = self.scrape_product_details_with_stock(product_url)
                    if product:
                        all_products.append(product)
                        
                    # Add small delay to be respectful to the server
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error scraping product {product_url}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(all_products)} products from ENGWE")
            return all_products
            
        except Exception as e:
            logger.error(f"Error scraping ENGWE: {e}")
            return []
    
    def discover_all_product_urls(self) -> List[str]:
        """Discover all product URLs from ENGWE website"""
        product_urls = set()
        
        try:
            # Start with main pages
            base_urls = [
                "https://engwe.com/",
                "https://engwe.com/collections/all-products",
                "https://engwe.com/collections/ebikes",
                "https://engwe.com/collections/accessories"
            ]
            
            for base_url in base_urls:
                try:
                    logger.info(f"Exploring page: {base_url}")
                    response = self.session.get(base_url)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all product links
                    links = soup.find_all('a', href=lambda x: x and '/products/' in x)
                    for link in links:
                        href = link.get('href', '')
                        if href.startswith('/'):
                            product_url = f"https://engwe.com{href}"
                        elif href.startswith('http'):
                            product_url = href
                        else:
                            continue
                            
                        # Clean URL (remove parameters)
                        if '?' in product_url:
                            product_url = product_url.split('?')[0]
                            
                        product_urls.add(product_url)
                    
                    # Check for pagination
                    pagination_urls = self.get_pagination_urls(soup, base_url)
                    for page_url in pagination_urls:
                        try:
                            logger.info(f"Exploring pagination: {page_url}")
                            page_response = self.session.get(page_url)
                            page_response.raise_for_status()
                            
                            page_soup = BeautifulSoup(page_response.content, 'html.parser')
                            page_links = page_soup.find_all('a', href=lambda x: x and '/products/' in x)
                            
                            for link in page_links:
                                href = link.get('href', '')
                                if href.startswith('/'):
                                    product_url = f"https://engwe.com{href}"
                                elif href.startswith('http'):
                                    product_url = href
                                else:
                                    continue
                                    
                                if '?' in product_url:
                                    product_url = product_url.split('?')[0]
                                    
                                product_urls.add(product_url)
                                
                            time.sleep(0.3)  # Be respectful
                            
                        except Exception as e:
                            logger.error(f"Error exploring pagination {page_url}: {e}")
                            continue
                    
                    time.sleep(0.3)  # Be respectful
                    
                except Exception as e:
                    logger.error(f"Error exploring {base_url}: {e}")
                    continue
            
            # Try to get sitemap if available
            try:
                sitemap_response = self.session.get("https://engwe.com/sitemap.xml")
                if sitemap_response.status_code == 200:
                    sitemap_soup = BeautifulSoup(sitemap_response.content, 'xml')
                    urls = sitemap_soup.find_all('url')
                    for url in urls:
                        loc = url.find('loc')
                        if loc and '/products/' in loc.text:
                            product_urls.add(loc.text)
            except:
                pass  # Sitemap not available or accessible
            
            return list(product_urls)
            
        except Exception as e:
            logger.error(f"Error discovering product URLs: {e}")
            return []
    
    def get_pagination_urls(self, soup, base_url: str) -> List[str]:
        """Extract pagination URLs from a page"""
        pagination_urls = []
        
        # Look for pagination elements
        pagination_selectors = [
            '.pagination a',
            '.paginate a',
            '.page-numbers a',
            'a[href*="page="]'
        ]
        
        for selector in pagination_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if href and ('page=' in href or 'page/' in href):
                    if href.startswith('/'):
                        page_url = f"https://engwe.com{href}"
                    elif href.startswith('http'):
                        page_url = href
                    else:
                        continue
                    pagination_urls.append(page_url)
        
        return list(set(pagination_urls))  # Remove duplicates
    
    def scrape_product_details_with_stock(self, url: str) -> Optional[Product]:
        """Scrape detailed product information with real-time stock status"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract detailed product information
            name_elem = soup.find(['h1', '.product-title', '.product-name'])
            name = name_elem.get_text(strip=True) if name_elem else "Unknown Product"
            
            # Skip if not a valid product
            if not name or name == "Unknown Product":
                return None
            
            product_id = name.lower().replace(' ', '-').replace('.', '').replace('/', '-')
            
            # Extract price with more precision
            price_elem = soup.find(['span', 'div'], class_=['price', 'product-price', 'current-price', 'money'])
            price = self.extract_price(price_elem.get_text() if price_elem else "0")
            
            # Extract original price
            original_price_elem = soup.find(['span', 'div'], class_=['original-price', 'compare-price', 'was-price'])
            original_price = self.extract_price(original_price_elem.get_text() if original_price_elem else "0") if original_price_elem else None
            
            # Extract real-time stock information
            stock_status = self.get_real_time_stock(soup)
            
            # Extract description
            desc_elem = soup.find(['div', '.product-description', '.product-content', '.rte'])
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract specifications
            specs = self.extract_detailed_specs(soup)
            
            # Extract colors/variants
            colors = self.extract_color_variants(soup)
            
            # Extract categories
            categories = self.extract_categories(soup)
            
            # Extract rating and reviews
            rating = self.extract_rating(soup)
            review_count = self.extract_review_count(soup)
            
            # Extract high-quality images
            image_url = self.extract_main_image(soup)
            
            return Product(
                id=product_id,
                name=name,
                description=description[:1000],  # Increased description length
                price=price,
                original_price=original_price,
                image_url=image_url,
                category=categories,
                colors=colors,
                availability=stock_status,
                specifications=specs,
                rating=rating,
                reviews_count=review_count,
                source_url=url,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error scraping product details from {url}: {e}")
            return None
    
    def get_real_time_stock(self, soup) -> str:
        """Extract real-time stock information"""
        # Look for stock indicators
        stock_indicators = [
            '.stock-status',
            '.inventory-status',
            '.availability',
            '.product-availability',
            '.in-stock',
            '.out-of-stock',
            '.stock-level'
        ]
        
        for indicator in stock_indicators:
            elem = soup.select_one(indicator)
            if elem:
                stock_text = elem.get_text(strip=True).lower()
                if any(word in stock_text for word in ['out of stock', 'sold out', 'unavailable']):
                    return 'out-of-stock'
                elif any(word in stock_text for word in ['in stock', 'available', 'ready']):
                    return 'in-stock'
                elif any(word in stock_text for word in ['limited', 'few left', 'low stock']):
                    return 'limited-stock'
        
        # Check for add to cart button
        add_to_cart = soup.find(['button', 'input'], class_=['add-to-cart', 'btn-cart', 'product-form__cart-submit'])
        if add_to_cart:
            if add_to_cart.get('disabled') or 'disabled' in add_to_cart.get('class', []):
                return 'out-of-stock'
            button_text = add_to_cart.get_text(strip=True).lower()
            if 'add to cart' in button_text or 'buy now' in button_text:
                return 'in-stock'
            elif 'notify' in button_text or 'sold out' in button_text:
                return 'out-of-stock'
        
        # Check for variant selectors (if product has variants, it's likely in stock)
        variant_selectors = soup.find_all(['select', 'input'], {'name': lambda x: x and 'variant' in x.lower()})
        if variant_selectors:
            return 'in-stock'
        
        # Default to in-stock if no clear indicators
        return 'in-stock'
    
    def extract_detailed_specs(self, soup) -> Dict:
        """Extract detailed product specifications"""
        specs = {}
        
        # Look for specification tables
        spec_tables = soup.find_all(['table', 'dl'], class_=['specs', 'specifications', 'product-specs'])
        for table in spec_tables:
            rows = table.find_all(['tr', 'dt'])
            for row in rows:
                if row.name == 'tr':
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            specs[key] = value
                elif row.name == 'dt':
                    key = row.get_text(strip=True)
                    dd = row.find_next_sibling('dd')
                    if dd:
                        value = dd.get_text(strip=True)
                        if key and value:
                            specs[key] = value
        
        # Look for spec lists
        spec_lists = soup.find_all(['ul', 'ol'], class_=['specs', 'specifications', 'features'])
        for spec_list in spec_lists:
            items = spec_list.find_all('li')
            for item in items:
                item_text = item.get_text(strip=True)
                if ':' in item_text:
                    key, value = item_text.split(':', 1)
                    specs[key.strip()] = value.strip()
                elif item_text:
                    specs[f"Feature {len(specs) + 1}"] = item_text
        
        # Look for individual spec elements
        spec_elements = soup.find_all(['span', 'div', 'p'], string=lambda x: x and ':' in x)
        for elem in spec_elements:
            text = elem.get_text(strip=True)
            if ':' in text and len(text) < 100:  # Avoid long descriptions
                key, value = text.split(':', 1)
                specs[key.strip()] = value.strip()
        
        return specs
    
    def extract_color_variants(self, soup) -> List[str]:
        """Extract color/variant options"""
        colors = []
        
        # Look for color selectors
        color_selectors = [
            '.color-swatch',
            '.variant-option',
            '.product-option',
            '.swatch',
            'input[type="radio"][name*="color"]',
            'select option[value*="color"]'
        ]
        
        for selector in color_selectors:
            elements = soup.select(selector)
            for elem in elements:
                if elem.name == 'option':
                    color = elem.get_text(strip=True)
                elif elem.name == 'input':
                    color = elem.get('value', '')
                else:
                    color = elem.get('title', '') or elem.get('data-value', '') or elem.get_text(strip=True)
                
                if color and color.lower() not in ['default', 'select', 'choose']:
                    colors.append(color)
        
        # Look for variant labels
        variant_labels = soup.find_all(['label', 'span'], string=lambda x: x and any(c in x.lower() for c in ['black', 'white', 'red', 'blue', 'green', 'grey', 'silver']))
        for label in variant_labels:
            color = label.get_text(strip=True)
            if color and len(color) < 30:  # Avoid long descriptions
                colors.append(color)
        
        return list(set(colors))[:10]  # Remove duplicates and limit
    
    def extract_categories(self, soup) -> List[str]:
        """Extract product categories"""
        categories = ['e-bike']  # Default category
        
        # Look for breadcrumbs
        breadcrumb = soup.find(['nav', '.breadcrumb', '.breadcrumbs'])
        if breadcrumb:
            links = breadcrumb.find_all('a')
            for link in links:
                category = link.get_text(strip=True).lower()
                if category not in ['home', 'products', 'shop'] and category:
                    categories.append(category)
        
        # Look for category tags or labels
        category_elements = soup.find_all(['span', 'div'], class_=['category', 'tag', 'product-type'])
        for elem in category_elements:
            category = elem.get_text(strip=True).lower()
            if category and category not in categories:
                categories.append(category)
        
        return categories[:5]  # Limit categories
    
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
                    existing_products = self.db.get_all_products()
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
        """Start scheduled inventory synchronization with real-time stock updates"""
        logger.info("Starting scheduled inventory synchronization with real-time stock monitoring...")
        
        # Initialize APScheduler
        self.scheduler = BackgroundScheduler()
        
        # Schedule comprehensive sync every 15 minutes (increased frequency for real-time stock)
        self.scheduler.add_job(
            func=self.sync_inventory,
            trigger="interval",
            minutes=15,
            id='inventory_sync'
        )
        
        # Schedule stock-only updates every 5 minutes
        self.scheduler.add_job(
            func=self.quick_stock_update,
            trigger="interval",
            minutes=5,
            id='stock_update'
        )
        
        # Schedule daily comprehensive sync with full product discovery
        self.scheduler.add_job(
            func=self.comprehensive_sync,
            trigger="cron",
            hour=2,
            minute=0,
            id='comprehensive_sync'
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Scheduled synchronization with real-time stock monitoring started")
    
    def quick_stock_update(self):
        """Quick stock status update for existing products"""
        logger.info("Starting quick stock status update...")
        
        try:
            # Get existing products
            existing_products = self.db.get_products(limit=1000)  # Get more products
            
            updated_count = 0
            
            for product in existing_products:
                try:
                    # Check stock for existing product
                    response = self.scraper.session.get(product['source_url'])
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        new_stock_status = self.scraper.get_real_time_stock(soup)
                        
                        # Update if stock status changed
                        if new_stock_status != product['availability']:
                            with sqlite3.connect(self.db.db_path) as conn:
                                conn.execute("""
                                    UPDATE products 
                                    SET availability = ?, last_updated = ?
                                    WHERE id = ?
                                """, (new_stock_status, datetime.now().isoformat(), product['id']))
                            
                            updated_count += 1
                            logger.info(f"Stock updated for {product['name']}: {product['availability']} -> {new_stock_status}")
                    
                    time.sleep(0.2)  # Small delay between requests
                    
                except Exception as e:
                    logger.error(f"Error updating stock for {product['id']}: {e}")
                    continue
            
            logger.info(f"Quick stock update completed: {updated_count} products updated")
            
        except Exception as e:
            logger.error(f"Error during quick stock update: {e}")
    
    def comprehensive_sync(self):
        """Perform comprehensive synchronization with full product discovery"""
        logger.info("Starting comprehensive inventory sync with full product discovery...")
        
        # Sync all products (this will now get ALL products)
        result = self.sync_inventory()
        
        # Additional tasks for comprehensive sync
        self.cleanup_old_price_history()
        self.check_price_changes()
        self.update_product_stats()
        
        return result
    
    def update_product_stats(self):
        """Update product statistics and health check"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                # Count products by availability
                availability_stats = conn.execute("""
                    SELECT availability, COUNT(*) as count
                    FROM products
                    GROUP BY availability
                """).fetchall()
                
                logger.info("Product availability stats:")
                for status, count in availability_stats:
                    logger.info(f"  {status}: {count} products")
                
                # Check for products that haven't been updated recently
                stale_products = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM products
                    WHERE last_updated < datetime('now', '-2 hours')
                """).fetchone()[0]
                
                if stale_products > 0:
                    logger.warning(f"{stale_products} products haven't been updated in 2+ hours")
                
        except Exception as e:
            logger.error(f"Error updating product stats: {e}")
    
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