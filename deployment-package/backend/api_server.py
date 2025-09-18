#!/usr/bin/env python3
"""
Fast API Backend for Drop Shipping Site
Author: MiniMax Agent

Provides REST API endpoints for the e-commerce frontend.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import sqlite3
import uvicorn
from pathlib import Path

# Import our inventory manager
from .inventory_manager import InventoryManager, DatabaseManager

# Import marketing automation
from .marketing_api import add_marketing_routes

# Initialize FastAPI app
app = FastAPI(
    title="NLE Bike API",
    description="Modern Drop Shipping E-commerce API with Automated Inventory Management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="../"), name="static")

# Initialize managers
inventory_manager = InventoryManager()
db_manager = DatabaseManager()

# Pydantic models
class ProductResponse(BaseModel):
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

class SyncRequest(BaseModel):
    source: str
    force: bool = False
    lastSync: Optional[str] = None

class CartItem(BaseModel):
    product_id: str
    quantity: int

class OrderRequest(BaseModel):
    items: List[CartItem]
    customer_info: Dict
    shipping_address: Dict
    payment_method: str

# API Routes

@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """Serve the main website"""
    try:
        with open("../index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Welcome to NLE Bike API</h1><p>Frontend not found. Please ensure index.html is in the correct directory.</p>")

@app.get("/api/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    try:
        # Check if database is accessible
        products = db_manager.get_products(limit=1)
        
        return {
            "status": "healthy",
            "service": "NLE Bike API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "products_available": len(products) > 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "NLE Bike API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0)
):
    """Get products with filtering and pagination"""
    try:
        products = db_manager.get_products(limit, offset)
        
        # Apply filters
        if category:
            products = [p for p in products if category.lower() in [c.lower() for c in p['category']]]
        
        if search:
            search_lower = search.lower()
            products = [p for p in products if 
                       search_lower in p['name'].lower() or 
                       search_lower in p['description'].lower()]
        
        if min_price is not None:
            products = [p for p in products if p['price'] >= min_price]
        
        if max_price is not None:
            products = [p for p in products if p['price'] <= max_price]
        
        return products
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get a specific product by ID"""
    try:
        products = db_manager.get_products()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@app.get("/api/categories")
async def get_categories():
    """Get all product categories"""
    try:
        products = db_manager.get_products()
        categories = set()
        
        for product in products:
            categories.update(product['category'])
        
        return sorted(list(categories))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@app.post("/api/sync-inventory")
async def sync_inventory(request: SyncRequest, background_tasks: BackgroundTasks):
    """Trigger inventory synchronization"""
    try:
        if request.force:
            # Run sync immediately
            result = inventory_manager.sync_inventory()
            return result
        else:
            # Run sync in background
            background_tasks.add_task(inventory_manager.sync_inventory)
            return {
                "status": "scheduled",
                "message": "Inventory sync scheduled",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing inventory: {str(e)}")

@app.get("/api/inventory/stats")
async def get_inventory_stats():
    """Get inventory statistics"""
    try:
        stats = inventory_manager.get_inventory_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.get("/api/inventory/sync-logs")
async def get_sync_logs(limit: int = Query(10, ge=1, le=50)):
    """Get recent synchronization logs"""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM sync_logs 
                ORDER BY sync_time DESC 
                LIMIT ?
            """, (limit,))
            
            logs = [dict(row) for row in cursor.fetchall()]
            return logs
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sync logs: {str(e)}")

@app.get("/api/price-history/{product_id}")
async def get_price_history(product_id: str, days: int = Query(30, ge=1, le=365)):
    """Get price history for a product"""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT price, recorded_at 
                FROM price_history 
                WHERE product_id = ? 
                AND recorded_at > datetime('now', '-{} days')
                ORDER BY recorded_at DESC
            """.format(days), (product_id,))
            
            history = [dict(row) for row in cursor.fetchall()]
            return history
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching price history: {str(e)}")

@app.post("/api/orders")
async def create_order(order: OrderRequest):
    """Create a new order (mock implementation)"""
    try:
        # In a real implementation, this would:
        # 1. Validate inventory availability
        # 2. Calculate totals and taxes
        # 3. Process payment
        # 4. Create order in database
        # 5. Send confirmation emails
        # 6. Update inventory
        
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{hash(str(order.items)) % 10000:04d}"
        
        # Mock order processing
        total_amount = 0
        for item in order.items:
            products = db_manager.get_products()
            product = next((p for p in products if p['id'] == item.product_id), None)
            if product:
                total_amount += product['price'] * item.quantity
        
        return {
            "order_id": order_id,
            "status": "confirmed",
            "total_amount": total_amount,
            "estimated_delivery": "5-7 business days",
            "tracking_number": f"TRK{order_id[-8:]}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@app.get("/api/search")
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50)
):
    """Search products with advanced search capabilities"""
    try:
        products = db_manager.get_products()
        search_terms = q.lower().split()
        
        scored_products = []
        
        for product in products:
            score = 0
            text_content = f"{product['name']} {product['description']}".lower()
            
            # Calculate relevance score
            for term in search_terms:
                if term in product['name'].lower():
                    score += 10  # Higher weight for name matches
                elif term in product['description'].lower():
                    score += 5   # Medium weight for description matches
                elif any(term in cat.lower() for cat in product['category']):
                    score += 3   # Lower weight for category matches
            
            if score > 0:
                scored_products.append((score, product))
        
        # Sort by score and return top results
        scored_products.sort(key=lambda x: x[0], reverse=True)
        results = [product for _, product in scored_products[:limit]]
        
        return {
            "query": q,
            "total_results": len(results),
            "products": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")

@app.get("/api/recommendations/{product_id}")
async def get_recommendations(product_id: str, limit: int = Query(5, ge=1, le=10)):
    """Get product recommendations based on a product"""
    try:
        products = db_manager.get_products()
        target_product = next((p for p in products if p['id'] == product_id), None)
        
        if not target_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Simple recommendation algorithm based on categories and price range
        recommendations = []
        target_categories = set(target_product['category'])
        target_price = target_product['price']
        
        for product in products:
            if product['id'] == product_id:
                continue
                
            score = 0
            
            # Category similarity
            common_categories = set(product['category']) & target_categories
            score += len(common_categories) * 10
            
            # Price similarity (within 20% range gets bonus)
            price_diff = abs(product['price'] - target_price) / target_price
            if price_diff <= 0.2:
                score += 5
            
            if score > 0:
                recommendations.append((score, product))
        
        # Sort by score and return top results
        recommendations.sort(key=lambda x: x[0], reverse=True)
        results = [product for _, product in recommendations[:limit]]
        
        return {
            "product_id": product_id,
            "recommendations": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        db_status = "ok"
        try:
            with sqlite3.connect(db_manager.db_path) as conn:
                conn.execute("SELECT 1").fetchone()
        except Exception:
            db_status = "error"
        
        # Check if inventory manager is running
        inventory_status = "running" if inventory_manager.is_running else "stopped"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "inventory_manager": inventory_status,
            "version": "1.0.0"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    print("Starting NLE Bike API...")
    
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Start inventory manager
    inventory_manager.start_scheduled_sync()
    
    # Add marketing automation routes
    add_marketing_routes(app)
    
    print("API started successfully!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down NLE Bike API...")
    inventory_manager.stop()
    print("API shut down successfully!")

if __name__ == "__main__":
    print("Starting NLE Bike API Server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Website: http://localhost:8000")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )