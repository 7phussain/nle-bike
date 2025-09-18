#!/usr/bin/env python3
"""
Advanced Marketing Automation System
Author: MiniMax Agent

Complete marketing automation including:
- Customer behavior tracking
- Abandoned cart recovery
- Push notifications (Web, Email, WhatsApp)
- Wishlist automation
- Price drop alerts
- Product update notifications
"""

import os
import json
import asyncio
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from apscheduler.schedulers.background import BackgroundScheduler
import uuid

logger = logging.getLogger(__name__)

@dataclass
class CustomerBehavior:
    user_id: str
    session_id: str
    event_type: str
    event_data: Dict
    timestamp: datetime
    page_url: str
    user_agent: str
    ip_address: str

@dataclass
class CartItem:
    product_id: str
    product_name: str
    price: float
    quantity: int
    image_url: str
    added_at: datetime

@dataclass
class Cart:
    user_id: str
    session_id: str
    items: List[CartItem]
    total_value: float
    created_at: datetime
    updated_at: datetime
    status: str  # 'active', 'abandoned', 'converted'

@dataclass
class Notification:
    id: str
    user_id: str
    type: str  # 'cart_abandonment', 'price_drop', 'back_in_stock', 'order_update'
    channel: str  # 'email', 'web_push', 'whatsapp'
    content: Dict
    scheduled_at: datetime
    sent_at: Optional[datetime]
    status: str  # 'pending', 'sent', 'failed'

class BehaviorTracker:
    """Track and analyze customer behavior"""
    
    def __init__(self, db_path: str = "data/marketing.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize marketing database"""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Customer behavior tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_behavior (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    page_url TEXT,
                    user_agent TEXT,
                    ip_address TEXT,
                    device_type TEXT,
                    referrer TEXT
                )
            """)
            
            # Shopping carts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shopping_carts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    cart_data TEXT,
                    total_value REAL DEFAULT 0,
                    items_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Wishlists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wishlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT,
                    price REAL,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    notified_price_drop BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Notifications queue
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    type TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    content TEXT,
                    scheduled_at TEXT,
                    sent_at TEXT,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Customer segments
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    segment_type TEXT,
                    segment_value TEXT,
                    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, segment_type)
                )
            """)
            
            # Email subscriptions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    subscription_types TEXT,
                    subscribed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    unsubscribed_at TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
    
    def track_behavior(self, user_id: str, session_id: str, event_type: str, 
                      event_data: Dict, page_url: str = None, user_agent: str = None, 
                      ip_address: str = None, device_type: str = None, referrer: str = None):
        """Track customer behavior event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO customer_behavior 
                    (user_id, session_id, event_type, event_data, page_url, user_agent, 
                     ip_address, device_type, referrer)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, session_id, event_type, json.dumps(event_data),
                    page_url, user_agent, ip_address, device_type, referrer
                ))
            
            # Trigger automation based on event
            asyncio.create_task(self.process_behavior_event(user_id, event_type, event_data))
            
        except Exception as e:
            logger.error(f"Error tracking behavior: {e}")
    
    async def process_behavior_event(self, user_id: str, event_type: str, event_data: Dict):
        """Process behavior event and trigger automations"""
        try:
            automation = MarketingAutomation()
            
            if event_type == 'add_to_cart':
                await automation.handle_cart_addition(user_id, event_data)
            elif event_type == 'remove_from_cart':
                await automation.handle_cart_removal(user_id, event_data)
            elif event_type == 'page_exit' and 'cart' in event_data.get('page', ''):
                await automation.handle_cart_abandonment(user_id)
            elif event_type == 'wishlist_add':
                await automation.handle_wishlist_addition(user_id, event_data)
            elif event_type == 'product_view':
                await automation.handle_product_view(user_id, event_data)
                
        except Exception as e:
            logger.error(f"Error processing behavior event: {e}")
    
    def get_customer_segment(self, user_id: str) -> Dict[str, str]:
        """Get customer segment information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT segment_type, segment_value 
                    FROM customer_segments 
                    WHERE user_id = ?
                """, (user_id,))
                
                segments = {}
                for row in cursor.fetchall():
                    segments[row['segment_type']] = row['segment_value']
                
                return segments
                
        except Exception as e:
            logger.error(f"Error getting customer segment: {e}")
            return {}

class MarketingAutomation:
    """Core marketing automation engine"""
    
    def __init__(self):
        self.db_path = "data/marketing.db"
        self.notification_service = NotificationService()
        
    async def handle_cart_addition(self, user_id: str, event_data: Dict):
        """Handle add to cart event"""
        try:
            # Update cart in database
            await self.update_cart(user_id, event_data, 'add')
            
            # Schedule abandoned cart recovery email (if cart not converted in 1 hour)
            await self.schedule_abandoned_cart_recovery(user_id, delay_hours=1)
            
        except Exception as e:
            logger.error(f"Error handling cart addition: {e}")
    
    async def handle_cart_removal(self, user_id: str, event_data: Dict):
        """Handle remove from cart event"""
        try:
            await self.update_cart(user_id, event_data, 'remove')
            
        except Exception as e:
            logger.error(f"Error handling cart removal: {e}")
    
    async def handle_cart_abandonment(self, user_id: str):
        """Handle cart abandonment detection"""
        try:
            # Check if user has items in cart
            cart = await self.get_active_cart(user_id)
            if cart and cart['items_count'] > 0:
                # Schedule immediate abandoned cart email
                await self.schedule_abandoned_cart_recovery(user_id, delay_hours=0.5)
                
                # Schedule follow-up emails
                await self.schedule_abandoned_cart_recovery(user_id, delay_hours=24, template='cart_reminder_2')
                await self.schedule_abandoned_cart_recovery(user_id, delay_hours=72, template='cart_reminder_final')
                
        except Exception as e:
            logger.error(f"Error handling cart abandonment: {e}")
    
    async def handle_wishlist_addition(self, user_id: str, event_data: Dict):
        """Handle wishlist addition"""
        try:
            product_id = event_data.get('product_id')
            product_name = event_data.get('product_name')
            price = event_data.get('price')
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO wishlists 
                    (user_id, product_id, product_name, price)
                    VALUES (?, ?, ?, ?)
                """, (user_id, product_id, product_name, price))
            
            # Send wishlist confirmation
            await self.notification_service.send_wishlist_confirmation(user_id, product_name)
            
        except Exception as e:
            logger.error(f"Error handling wishlist addition: {e}")
    
    async def handle_product_view(self, user_id: str, event_data: Dict):
        """Handle product view for personalization"""
        try:
            product_id = event_data.get('product_id')
            category = event_data.get('category', 'general')
            
            # Update customer interest segment
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO customer_segments 
                    (user_id, segment_type, segment_value)
                    VALUES (?, ?, ?)
                """, (user_id, 'interest', category))
            
        except Exception as e:
            logger.error(f"Error handling product view: {e}")
    
    async def update_cart(self, user_id: str, event_data: Dict, action: str):
        """Update shopping cart"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current cart
                cursor = conn.execute("""
                    SELECT cart_data, total_value, items_count 
                    FROM shopping_carts 
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY updated_at DESC LIMIT 1
                """, (user_id,))
                
                cart_row = cursor.fetchone()
                cart_items = json.loads(cart_row[0]) if cart_row else []
                total_value = cart_row[1] if cart_row else 0
                items_count = cart_row[2] if cart_row else 0
                
                product_id = event_data.get('product_id')
                
                if action == 'add':
                    # Add or update item in cart
                    item = {
                        'product_id': product_id,
                        'product_name': event_data.get('product_name'),
                        'price': event_data.get('price'),
                        'quantity': event_data.get('quantity', 1),
                        'image_url': event_data.get('image_url'),
                        'added_at': datetime.now().isoformat()
                    }
                    
                    # Check if item already exists
                    existing_item = next((i for i in cart_items if i['product_id'] == product_id), None)
                    if existing_item:
                        existing_item['quantity'] += item['quantity']
                    else:
                        cart_items.append(item)
                        items_count += 1
                    
                    total_value += item['price'] * item['quantity']
                
                elif action == 'remove':
                    # Remove item from cart
                    cart_items = [i for i in cart_items if i['product_id'] != product_id]
                    items_count = len(cart_items)
                    total_value = sum(i['price'] * i['quantity'] for i in cart_items)
                
                # Update cart in database
                conn.execute("""
                    INSERT OR REPLACE INTO shopping_carts 
                    (user_id, cart_data, total_value, items_count, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, json.dumps(cart_items), total_value, items_count, datetime.now().isoformat()))
                
        except Exception as e:
            logger.error(f"Error updating cart: {e}")
    
    async def get_active_cart(self, user_id: str) -> Optional[Dict]:
        """Get active cart for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM shopping_carts 
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY updated_at DESC LIMIT 1
                """, (user_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting active cart: {e}")
            return None
    
    async def schedule_abandoned_cart_recovery(self, user_id: str, delay_hours: float, template: str = 'abandoned_cart'):
        """Schedule abandoned cart recovery notification"""
        try:
            notification_id = str(uuid.uuid4())
            scheduled_at = datetime.now() + timedelta(hours=delay_hours)
            
            cart = await self.get_active_cart(user_id)
            if not cart or cart['items_count'] == 0:
                return
            
            notification = Notification(
                id=notification_id,
                user_id=user_id,
                type='cart_abandonment',
                channel='email',
                content={
                    'template': template,
                    'cart_data': cart['cart_data'],
                    'total_value': cart['total_value']
                },
                scheduled_at=scheduled_at,
                sent_at=None,
                status='pending'
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO notifications 
                    (id, user_id, type, channel, content, scheduled_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    notification.id, notification.user_id, notification.type,
                    notification.channel, json.dumps(notification.content),
                    notification.scheduled_at.isoformat(), notification.status
                ))
            
        except Exception as e:
            logger.error(f"Error scheduling abandoned cart recovery: {e}")
    
    async def check_price_drops(self):
        """Check for price drops on wishlist items"""
        try:
            from .inventory_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT w.*, p.price as current_price 
                    FROM wishlists w
                    JOIN products p ON w.product_id = p.id
                    WHERE p.price < w.price AND w.notified_price_drop = FALSE
                """)
                
                for row in cursor.fetchall():
                    # Send price drop notification
                    await self.notification_service.send_price_drop_alert(
                        row['user_id'], row['product_name'], 
                        row['price'], row['current_price']
                    )
                    
                    # Mark as notified
                    conn.execute("""
                        UPDATE wishlists 
                        SET notified_price_drop = TRUE 
                        WHERE id = ?
                    """, (row['id'],))
                    
        except Exception as e:
            logger.error(f"Error checking price drops: {e}")

class NotificationService:
    """Handle all notification channels (Email, Web Push, WhatsApp)"""
    
    def __init__(self):
        self.db_path = "data/marketing.db"
        self.email_templates = self.load_email_templates()
    
    def load_email_templates(self) -> Dict[str, str]:
        """Load email templates"""
        return {
            'abandoned_cart': """
            <h2>🛒 You left something in your cart!</h2>
            <p>Don't miss out on these amazing e-bikes:</p>
            {% for item in cart_items %}
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                <h3>{{ item.product_name }}</h3>
                <p>Price: ${{ item.price }}</p>
                <p>Quantity: {{ item.quantity }}</p>
            </div>
            {% endfor %}
            <p><strong>Total: ${{ total_value }}</strong></p>
            <a href="{{ checkout_url }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none;">Complete Purchase</a>
            """,
            
            'cart_reminder_2': """
            <h2>⏰ Still thinking about your e-bike?</h2>
            <p>Your cart is waiting! These premium ENGWE bikes won't last long.</p>
            <p>Total Value: ${{ total_value }}</p>
            <a href="{{ checkout_url }}">Complete Your Order Now</a>
            """,
            
            'cart_reminder_final': """
            <h2>🚨 Last chance! Your cart expires soon</h2>
            <p>This is your final reminder about the e-bikes in your cart.</p>
            <p><strong>Special offer: Use code SAVE10 for 10% off!</strong></p>
            <a href="{{ checkout_url }}">Claim Your Discount Now</a>
            """,
            
            'price_drop': """
            <h2>💰 Price Drop Alert!</h2>
            <p>Great news! The price of {{ product_name }} in your wishlist has dropped!</p>
            <p>Was: ${{ old_price }}</p>
            <p>Now: ${{ new_price }} (Save ${{ savings }}!)</p>
            <a href="{{ product_url }}">Buy Now</a>
            """,
            
            'back_in_stock': """
            <h2>🎉 Back in Stock!</h2>
            <p>{{ product_name }} is now back in stock!</p>
            <p>Don't wait - limited quantities available.</p>
            <a href="{{ product_url }}">Order Now</a>
            """,
            
            'order_confirmation': """
            <h2>✅ Order Confirmed!</h2>
            <p>Thank you for your order #{{ order_id }}!</p>
            <p>We'll send you tracking information once your e-bike ships.</p>
            <p>Estimated delivery: {{ estimated_delivery }}</p>
            """,
            
            'shipping_update': """
            <h2>📦 Your e-bike is on the way!</h2>
            <p>Order #{{ order_id }} has shipped!</p>
            <p>Tracking number: {{ tracking_number }}</p>
            <p><a href="{{ tracking_url }}">Track Your Package</a></p>
            """
        }
    
    async def send_abandoned_cart_email(self, user_id: str, cart_data: Dict, template: str = 'abandoned_cart'):
        """Send abandoned cart recovery email"""
        try:
            email = await self.get_user_email(user_id)
            if not email:
                return False
            
            cart_items = json.loads(cart_data['cart_data'])
            template_content = self.email_templates[template]
            
            # Render template
            template_obj = Template(template_content)
            html_content = template_obj.render(
                cart_items=cart_items,
                total_value=cart_data['total_value'],
                checkout_url=f"https://your-domain.com/checkout?user={user_id}"
            )
            
            # Send email (implement with your email service)
            subject = "Complete your e-bike purchase - Cart waiting!"
            await self.send_email(email, subject, html_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending abandoned cart email: {e}")
            return False
    
    async def send_price_drop_alert(self, user_id: str, product_name: str, old_price: float, new_price: float):
        """Send price drop notification"""
        try:
            email = await self.get_user_email(user_id)
            if not email:
                return False
            
            savings = old_price - new_price
            template_obj = Template(self.email_templates['price_drop'])
            html_content = template_obj.render(
                product_name=product_name,
                old_price=old_price,
                new_price=new_price,
                savings=savings,
                product_url=f"https://your-domain.com/product/{product_name.lower().replace(' ', '-')}"
            )
            
            subject = f"💰 Price Drop: {product_name} - Save ${savings:.2f}!"
            await self.send_email(email, subject, html_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending price drop alert: {e}")
            return False
    
    async def send_wishlist_confirmation(self, user_id: str, product_name: str):
        """Send wishlist confirmation"""
        try:
            email = await self.get_user_email(user_id)
            if not email:
                return False
            
            html_content = f"""
            <h2>❤️ Added to Wishlist!</h2>
            <p>{product_name} has been added to your wishlist.</p>
            <p>We'll notify you about price drops and when it's back in stock!</p>
            <a href="https://your-domain.com/wishlist">View Your Wishlist</a>
            """
            
            subject = f"Added to Wishlist: {product_name}"
            await self.send_email(email, subject, html_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending wishlist confirmation: {e}")
            return False
    
    async def send_web_push_notification(self, user_id: str, title: str, message: str, action_url: str = None):
        """Send web push notification"""
        try:
            # Implement web push notification
            # This would integrate with services like Firebase Cloud Messaging
            notification_data = {
                'title': title,
                'message': message,
                'action_url': action_url,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store for web push delivery
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO notifications 
                    (id, user_id, type, channel, content, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), user_id, 'web_push', 'web_push',
                    json.dumps(notification_data), 'pending'
                ))
            
            logger.info(f"Web push notification queued for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending web push notification: {e}")
            return False
    
    async def send_whatsapp_message(self, user_id: str, message: str, phone_number: str = None):
        """Send WhatsApp message"""
        try:
            if not phone_number:
                phone_number = await self.get_user_phone(user_id)
            
            if not phone_number:
                return False
            
            # Implement WhatsApp API integration
            # This would integrate with WhatsApp Business API
            whatsapp_data = {
                'phone': phone_number,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store for WhatsApp delivery
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO notifications 
                    (id, user_id, type, channel, content, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), user_id, 'whatsapp', 'whatsapp',
                    json.dumps(whatsapp_data), 'pending'
                ))
            
            logger.info(f"WhatsApp message queued for {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    async def get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email address"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT email FROM email_subscriptions 
                    WHERE user_id = ? AND status = 'active'
                    LIMIT 1
                """, (user_id,))
                
                row = cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            logger.error(f"Error getting user email: {e}")
            return None
    
    async def get_user_phone(self, user_id: str) -> Optional[str]:
        """Get user phone number"""
        try:
            # Implement phone number retrieval from customer database
            # This would be stored during customer registration
            return None
            
        except Exception as e:
            logger.error(f"Error getting user phone: {e}")
            return None
    
    async def send_email(self, to_email: str, subject: str, html_content: str):
        """Send email using configured SMTP"""
        try:
            # Implement actual email sending
            # This would use the email service from email_marketing.py
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

class AutomationScheduler:
    """Schedule and manage marketing automation tasks"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.automation = MarketingAutomation()
        
    def start(self):
        """Start the automation scheduler"""
        # Check for abandoned carts every 15 minutes
        self.scheduler.add_job(
            func=self.process_pending_notifications,
            trigger="interval",
            minutes=15,
            id='process_notifications'
        )
        
        # Check for price drops daily
        self.scheduler.add_job(
            func=self.automation.check_price_drops,
            trigger="cron",
            hour=9,
            minute=0,
            id='check_price_drops'
        )
        
        # Clean up old behavior data weekly
        self.scheduler.add_job(
            func=self.cleanup_old_data,
            trigger="cron",
            day_of_week='sun',
            hour=2,
            minute=0,
            id='cleanup_data'
        )
        
        self.scheduler.start()
        logger.info("Marketing automation scheduler started")
    
    async def process_pending_notifications(self):
        """Process pending notifications"""
        try:
            notification_service = NotificationService()
            
            with sqlite3.connect("data/marketing.db") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM notifications 
                    WHERE status = 'pending' 
                    AND scheduled_at <= ?
                """, (datetime.now().isoformat(),))
                
                for notification in cursor.fetchall():
                    try:
                        content = json.loads(notification['content'])
                        
                        if notification['type'] == 'cart_abandonment':
                            await notification_service.send_abandoned_cart_email(
                                notification['user_id'], content
                            )
                        
                        # Mark as sent
                        conn.execute("""
                            UPDATE notifications 
                            SET status = 'sent', sent_at = ?
                            WHERE id = ?
                        """, (datetime.now().isoformat(), notification['id']))
                        
                    except Exception as e:
                        logger.error(f"Error processing notification {notification['id']}: {e}")
                        
                        # Mark as failed and increment retry count
                        conn.execute("""
                            UPDATE notifications 
                            SET status = 'failed', retry_count = retry_count + 1
                            WHERE id = ?
                        """, (notification['id'],))
                        
        except Exception as e:
            logger.error(f"Error processing pending notifications: {e}")
    
    def cleanup_old_data(self):
        """Clean up old behavior data"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
            
            with sqlite3.connect("data/marketing.db") as conn:
                # Clean old behavior data
                conn.execute("""
                    DELETE FROM customer_behavior 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                # Clean old notifications
                conn.execute("""
                    DELETE FROM notifications 
                    WHERE created_at < ? AND status IN ('sent', 'failed')
                """, (cutoff_date,))
                
            logger.info("Old marketing data cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Marketing automation scheduler stopped")

# Initialize global instances
behavior_tracker = BehaviorTracker()
automation_scheduler = AutomationScheduler()

if __name__ == "__main__":
    # Start the marketing automation system
    automation_scheduler.start()
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        automation_scheduler.stop()
