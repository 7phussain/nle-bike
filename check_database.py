#!/usr/bin/env python3
import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('data/inventory.db')
conn.row_factory = sqlite3.Row

# Get product count
cursor = conn.execute('SELECT COUNT(*) as count FROM products')
product_count = cursor.fetchone()['count']
print(f'Total products in database: {product_count}')

if product_count > 0:
    print('\n--- Sample Products ---')
    cursor = conn.execute('SELECT * FROM products LIMIT 3')
    products = cursor.fetchall()
    
    for product in products:
        print(f'ID: {product["id"]}')
        print(f'Name: {product["name"]}')
        print(f'Price: ${product["price"]}')
        print(f'Last Updated: {product["last_updated"]}')
        print(f'Source: {product["source_url"]}')
        print('---')

# Check sync logs
print('\n--- Sync Logs ---')
cursor = conn.execute('SELECT * FROM sync_logs ORDER BY sync_time DESC LIMIT 3')
logs = cursor.fetchall()

if logs:
    for log in logs:
        print(f'Sync Time: {log["sync_time"]}')
        print(f'Products Added: {log["products_added"]}')
        print(f'Products Updated: {log["products_updated"]}')
        print(f'Status: {log["status"]}')
        print('---')
else:
    print('No sync logs found')

conn.close()
