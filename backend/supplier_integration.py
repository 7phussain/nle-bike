#!/usr/bin/env python3
"""
Supplier Integration and Dropshipping Apps Integration
Author: MiniMax Agent

Integrates with popular dropshipping platforms like Oberlo, Spocket, CJ Dropshipping, etc.
"""

import os
import json
import asyncio
import aiohttp
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET
import csv
import io

logger = logging.getLogger(__name__)

@dataclass
class SupplierProduct:
    supplier_id: str
    supplier_sku: str
    name: str
    description: str
    price: float
    cost: float
    category: str
    images: List[str]
    variants: List[Dict]
    stock_quantity: int
    shipping_info: Dict
    supplier_name: str
    last_updated: str

@dataclass
class DropshipOrder:
    order_id: str
    supplier_order_id: str
    customer_info: Dict
    shipping_address: Dict
    items: List[Dict]
    total_amount: float
    cost_amount: float
    profit: float
    status: str
    tracking_number: Optional[str]
    created_at: str
    updated_at: str

class SupplierIntegration(ABC):
    """Abstract base class for supplier integrations"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def get_products(self, category: str = None, limit: int = 100) -> List[SupplierProduct]:
        """Get products from supplier"""
        pass
    
    @abstractmethod
    async def get_product_details(self, supplier_sku: str) -> Optional[SupplierProduct]:
        """Get detailed product information"""
        pass
    
    @abstractmethod
    async def place_order(self, order_data: Dict) -> Dict:
        """Place order with supplier"""
        pass
    
    @abstractmethod
    async def get_order_status(self, supplier_order_id: str) -> Dict:
        """Get order status from supplier"""
        pass
    
    @abstractmethod
    async def get_tracking_info(self, supplier_order_id: str) -> Dict:
        """Get tracking information"""
        pass

class ENGWEIntegration(SupplierIntegration):
    """Integration with ENGWE as a supplier"""
    
    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.base_url = "https://engwe.com"
        self.session = aiohttp.ClientSession()
    
    async def get_products(self, category: str = None, limit: int = 100) -> List[SupplierProduct]:
        """Scrape products from ENGWE website"""
        try:
            # This would use the existing inventory scraper
            from inventory_manager import InventoryScraper
            
            scraper = InventoryScraper()
            products_data = scraper.scrape_engwe_products()
            
            supplier_products = []
            for product in products_data[:limit]:
                supplier_product = SupplierProduct(
                    supplier_id="engwe",
                    supplier_sku=product.id,
                    name=product.name,
                    description=product.description,
                    price=float(product.price) * 1.3,  # Add 30% markup
                    cost=float(product.price),
                    category=product.category[0] if product.category else "e-bike",
                    images=[product.image_url],
                    variants=[],
                    stock_quantity=10,  # Assume in stock
                    shipping_info={"method": "standard", "cost": 0, "time": "5-7 days"},
                    supplier_name="ENGWE",
                    last_updated=product.last_updated
                )
                supplier_products.append(supplier_product)
            
            return supplier_products
            
        except Exception as e:
            logger.error(f"Error getting products from ENGWE: {e}")
            return []
    
    async def get_product_details(self, supplier_sku: str) -> Optional[SupplierProduct]:
        """Get detailed product information from ENGWE"""
        try:
            # This would fetch detailed product info
            products = await self.get_products()
            for product in products:
                if product.supplier_sku == supplier_sku:
                    return product
            return None
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return None
    
    async def place_order(self, order_data: Dict) -> Dict:
        """Place order with ENGWE (simulated)"""
        try:
            # In a real integration, this would place an actual order
            # For now, we simulate the order placement
            
            supplier_order_id = f"ENGWE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Simulate order processing delay
            await asyncio.sleep(1)
            
            return {
                'success': True,
                'supplier_order_id': supplier_order_id,
                'status': 'confirmed',
                'estimated_delivery': '5-7 business days',
                'message': 'Order placed successfully with ENGWE'
            }
            
        except Exception as e:
            logger.error(f"Error placing order with ENGWE: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_order_status(self, supplier_order_id: str) -> Dict:
        """Get order status from ENGWE"""
        # Simulate order status
        statuses = ['confirmed', 'processing', 'shipped', 'delivered']
        import random
        
        return {
            'supplier_order_id': supplier_order_id,
            'status': random.choice(statuses),
            'tracking_number': f"TRK{supplier_order_id[-8:]}" if random.choice([True, False]) else None,
            'last_updated': datetime.now().isoformat()
        }
    
    async def get_tracking_info(self, supplier_order_id: str) -> Dict:
        """Get tracking information from ENGWE"""
        tracking_number = f"TRK{supplier_order_id[-8:]}"
        
        return {
            'tracking_number': tracking_number,
            'status': 'in_transit',
            'location': 'Warehouse - Germany',
            'estimated_delivery': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'tracking_url': f"https://track.engwe.com/{tracking_number}"
        }

class SpocketIntegration(SupplierIntegration):
    """Integration with Spocket API"""
    
    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = "https://api.spocket.co/api/v1"
    
    async def get_products(self, category: str = None, limit: int = 100) -> List[SupplierProduct]:
        """Get products from Spocket API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'limit': limit,
                'category': category
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/products", headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        products = []
                        
                        for item in data.get('data', []):
                            product = SupplierProduct(
                                supplier_id="spocket",
                                supplier_sku=item['id'],
                                name=item['title'],
                                description=item['description'],
                                price=float(item['retail_price']),
                                cost=float(item['cost']),
                                category=item.get('category', 'general'),
                                images=item.get('images', []),
                                variants=item.get('variants', []),
                                stock_quantity=item.get('inventory', 0),
                                shipping_info=item.get('shipping', {}),
                                supplier_name="Spocket",
                                last_updated=datetime.now().isoformat()
                            )
                            products.append(product)
                        
                        return products
                    else:
                        logger.error(f"Spocket API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting products from Spocket: {e}")
            return []
    
    async def get_product_details(self, supplier_sku: str) -> Optional[SupplierProduct]:
        """Get detailed product information from Spocket"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/products/{supplier_sku}", headers=headers) as response:
                    if response.status == 200:
                        item = await response.json()
                        
                        return SupplierProduct(
                            supplier_id="spocket",
                            supplier_sku=item['id'],
                            name=item['title'],
                            description=item['description'],
                            price=float(item['retail_price']),
                            cost=float(item['cost']),
                            category=item.get('category', 'general'),
                            images=item.get('images', []),
                            variants=item.get('variants', []),
                            stock_quantity=item.get('inventory', 0),
                            shipping_info=item.get('shipping', {}),
                            supplier_name="Spocket",
                            last_updated=datetime.now().isoformat()
                        )
                    return None
        except Exception as e:
            logger.error(f"Error getting product details from Spocket: {e}")
            return None
    
    async def place_order(self, order_data: Dict) -> Dict:
        """Place order with Spocket"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            order_payload = {
                'line_items': order_data['items'],
                'shipping_address': order_data['shipping_address'],
                'note': f"Order from ElectroRide Pro - {order_data['order_id']}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/orders", headers=headers, json=order_payload) as response:
                    if response.status == 201:
                        result = await response.json()
                        return {
                            'success': True,
                            'supplier_order_id': result['id'],
                            'status': result['status'],
                            'message': 'Order placed successfully with Spocket'
                        }
                    else:
                        error_data = await response.json()
                        return {
                            'success': False,
                            'error': error_data.get('message', 'Unknown error')
                        }
        except Exception as e:
            logger.error(f"Error placing order with Spocket: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_order_status(self, supplier_order_id: str) -> Dict:
        """Get order status from Spocket"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/orders/{supplier_order_id}", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'supplier_order_id': supplier_order_id,
                            'status': data['status'],
                            'tracking_number': data.get('tracking_number'),
                            'last_updated': data.get('updated_at')
                        }
            return {}
        except Exception as e:
            logger.error(f"Error getting order status from Spocket: {e}")
            return {}
    
    async def get_tracking_info(self, supplier_order_id: str) -> Dict:
        """Get tracking information from Spocket"""
        try:
            order_status = await self.get_order_status(supplier_order_id)
            tracking_number = order_status.get('tracking_number')
            
            if tracking_number:
                return {
                    'tracking_number': tracking_number,
                    'status': 'shipped',
                    'tracking_url': f"https://track.spocket.co/{tracking_number}"
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting tracking info from Spocket: {e}")
            return {}

class CJDropshippingIntegration(SupplierIntegration):
    """Integration with CJ Dropshipping API"""
    
    def __init__(self, config: Dict[str, str]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = "https://developers.cjdropshipping.com/api2.0/v1"
    
    async def get_products(self, category: str = None, limit: int = 100) -> List[SupplierProduct]:
        """Get products from CJ Dropshipping API"""
        try:
            headers = {
                'CJ-Access-Token': self.api_key,
                'Content-Type': 'application/json'
            }
            
            params = {
                'pageSize': limit,
                'categoryId': category
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/products/list", headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        products = []
                        
                        for item in data.get('data', []):
                            product = SupplierProduct(
                                supplier_id="cj_dropshipping",
                                supplier_sku=item['pid'],
                                name=item['productName'],
                                description=item.get('description', ''),
                                price=float(item['sellPrice']),
                                cost=float(item['sourcePrice']),
                                category=item.get('categoryName', 'general'),
                                images=item.get('productImage', []),
                                variants=item.get('variants', []),
                                stock_quantity=item.get('stockQuantity', 0),
                                shipping_info=item.get('shippingInfo', {}),
                                supplier_name="CJ Dropshipping",
                                last_updated=datetime.now().isoformat()
                            )
                            products.append(product)
                        
                        return products
                    return []
        except Exception as e:
            logger.error(f"Error getting products from CJ Dropshipping: {e}")
            return []
    
    async def get_product_details(self, supplier_sku: str) -> Optional[SupplierProduct]:
        """Get detailed product information from CJ Dropshipping"""
        try:
            headers = {
                'CJ-Access-Token': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/products/query", headers=headers, params={'pid': supplier_sku}) as response:
                    if response.status == 200:
                        data = await response.json()
                        item = data.get('data')
                        
                        if item:
                            return SupplierProduct(
                                supplier_id="cj_dropshipping",
                                supplier_sku=item['pid'],
                                name=item['productName'],
                                description=item.get('description', ''),
                                price=float(item['sellPrice']),
                                cost=float(item['sourcePrice']),
                                category=item.get('categoryName', 'general'),
                                images=item.get('productImage', []),
                                variants=item.get('variants', []),
                                stock_quantity=item.get('stockQuantity', 0),
                                shipping_info=item.get('shippingInfo', {}),
                                supplier_name="CJ Dropshipping",
                                last_updated=datetime.now().isoformat()
                            )
                    return None
        except Exception as e:
            logger.error(f"Error getting product details from CJ Dropshipping: {e}")
            return None
    
    async def place_order(self, order_data: Dict) -> Dict:
        """Place order with CJ Dropshipping"""
        try:
            headers = {
                'CJ-Access-Token': self.api_key,
                'Content-Type': 'application/json'
            }
            
            order_payload = {
                'orderNumber': order_data['order_id'],
                'shippingAddress': order_data['shipping_address'],
                'products': order_data['items']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/shopping/order/createOrder", headers=headers, json=order_payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'supplier_order_id': result['data']['orderId'],
                            'status': 'confirmed',
                            'message': 'Order placed successfully with CJ Dropshipping'
                        }
                    else:
                        error_data = await response.json()
                        return {
                            'success': False,
                            'error': error_data.get('message', 'Unknown error')
                        }
        except Exception as e:
            logger.error(f"Error placing order with CJ Dropshipping: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_order_status(self, supplier_order_id: str) -> Dict:
        """Get order status from CJ Dropshipping"""
        try:
            headers = {
                'CJ-Access-Token': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/shopping/order/getOrderDetail", headers=headers, params={'orderId': supplier_order_id}) as response:
                    if response.status == 200:
                        data = await response.json()
                        order_data = data.get('data')
                        
                        if order_data:
                            return {
                                'supplier_order_id': supplier_order_id,
                                'status': order_data['orderStatus'],
                                'tracking_number': order_data.get('trackNumber'),
                                'last_updated': order_data.get('updateTime')
                            }
            return {}
        except Exception as e:
            logger.error(f"Error getting order status from CJ Dropshipping: {e}")
            return {}
    
    async def get_tracking_info(self, supplier_order_id: str) -> Dict:
        """Get tracking information from CJ Dropshipping"""
        try:
            order_status = await self.get_order_status(supplier_order_id)
            tracking_number = order_status.get('tracking_number')
            
            if tracking_number:
                return {
                    'tracking_number': tracking_number,
                    'status': 'shipped',
                    'tracking_url': f"https://track.cjpacket.com/{tracking_number}"
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting tracking info from CJ Dropshipping: {e}")
            return {}

class SupplierManager:
    """Manage multiple supplier integrations"""
    
    def __init__(self, supplier_configs: Dict[str, Dict]):
        self.suppliers = {}
        self.db_path = "data/supplier_data.db"
        self.init_database()
        self.init_suppliers(supplier_configs)
    
    def init_database(self):
        """Initialize supplier database"""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS supplier_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id TEXT NOT NULL,
                    supplier_sku TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    cost REAL NOT NULL,
                    category TEXT,
                    images TEXT,
                    variants TEXT,
                    stock_quantity INTEGER,
                    shipping_info TEXT,
                    supplier_name TEXT,
                    last_updated TEXT,
                    UNIQUE(supplier_id, supplier_sku)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dropship_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    supplier_order_id TEXT,
                    supplier_name TEXT,
                    customer_info TEXT,
                    shipping_address TEXT,
                    items TEXT,
                    total_amount REAL,
                    cost_amount REAL,
                    profit REAL,
                    status TEXT,
                    tracking_number TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def init_suppliers(self, configs: Dict[str, Dict]):
        """Initialize supplier integrations"""
        for supplier_name, config in configs.items():
            try:
                if supplier_name == 'engwe':
                    self.suppliers['engwe'] = ENGWEIntegration(config)
                elif supplier_name == 'spocket':
                    self.suppliers['spocket'] = SpocketIntegration(config)
                elif supplier_name == 'cj_dropshipping':
                    self.suppliers['cj_dropshipping'] = CJDropshippingIntegration(config)
                
                logger.info(f"Initialized {supplier_name} integration")
            except Exception as e:
                logger.error(f"Failed to initialize {supplier_name}: {e}")
    
    async def sync_all_products(self) -> Dict[str, int]:
        """Sync products from all suppliers"""
        results = {}
        
        for supplier_name, supplier in self.suppliers.items():
            try:
                logger.info(f"Syncing products from {supplier_name}...")
                products = await supplier.get_products(limit=200)
                
                # Save products to database
                count = 0
                with sqlite3.connect(self.db_path) as conn:
                    for product in products:
                        conn.execute("""
                            INSERT OR REPLACE INTO supplier_products
                            (supplier_id, supplier_sku, name, description, price, cost, 
                             category, images, variants, stock_quantity, shipping_info, 
                             supplier_name, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            product.supplier_id,
                            product.supplier_sku,
                            product.name,
                            product.description,
                            product.price,
                            product.cost,
                            product.category,
                            json.dumps(product.images),
                            json.dumps(product.variants),
                            product.stock_quantity,
                            json.dumps(product.shipping_info),
                            product.supplier_name,
                            product.last_updated
                        ))
                        count += 1
                
                results[supplier_name] = count
                logger.info(f"Synced {count} products from {supplier_name}")
                
            except Exception as e:
                logger.error(f"Error syncing products from {supplier_name}: {e}")
                results[supplier_name] = 0
        
        return results
    
    async def place_dropship_order(self, order_data: Dict, preferred_supplier: str = None) -> Dict:
        """Place order with the best available supplier"""
        try:
            # Find best supplier for each item
            supplier_orders = {}
            
            for item in order_data['items']:
                best_supplier = await self.find_best_supplier_for_product(item['product_id'], preferred_supplier)
                
                if best_supplier:
                    if best_supplier not in supplier_orders:
                        supplier_orders[best_supplier] = {
                            'supplier': self.suppliers[best_supplier],
                            'items': [],
                            'total_cost': 0
                        }
                    
                    # Get product cost from database
                    cost = await self.get_product_cost(item['product_id'], best_supplier)
                    supplier_orders[best_supplier]['items'].append({
                        **item,
                        'cost': cost
                    })
                    supplier_orders[best_supplier]['total_cost'] += cost * item['quantity']
            
            # Place orders with each supplier
            order_results = []
            total_cost = 0
            
            for supplier_name, order_info in supplier_orders.items():
                supplier_order_data = {
                    'order_id': f"{order_data['order_id']}-{supplier_name}",
                    'items': order_info['items'],
                    'shipping_address': order_data['shipping_address'],
                    'customer_info': order_data['customer_info']
                }
                
                result = await order_info['supplier'].place_order(supplier_order_data)
                
                if result['success']:
                    # Save order to database
                    dropship_order = DropshipOrder(
                        order_id=order_data['order_id'],
                        supplier_order_id=result['supplier_order_id'],
                        customer_info=order_data['customer_info'],
                        shipping_address=order_data['shipping_address'],
                        items=order_info['items'],
                        total_amount=order_data['total_amount'],
                        cost_amount=order_info['total_cost'],
                        profit=order_data['total_amount'] - order_info['total_cost'],
                        status=result['status'],
                        tracking_number=None,
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat()
                    )
                    
                    await self.save_dropship_order(dropship_order, supplier_name)
                    total_cost += order_info['total_cost']
                
                order_results.append({
                    'supplier': supplier_name,
                    'result': result
                })
            
            return {
                'success': True,
                'orders': order_results,
                'total_cost': total_cost,
                'profit': order_data['total_amount'] - total_cost
            }
            
        except Exception as e:
            logger.error(f"Error placing dropship order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def find_best_supplier_for_product(self, product_id: str, preferred_supplier: str = None) -> Optional[str]:
        """Find the best supplier for a specific product"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if preferred_supplier and preferred_supplier in self.suppliers:
                    # Check if preferred supplier has the product
                    cursor = conn.execute("""
                        SELECT supplier_id FROM supplier_products 
                        WHERE supplier_sku = ? AND supplier_id = ?
                    """, (product_id, preferred_supplier))
                    
                    if cursor.fetchone():
                        return preferred_supplier
                
                # Find supplier with lowest cost
                cursor = conn.execute("""
                    SELECT supplier_id, cost FROM supplier_products 
                    WHERE supplier_sku = ? 
                    ORDER BY cost ASC 
                    LIMIT 1
                """, (product_id,))
                
                result = cursor.fetchone()
                if result:
                    return result[0]
                
            return None
        except Exception as e:
            logger.error(f"Error finding best supplier: {e}")
            return None
    
    async def get_product_cost(self, product_id: str, supplier_id: str) -> float:
        """Get product cost from specific supplier"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT cost FROM supplier_products 
                    WHERE supplier_sku = ? AND supplier_id = ?
                """, (product_id, supplier_id))
                
                result = cursor.fetchone()
                return result[0] if result else 0.0
        except Exception as e:
            logger.error(f"Error getting product cost: {e}")
            return 0.0
    
    async def save_dropship_order(self, order: DropshipOrder, supplier_name: str):
        """Save dropship order to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO dropship_orders
                    (order_id, supplier_order_id, supplier_name, customer_info, 
                     shipping_address, items, total_amount, cost_amount, profit, 
                     status, tracking_number, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order.order_id,
                    order.supplier_order_id,
                    supplier_name,
                    json.dumps(order.customer_info),
                    json.dumps(order.shipping_address),
                    json.dumps(order.items),
                    order.total_amount,
                    order.cost_amount,
                    order.profit,
                    order.status,
                    order.tracking_number,
                    order.created_at,
                    order.updated_at
                ))
        except Exception as e:
            logger.error(f"Error saving dropship order: {e}")
    
    async def update_order_status(self, order_id: str) -> Dict:
        """Update order status from all suppliers"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT supplier_order_id, supplier_name FROM dropship_orders 
                    WHERE order_id = ?
                """, (order_id,))
                
                orders = cursor.fetchall()
                results = []
                
                for supplier_order_id, supplier_name in orders:
                    if supplier_name in self.suppliers:
                        supplier = self.suppliers[supplier_name]
                        status = await supplier.get_order_status(supplier_order_id)
                        
                        # Update database
                        if status:
                            conn.execute("""
                                UPDATE dropship_orders 
                                SET status = ?, tracking_number = ?, updated_at = ?
                                WHERE supplier_order_id = ?
                            """, (
                                status.get('status'),
                                status.get('tracking_number'),
                                datetime.now().isoformat(),
                                supplier_order_id
                            ))
                        
                        results.append({
                            'supplier': supplier_name,
                            'supplier_order_id': supplier_order_id,
                            'status': status
                        })
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'updates': results
                }
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_supplier_stats(self) -> Dict:
        """Get supplier statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Product counts by supplier
                cursor = conn.execute("""
                    SELECT supplier_name, COUNT(*) as product_count
                    FROM supplier_products 
                    GROUP BY supplier_name
                """)
                product_stats = dict(cursor.fetchall())
                
                # Order counts by supplier
                cursor = conn.execute("""
                    SELECT supplier_name, COUNT(*) as order_count, SUM(profit) as total_profit
                    FROM dropship_orders 
                    GROUP BY supplier_name
                """)
                order_stats = {}
                for supplier, count, profit in cursor.fetchall():
                    order_stats[supplier] = {
                        'order_count': count,
                        'total_profit': profit or 0
                    }
                
                return {
                    'product_stats': product_stats,
                    'order_stats': order_stats,
                    'active_suppliers': list(self.suppliers.keys())
                }
        except Exception as e:
            logger.error(f"Error getting supplier stats: {e}")
            return {}

# Example usage and configuration
if __name__ == "__main__":
    # Supplier configurations
    supplier_configs = {
        'engwe': {
            'base_url': 'https://engwe.com'
        },
        'spocket': {
            'api_key': 'your_spocket_api_key'
        },
        'cj_dropshipping': {
            'api_key': 'your_cj_api_key'
        }
    }
    
    # Initialize supplier manager
    supplier_manager = SupplierManager(supplier_configs)
    
    print("Supplier integration system initialized successfully!")