#!/usr/bin/env python3
"""
Analytics and Reporting System
Author: MiniMax Agent

Comprehensive analytics for tracking sales, traffic, conversion rates, and business metrics
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsMetric:
    name: str
    value: float
    change: float
    period: str
    unit: str
    trend: str  # 'up', 'down', 'stable'

@dataclass
class SalesData:
    date: str
    revenue: float
    orders: int
    customers: int
    avg_order_value: float
    conversion_rate: float

@dataclass
class TrafficData:
    date: str
    visits: int
    unique_visitors: int
    page_views: int
    bounce_rate: float
    avg_session_duration: float
    traffic_sources: Dict[str, int]

class AnalyticsEngine:
    """Core analytics engine for processing business metrics"""
    
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize analytics database"""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Sales analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    revenue REAL DEFAULT 0,
                    orders INTEGER DEFAULT 0,
                    customers INTEGER DEFAULT 0,
                    avg_order_value REAL DEFAULT 0,
                    conversion_rate REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Traffic analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traffic_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    visits INTEGER DEFAULT 0,
                    unique_visitors INTEGER DEFAULT 0,
                    page_views INTEGER DEFAULT 0,
                    bounce_rate REAL DEFAULT 0,
                    avg_session_duration REAL DEFAULT 0,
                    traffic_sources TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Product analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS product_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT,
                    views INTEGER DEFAULT 0,
                    cart_adds INTEGER DEFAULT 0,
                    purchases INTEGER DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    conversion_rate REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Customer analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    new_customers INTEGER DEFAULT 0,
                    returning_customers INTEGER DEFAULT 0,
                    customer_lifetime_value REAL DEFAULT 0,
                    repeat_purchase_rate REAL DEFAULT 0,
                    avg_time_between_orders REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Marketing analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS marketing_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    campaign_name TEXT,
                    channel TEXT,
                    spend REAL DEFAULT 0,
                    impressions INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    roas REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Events tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """)
    
    def track_event(self, event_type: str, event_data: Dict, user_id: str = None, 
                   session_id: str = None, ip_address: str = None, user_agent: str = None):
        """Track a user event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO events (event_type, event_data, user_id, session_id, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event_type,
                    json.dumps(event_data),
                    user_id,
                    session_id,
                    ip_address,
                    user_agent
                ))
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
    
    def track_page_view(self, page: str, user_id: str = None, session_id: str = None, **kwargs):
        """Track a page view"""
        self.track_event('page_view', {
            'page': page,
            **kwargs
        }, user_id, session_id)
    
    def track_product_view(self, product_id: str, product_name: str, user_id: str = None, **kwargs):
        """Track a product view"""
        self.track_event('product_view', {
            'product_id': product_id,
            'product_name': product_name,
            **kwargs
        }, user_id)
    
    def track_add_to_cart(self, product_id: str, quantity: int, price: float, user_id: str = None):
        """Track add to cart event"""
        self.track_event('add_to_cart', {
            'product_id': product_id,
            'quantity': quantity,
            'price': price
        }, user_id)
    
    def track_purchase(self, order_id: str, items: List[Dict], total: float, user_id: str = None):
        """Track a purchase"""
        self.track_event('purchase', {
            'order_id': order_id,
            'items': items,
            'total': total
        }, user_id)
    
    def generate_daily_sales_report(self, date: str = None) -> SalesData:
        """Generate daily sales report"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get purchase events for the date
                cursor = conn.execute("""
                    SELECT event_data FROM events 
                    WHERE event_type = 'purchase' 
                    AND DATE(timestamp) = ?
                """, (date,))
                
                purchases = [json.loads(row[0]) for row in cursor.fetchall()]
                
                # Calculate metrics
                revenue = sum(p['total'] for p in purchases)
                orders = len(purchases)
                
                # Get unique customers
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM events 
                    WHERE event_type = 'purchase' 
                    AND DATE(timestamp) = ?
                    AND user_id IS NOT NULL
                """, (date,))
                customers = cursor.fetchone()[0] or 0
                
                # Calculate average order value
                avg_order_value = revenue / orders if orders > 0 else 0
                
                # Calculate conversion rate (purchases / unique visitors)
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT session_id) FROM events 
                    WHERE DATE(timestamp) = ?
                    AND session_id IS NOT NULL
                """, (date,))
                visitors = cursor.fetchone()[0] or 0
                conversion_rate = (orders / visitors * 100) if visitors > 0 else 0
                
                sales_data = SalesData(
                    date=date,
                    revenue=revenue,
                    orders=orders,
                    customers=customers,
                    avg_order_value=avg_order_value,
                    conversion_rate=conversion_rate
                )
                
                # Save to analytics table
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO sales_analytics 
                        (date, revenue, orders, customers, avg_order_value, conversion_rate)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        date, revenue, orders, customers, avg_order_value, conversion_rate
                    ))
                
                return sales_data
                
        except Exception as e:
            logger.error(f"Error generating sales report: {e}")
            return SalesData(date, 0, 0, 0, 0, 0)
    
    def generate_traffic_report(self, date: str = None) -> TrafficData:
        """Generate daily traffic report"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get page view events
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM events 
                    WHERE event_type = 'page_view' 
                    AND DATE(timestamp) = ?
                """, (date,))
                page_views = cursor.fetchone()[0] or 0
                
                # Get unique visitors
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT session_id) FROM events 
                    WHERE event_type = 'page_view' 
                    AND DATE(timestamp) = ?
                    AND session_id IS NOT NULL
                """, (date,))
                unique_visitors = cursor.fetchone()[0] or 0
                
                # Calculate visits (sessions)
                visits = unique_visitors  # Simplified - in reality would group by session
                
                # Calculate bounce rate (single page sessions)
                cursor = conn.execute("""
                    SELECT session_id, COUNT(*) as page_count
                    FROM events 
                    WHERE event_type = 'page_view' 
                    AND DATE(timestamp) = ?
                    AND session_id IS NOT NULL
                    GROUP BY session_id
                """, (date,))
                
                session_page_counts = cursor.fetchall()
                single_page_sessions = sum(1 for _, count in session_page_counts if count == 1)
                bounce_rate = (single_page_sessions / visits * 100) if visits > 0 else 0
                
                # Mock traffic sources (in real app, would track referrers)
                traffic_sources = {
                    'direct': int(visits * 0.4),
                    'search': int(visits * 0.3),
                    'social': int(visits * 0.2),
                    'email': int(visits * 0.1)
                }
                
                # Average session duration (mock data)
                avg_session_duration = 180  # 3 minutes
                
                traffic_data = TrafficData(
                    date=date,
                    visits=visits,
                    unique_visitors=unique_visitors,
                    page_views=page_views,
                    bounce_rate=bounce_rate,
                    avg_session_duration=avg_session_duration,
                    traffic_sources=traffic_sources
                )
                
                # Save to analytics table
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO traffic_analytics 
                        (date, visits, unique_visitors, page_views, bounce_rate, 
                         avg_session_duration, traffic_sources)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date, visits, unique_visitors, page_views, bounce_rate,
                        avg_session_duration, json.dumps(traffic_sources)
                    ))
                
                return traffic_data
                
        except Exception as e:
            logger.error(f"Error generating traffic report: {e}")
            return TrafficData(date, 0, 0, 0, 0, 0, {})
    
    def get_product_analytics(self, date: str = None, limit: int = 10) -> List[Dict]:
        """Get product performance analytics"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get product views
                cursor = conn.execute("""
                    SELECT 
                        JSON_EXTRACT(event_data, '$.product_id') as product_id,
                        JSON_EXTRACT(event_data, '$.product_name') as product_name,
                        COUNT(*) as views
                    FROM events 
                    WHERE event_type = 'product_view' 
                    AND DATE(timestamp) = ?
                    GROUP BY product_id, product_name
                """, (date,))
                
                product_views = {row[0]: {'name': row[1], 'views': row[2]} for row in cursor.fetchall()}
                
                # Get add to cart events
                cursor = conn.execute("""
                    SELECT 
                        JSON_EXTRACT(event_data, '$.product_id') as product_id,
                        COUNT(*) as cart_adds
                    FROM events 
                    WHERE event_type = 'add_to_cart' 
                    AND DATE(timestamp) = ?
                    GROUP BY product_id
                """, (date,))
                
                cart_adds = dict(cursor.fetchall())
                
                # Get purchases
                cursor = conn.execute("""
                    SELECT event_data FROM events 
                    WHERE event_type = 'purchase' 
                    AND DATE(timestamp) = ?
                """, (date,))
                
                purchases = [json.loads(row[0]) for row in cursor.fetchall()]
                product_purchases = defaultdict(lambda: {'count': 0, 'revenue': 0})
                
                for purchase in purchases:
                    for item in purchase.get('items', []):
                        product_id = item.get('id')
                        if product_id:
                            product_purchases[product_id]['count'] += item.get('quantity', 1)
                            product_purchases[product_id]['revenue'] += item.get('price', 0) * item.get('quantity', 1)
                
                # Combine data
                analytics = []
                for product_id, view_data in product_views.items():
                    views = view_data['views']
                    cart_adds_count = cart_adds.get(product_id, 0)
                    purchases_count = product_purchases[product_id]['count']
                    revenue = product_purchases[product_id]['revenue']
                    
                    conversion_rate = (purchases_count / views * 100) if views > 0 else 0
                    
                    analytics.append({
                        'product_id': product_id,
                        'product_name': view_data['name'],
                        'views': views,
                        'cart_adds': cart_adds_count,
                        'purchases': purchases_count,
                        'revenue': revenue,
                        'conversion_rate': round(conversion_rate, 2)
                    })
                
                # Sort by revenue
                analytics.sort(key=lambda x: x['revenue'], reverse=True)
                
                return analytics[:limit]
                
        except Exception as e:
            logger.error(f"Error getting product analytics: {e}")
            return []
    
    def get_key_metrics(self, period: str = '7d') -> List[AnalyticsMetric]:
        """Get key business metrics with period comparison"""
        try:
            end_date = datetime.now()
            
            if period == '7d':
                start_date = end_date - timedelta(days=7)
                compare_start = start_date - timedelta(days=7)
                compare_end = start_date
            elif period == '30d':
                start_date = end_date - timedelta(days=30)
                compare_start = start_date - timedelta(days=30)
                compare_end = start_date
            else:  # 24h
                start_date = end_date - timedelta(days=1)
                compare_start = start_date - timedelta(days=1)
                compare_end = start_date
            
            current_metrics = self.calculate_period_metrics(start_date, end_date)\n            previous_metrics = self.calculate_period_metrics(compare_start, compare_end)
            
            metrics = []
            
            for key, current_value in current_metrics.items():
                previous_value = previous_metrics.get(key, 0)
                
                if previous_value > 0:
                    change = ((current_value - previous_value) / previous_value) * 100
                else:
                    change = 100 if current_value > 0 else 0
                
                trend = 'up' if change > 0 else 'down' if change < 0 else 'stable'
                
                # Format units
                if key in ['revenue', 'avg_order_value']:
                    unit = '€'
                elif key in ['conversion_rate', 'bounce_rate']:
                    unit = '%'
                else:
                    unit = ''
                
                metrics.append(AnalyticsMetric(
                    name=key.replace('_', ' ').title(),
                    value=current_value,
                    change=round(change, 1),
                    period=period,
                    unit=unit,
                    trend=trend
                ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting key metrics: {e}")
            return []
    
    def calculate_period_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate metrics for a specific period"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                start_str = start_date.strftime('%Y-%m-%d')
                end_str = end_date.strftime('%Y-%m-%d')
                
                # Revenue
                cursor = conn.execute("""
                    SELECT SUM(revenue) FROM sales_analytics 
                    WHERE date >= ? AND date <= ?
                """, (start_str, end_str))
                revenue = cursor.fetchone()[0] or 0
                
                # Orders
                cursor = conn.execute("""
                    SELECT SUM(orders) FROM sales_analytics 
                    WHERE date >= ? AND date <= ?
                """, (start_str, end_str))
                orders = cursor.fetchone()[0] or 0
                
                # Customers
                cursor = conn.execute("""
                    SELECT SUM(customers) FROM sales_analytics 
                    WHERE date >= ? AND date <= ?
                """, (start_str, end_str))
                customers = cursor.fetchone()[0] or 0
                
                # Average order value
                avg_order_value = revenue / orders if orders > 0 else 0
                
                # Conversion rate (average)
                cursor = conn.execute("""
                    SELECT AVG(conversion_rate) FROM sales_analytics 
                    WHERE date >= ? AND date <= ?
                """, (start_str, end_str))
                conversion_rate = cursor.fetchone()[0] or 0
                
                # Bounce rate (average)
                cursor = conn.execute("""
                    SELECT AVG(bounce_rate) FROM traffic_analytics 
                    WHERE date >= ? AND date <= ?
                """, (start_str, end_str))
                bounce_rate = cursor.fetchone()[0] or 0
                
                # Unique visitors
                cursor = conn.execute("""
                    SELECT SUM(unique_visitors) FROM traffic_analytics 
                    WHERE date >= ? AND date <= ?
                """, (start_str, end_str))
                unique_visitors = cursor.fetchone()[0] or 0
                
                return {
                    'revenue': revenue,
                    'orders': orders,
                    'customers': customers,
                    'avg_order_value': avg_order_value,
                    'conversion_rate': conversion_rate,
                    'bounce_rate': bounce_rate,
                    'unique_visitors': unique_visitors
                }
                
        except Exception as e:
            logger.error(f"Error calculating period metrics: {e}")
            return {}
    
    def get_sales_trend(self, days: int = 30) -> List[Dict]:
        """Get sales trend data for charts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                cursor = conn.execute("""
                    SELECT date, revenue, orders, customers 
                    FROM sales_analytics 
                    WHERE date >= ? AND date <= ?
                    ORDER BY date
                """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                
                return [
                    {
                        'date': row[0],
                        'revenue': row[1],
                        'orders': row[2],
                        'customers': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error getting sales trend: {e}")
            return []
    
    def get_traffic_sources(self, days: int = 7) -> Dict[str, int]:
        """Get traffic sources breakdown"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                cursor = conn.execute("""
                    SELECT traffic_sources 
                    FROM traffic_analytics 
                    WHERE date >= ? AND date <= ?
                """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                
                total_sources = defaultdict(int)
                
                for row in cursor.fetchall():
                    if row[0]:
                        sources = json.loads(row[0])
                        for source, count in sources.items():
                            total_sources[source] += count
                
                return dict(total_sources)
                
        except Exception as e:
            logger.error(f"Error getting traffic sources: {e}")
            return {}
    
    def export_analytics_report(self, start_date: str, end_date: str, format: str = 'json') -> str:
        """Export comprehensive analytics report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Sales data
                sales_df = pd.read_sql_query("""
                    SELECT * FROM sales_analytics 
                    WHERE date >= ? AND date <= ?
                    ORDER BY date
                """, conn, params=(start_date, end_date))
                
                # Traffic data
                traffic_df = pd.read_sql_query("""
                    SELECT * FROM traffic_analytics 
                    WHERE date >= ? AND date <= ?
                    ORDER BY date
                """, conn, params=(start_date, end_date))
                
                # Product data
                product_df = pd.read_sql_query("""
                    SELECT * FROM product_analytics 
                    WHERE date >= ? AND date <= ?
                    ORDER BY date, revenue DESC
                """, conn, params=(start_date, end_date))
                
                report_data = {
                    'period': f"{start_date} to {end_date}",
                    'generated_at': datetime.now().isoformat(),
                    'sales_summary': {
                        'total_revenue': float(sales_df['revenue'].sum()),
                        'total_orders': int(sales_df['orders'].sum()),
                        'total_customers': int(sales_df['customers'].sum()),
                        'avg_order_value': float(sales_df['avg_order_value'].mean()),
                        'avg_conversion_rate': float(sales_df['conversion_rate'].mean())
                    },
                    'traffic_summary': {
                        'total_visits': int(traffic_df['visits'].sum()),
                        'total_unique_visitors': int(traffic_df['unique_visitors'].sum()),
                        'total_page_views': int(traffic_df['page_views'].sum()),
                        'avg_bounce_rate': float(traffic_df['bounce_rate'].mean()),
                        'avg_session_duration': float(traffic_df['avg_session_duration'].mean())
                    },
                    'top_products': product_df.head(10).to_dict('records'),
                    'daily_sales': sales_df.to_dict('records'),
                    'daily_traffic': traffic_df.to_dict('records')
                }
                
                if format == 'json':
                    return json.dumps(report_data, indent=2, default=str)
                elif format == 'csv':
                    # Export as CSV files
                    sales_csv = sales_df.to_csv(index=False)
                    return sales_csv
                else:
                    return json.dumps(report_data, indent=2, default=str)
                    
        except Exception as e:
            logger.error(f"Error exporting analytics report: {e}")
            return "{}"

class RealtimeAnalytics:
    """Real-time analytics for live dashboard updates"""
    
    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.active_sessions = set()
        self.current_visitors = 0
    
    def track_session_start(self, session_id: str):
        """Track when a user session starts"""
        self.active_sessions.add(session_id)
        self.current_visitors = len(self.active_sessions)
    
    def track_session_end(self, session_id: str):
        """Track when a user session ends"""
        self.active_sessions.discard(session_id)
        self.current_visitors = len(self.active_sessions)
    
    def get_realtime_metrics(self) -> Dict:
        """Get real-time metrics for dashboard"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.analytics_engine.db_path) as conn:
                # Today's revenue
                cursor = conn.execute("""
                    SELECT SUM(JSON_EXTRACT(event_data, '$.total')) 
                    FROM events 
                    WHERE event_type = 'purchase' 
                    AND DATE(timestamp) = ?
                """, (today,))
                today_revenue = cursor.fetchone()[0] or 0
                
                # Today's orders
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM events 
                    WHERE event_type = 'purchase' 
                    AND DATE(timestamp) = ?
                """, (today,))
                today_orders = cursor.fetchone()[0] or 0
                
                # Last hour activity
                one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM events 
                    WHERE timestamp >= ?
                """, (one_hour_ago,))
                last_hour_events = cursor.fetchone()[0] or 0
                
                return {
                    'current_visitors': self.current_visitors,
                    'today_revenue': today_revenue,
                    'today_orders': today_orders,
                    'last_hour_events': last_hour_events,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {
                'current_visitors': 0,
                'today_revenue': 0,
                'today_orders': 0,
                'last_hour_events': 0,
                'timestamp': datetime.now().isoformat()
            }

# Example usage and testing
if __name__ == "__main__":
    # Initialize analytics engine
    analytics = AnalyticsEngine()
    
    # Simulate some events for testing
    print("Simulating analytics events...")
    
    # Mock data for demonstration
    import random
    from datetime import date, timedelta
    
    # Generate mock events for the last 30 days
    for i in range(30):
        day = date.today() - timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        
        # Generate mock daily metrics
        daily_visitors = random.randint(100, 500)
        daily_orders = random.randint(5, 25)
        daily_revenue = daily_orders * random.uniform(50, 200)
        
        # Simulate events
        for j in range(daily_visitors):
            session_id = f"session_{day_str}_{j}"
            user_id = f"user_{random.randint(1, 200)}"
            
            # Page view
            analytics.track_page_view('/', user_id, session_id)
            
            # Some product views
            if random.random() < 0.3:
                product_id = f"product_{random.randint(1, 10)}"
                analytics.track_product_view(product_id, f"Product {product_id}", user_id)
                
                # Some add to cart
                if random.random() < 0.2:
                    analytics.track_add_to_cart(product_id, 1, random.uniform(50, 200), user_id)
        
        # Some purchases
        for j in range(daily_orders):
            user_id = f"user_{random.randint(1, 200)}"
            order_id = f"order_{day_str}_{j}"
            total = random.uniform(50, 200)
            
            analytics.track_purchase(order_id, [
                {'id': f"product_{random.randint(1, 10)}", 'quantity': 1, 'price': total}
            ], total, user_id)
        
        # Generate daily reports
        sales_data = analytics.generate_daily_sales_report(day_str)
        traffic_data = analytics.generate_traffic_report(day_str)
        
        print(f"Generated data for {day_str}: {sales_data.orders} orders, €{sales_data.revenue:.2f} revenue")
    
    # Get key metrics
    print("\nKey Metrics (7 days):")
    metrics = analytics.get_key_metrics('7d')
    for metric in metrics:
        print(f"{metric.name}: {metric.value:.2f}{metric.unit} ({metric.change:+.1f}%)")
    
    # Get product analytics
    print("\nTop Products Today:")
    product_analytics = analytics.get_product_analytics()
    for product in product_analytics[:5]:
        print(f"{product['product_name']}: {product['views']} views, €{product['revenue']:.2f} revenue")
    
    # Export report
    report = analytics.export_analytics_report(
        (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'),
        date.today().strftime('%Y-%m-%d')
    )
    
    # Save report
    with open('analytics_report.json', 'w') as f:
        f.write(report)
    
    print("\nAnalytics system initialized and test data generated successfully!")
    print("Report exported to analytics_report.json")
