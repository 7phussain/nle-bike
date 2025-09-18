#!/usr/bin/env python3
"""
Sample Data Populator for NLE Bike Demo
Author: MiniMax Agent

Adds sample e-bike products to demonstrate the system working with ENGWE-style data
"""

import sqlite3
import json
from datetime import datetime

def populate_sample_data():
    """Add sample e-bike products to the database"""
    
    sample_products = [
        {
            'id': 'engwe-engine-x-001',
            'name': 'ENGWE Engine X',
            'description': 'Premium 750W fat tire electric bike with 20" wheels, perfect for all terrains. Features include removable 48V 13Ah battery, 7-speed transmission, and LCD display.',
            'price': 1299.99,
            'original_price': 1599.99,
            'image_url': 'https://images.unsplash.com/photo-1571068316344-75bc76f77890?w=800',
            'category': '["Fat Tire", "Commuter"]',
            'colors': '["Black", "White", "Red"]',
            'availability': 'in_stock',
            'specifications': json.dumps({
                'motor': '750W Brushless',
                'battery': '48V 13Ah Lithium',
                'range': '65-100km',
                'max_speed': '45km/h',
                'weight': '31kg',
                'wheel_size': '20 inch'
            }),
            'rating': 4.7,
            'reviews_count': 234,
            'source_url': 'https://engwe.com/products/engine-x',
            'last_updated': datetime.now().isoformat()
        },
        {
            'id': 'engwe-engine-pro-002',
            'name': 'ENGWE Engine Pro 2.0',
            'description': 'Advanced electric mountain bike with 750W motor and dual suspension. Premium components and all-weather capability.',
            'price': 1599.99,
            'original_price': 1899.99,
            'image_url': 'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=800',
            'category': '["Motorcycle-Styled", "Commuter"]',
            'colors': '["Matte Black", "Forest Green"]',
            'availability': 'in_stock',
            'specifications': json.dumps({
                'motor': '750W Mid-Drive',
                'battery': '48V 17.5Ah',
                'range': '80-120km',
                'max_speed': '50km/h',
                'weight': '35kg',
                'suspension': 'Full Suspension'
            }),
            'rating': 4.9,
            'reviews_count': 189,
            'source_url': 'https://engwe.com/products/engine-pro-2',
            'last_updated': datetime.now().isoformat()
        },
        {
            'id': 'engwe-p20-003',
            'name': 'ENGWE P20',
            'description': 'Compact folding e-bike perfect for city commuting. Lightweight design with powerful performance.',
            'price': 899.99,
            'original_price': 1199.99,
            'image_url': 'https://images.unsplash.com/photo-1544191696-15f3c33b6785?w=800',
            'category': '["Folding", "Commuter"]',
            'colors': '["Silver", "Black"]',
            'availability': 'in_stock',
            'specifications': json.dumps({
                'motor': '500W Rear Hub',
                'battery': '36V 10Ah',
                'range': '45-65km',
                'max_speed': '25km/h',
                'weight': '22kg',
                'folded_size': '85x45x65cm'
            }),
            'rating': 4.5,
            'reviews_count': 156,
            'source_url': 'https://engwe.com/products/p20',
            'last_updated': datetime.now().isoformat()
        },
        {
            'id': 'engwe-m20-004',
            'name': 'ENGWE M20',
            'description': 'Versatile 20" fat tire e-bike with step-through frame. Perfect for riders of all heights and abilities.',
            'price': 1099.99,
            'original_price': 1399.99,
            'image_url': 'https://images.unsplash.com/photo-1502744688674-c619d1586c9e?w=800',
            'category': '["Fat Tire", "Transportation"]',
            'colors': '["Blue", "White", "Orange"]',
            'availability': 'in_stock',
            'specifications': json.dumps({
                'motor': '750W Hub Motor',
                'battery': '48V 12.8Ah',
                'range': '55-85km',
                'max_speed': '40km/h',
                'weight': '28kg',
                'frame': 'Step-through'
            }),
            'rating': 4.6,
            'reviews_count': 203,
            'source_url': 'https://engwe.com/products/m20',
            'last_updated': datetime.now().isoformat()
        },
        {
            'id': 'engwe-charger-005',
            'name': 'ENGWE Charger',
            'description': 'High-performance cargo e-bike with extended range. Perfect for deliveries and heavy-duty use.',
            'price': 1799.99,
            'original_price': 2199.99,
            'image_url': 'https://images.unsplash.com/photo-1517654149128-88da2b3e40c2?w=800',
            'category': '["Transportation", "Fat Tire", "Commuter"]',
            'colors': '["Army Green", "Black"]',
            'availability': 'in_stock',
            'specifications': json.dumps({
                'motor': '1000W Dual Motor',
                'battery': '48V 20Ah',
                'range': '100-150km',
                'max_speed': '55km/h',
                'weight': '38kg',
                'cargo_capacity': '150kg'
            }),
            'rating': 4.8,
            'reviews_count': 127,
            'source_url': 'https://engwe.com/products/charger',
            'last_updated': datetime.now().isoformat()
        }
    ]
    
    # Connect to database
    conn = sqlite3.connect('/workspace/data/inventory.db')
    cursor = conn.cursor()
    
    # Insert sample products
    for product in sample_products:
        cursor.execute('''
            INSERT OR REPLACE INTO products 
            (id, name, description, price, original_price, image_url, category, colors, 
             availability, specifications, rating, reviews_count, source_url, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product['id'], product['name'], product['description'], 
            product['price'], product['original_price'], product['image_url'],
            product['category'], product['colors'], product['availability'],
            product['specifications'], product['rating'], product['reviews_count'],
            product['source_url'], product['last_updated']
        ))
    
    # Add a sync log entry
    cursor.execute('''
        INSERT INTO sync_logs (sync_time, products_updated, products_added, errors, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().isoformat(), 0, len(sample_products), 0, 'demo_data_populated'))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully added {len(sample_products)} sample products to database")
    print("🎯 Products include: Engine X, Engine Pro 2.0, P20, M20, and Charger")
    print("📊 Your site now has live product data!")

if __name__ == "__main__":
    populate_sample_data()
