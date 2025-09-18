#!/usr/bin/env python3
"""
Email Marketing and Automation System
Author: MiniMax Agent

Handles email campaigns, abandoned cart recovery, newsletters, and customer communications
"""

import os
import json
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from jinja2 import Template
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class EmailTemplate:
    name: str
    subject: str
    html_content: str
    text_content: str
    variables: List[str]

@dataclass
class EmailCampaign:
    id: str
    name: str
    template: str
    recipients: List[str]
    status: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    stats: Dict[str, int]

class EmailService:
    """Core email sending service"""
    
    def __init__(self, smtp_config: Dict[str, str]):
        self.smtp_config = smtp_config
        
    async def send_email(self, to_email: str, subject: str, html_content: str, 
                        text_content: str = None, attachments: List = None) -> bool:
        """Send an email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    with open(attachment['path'], 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["name"]}'
                        )
                        msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

class EmailTemplateManager:
    """Manage email templates"""
    
    def __init__(self):
        self.templates = self.load_default_templates()
    
    def load_default_templates(self) -> Dict[str, EmailTemplate]:
        """Load default email templates"""
        return {
            'welcome': EmailTemplate(
                name='Welcome Email',
                subject='Welcome to ElectroRide Pro! 🚀',
                html_content=self.get_welcome_template(),
                text_content='Welcome to ElectroRide Pro! Thank you for subscribing to our newsletter.',
                variables=['customer_name', 'discount_code']
            ),
            'abandoned_cart': EmailTemplate(
                name='Abandoned Cart Recovery',
                subject='You left something in your cart 🛒',
                html_content=self.get_abandoned_cart_template(),
                text_content='You have items waiting in your cart. Complete your purchase now!',
                variables=['customer_name', 'cart_items', 'cart_total', 'checkout_url']
            ),
            'order_confirmation': EmailTemplate(
                name='Order Confirmation',
                subject='Order Confirmed - #{order_id}',
                html_content=self.get_order_confirmation_template(),
                text_content='Your order has been confirmed. Order ID: {order_id}',
                variables=['customer_name', 'order_id', 'order_items', 'total_amount', 'shipping_address']
            ),
            'shipping_notification': EmailTemplate(
                name='Shipping Notification',
                subject='Your order is on the way! 🚚',
                html_content=self.get_shipping_template(),
                text_content='Your order has been shipped. Tracking number: {tracking_number}',
                variables=['customer_name', 'order_id', 'tracking_number', 'tracking_url']
            ),
            'newsletter': EmailTemplate(
                name='Newsletter',
                subject='Latest Updates from ElectroRide Pro',
                html_content=self.get_newsletter_template(),
                text_content='Check out our latest products and offers!',
                variables=['customer_name', 'featured_products', 'special_offers']
            )
        }
    
    def get_welcome_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to ElectroRide Pro</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background: #f8fafc; }
                .container { max-width: 600px; margin: 0 auto; background: white; }
                .header { background: linear-gradient(135deg, #2563eb, #f59e0b); padding: 2rem; text-align: center; }
                .header h1 { color: white; margin: 0; font-size: 2rem; }
                .content { padding: 2rem; }
                .button { display: inline-block; background: #2563eb; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px; margin: 1rem 0; }
                .footer { background: #f1f5f9; padding: 1rem; text-align: center; color: #64748b; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚡ ElectroRide Pro</h1>
                    <p style="color: white; margin: 0;">Premium Electric Bikes</p>
                </div>
                <div class="content">
                    <h2>Welcome, {{ customer_name }}!</h2>
                    <p>Thank you for joining the ElectroRide Pro community! We're excited to have you on board.</p>
                    <p>As a welcome gift, here's a special discount code just for you:</p>
                    <div style="background: #f0f9ff; border: 2px dashed #2563eb; padding: 1rem; text-align: center; margin: 1rem 0;">
                        <strong style="font-size: 1.5rem; color: #2563eb;">{{ discount_code }}</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #64748b;">Get 10% off your first order!</p>
                    </div>
                    <p>Explore our premium collection of electric bikes and find the perfect ride for your urban adventures.</p>
                    <a href="https://electroridepro.com/products" class="button">Shop Now</a>
                    <p>Best regards,<br>The ElectroRide Pro Team</p>
                </div>
                <div class="footer">
                    <p>Follow us on social media for the latest updates!</p>
                    <p>You can unsubscribe from these emails at any time.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_abandoned_cart_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Complete Your Purchase</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background: #f8fafc; }
                .container { max-width: 600px; margin: 0 auto; background: white; }
                .header { background: #1f2937; padding: 2rem; text-align: center; }
                .header h1 { color: white; margin: 0; }
                .content { padding: 2rem; }
                .cart-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin: 1rem 0; display: flex; align-items: center; }
                .cart-item img { width: 80px; height: 80px; object-fit: cover; border-radius: 8px; margin-right: 1rem; }
                .button { display: inline-block; background: #10b981; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px; margin: 1rem 0; }
                .urgency { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; margin: 1rem 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛒 Don't Miss Out!</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ customer_name }},</h2>
                    <p>You left some amazing items in your cart. Don't let them get away!</p>
                    
                    <div class="urgency">
                        <strong>⏰ Limited Time:</strong> Your cart will expire in 24 hours!
                    </div>
                    
                    <h3>Your Cart Items:</h3>
                    {% for item in cart_items %}
                    <div class="cart-item">
                        <img src="{{ item.image }}" alt="{{ item.name }}">
                        <div>
                            <h4 style="margin: 0;">{{ item.name }}</h4>
                            <p style="margin: 0.5rem 0; color: #64748b;">Quantity: {{ item.quantity }}</p>
                            <p style="margin: 0; font-weight: bold; color: #2563eb;">€{{ item.price }}</p>
                        </div>
                    </div>
                    {% endfor %}
                    
                    <div style="text-align: right; border-top: 2px solid #e5e7eb; padding-top: 1rem; margin-top: 1rem;">
                        <h3>Total: €{{ cart_total }}</h3>
                    </div>
                    
                    <p>Complete your purchase now and get <strong>FREE SHIPPING</strong> on this order!</p>
                    <a href="{{ checkout_url }}" class="button">Complete Purchase</a>
                    
                    <p>Need help? Reply to this email and our support team will assist you.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_order_confirmation_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Order Confirmation</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background: #f8fafc; }
                .container { max-width: 600px; margin: 0 auto; background: white; }
                .header { background: #10b981; padding: 2rem; text-align: center; }
                .header h1 { color: white; margin: 0; }
                .content { padding: 2rem; }
                .order-details { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
                .item { border-bottom: 1px solid #e5e7eb; padding: 1rem 0; }
                .total { background: #f8fafc; padding: 1rem; margin: 1rem 0; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Order Confirmed!</h1>
                    <p style="color: white; margin: 0;">Order #{{ order_id }}</p>
                </div>
                <div class="content">
                    <h2>Thank you, {{ customer_name }}!</h2>
                    <p>Your order has been successfully placed and confirmed. We'll start processing it right away.</p>
                    
                    <div class="order-details">
                        <h3>Order Details</h3>
                        <p><strong>Order ID:</strong> {{ order_id }}</p>
                        <p><strong>Order Date:</strong> {{ order_date }}</p>
                        <p><strong>Expected Delivery:</strong> 5-7 business days</p>
                    </div>
                    
                    <h3>Items Ordered:</h3>
                    {% for item in order_items %}
                    <div class="item">
                        <strong>{{ item.name }}</strong><br>
                        Quantity: {{ item.quantity }} | Price: €{{ item.price }}
                    </div>
                    {% endfor %}
                    
                    <div class="total">
                        <h3>Order Total: €{{ total_amount }}</h3>
                    </div>
                    
                    <h3>Shipping Address:</h3>
                    <p>
                        {{ shipping_address.name }}<br>
                        {{ shipping_address.street }}<br>
                        {{ shipping_address.city }}, {{ shipping_address.postal_code }}<br>
                        {{ shipping_address.country }}
                    </p>
                    
                    <p>You'll receive another email with tracking information once your order ships.</p>
                    <p>Questions? Contact our support team at support@electroridepro.com</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_shipping_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Order is Shipping</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background: #f8fafc; }
                .container { max-width: 600px; margin: 0 auto; background: white; }
                .header { background: #3b82f6; padding: 2rem; text-align: center; }
                .header h1 { color: white; margin: 0; }
                .content { padding: 2rem; }
                .tracking { background: #eff6ff; border: 2px solid #3b82f6; border-radius: 8px; padding: 1.5rem; text-align: center; margin: 1rem 0; }
                .button { display: inline-block; background: #3b82f6; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px; margin: 1rem 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚚 Your Order is On the Way!</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ customer_name }},</h2>
                    <p>Great news! Your order #{{ order_id }} has been shipped and is on its way to you.</p>
                    
                    <div class="tracking">
                        <h3>Tracking Number</h3>
                        <p style="font-size: 1.5rem; font-weight: bold; color: #3b82f6; margin: 0.5rem 0;">{{ tracking_number }}</p>
                        <a href="{{ tracking_url }}" class="button">Track Your Package</a>
                    </div>
                    
                    <p>Your package should arrive within the estimated delivery time. You can track its progress using the tracking number above.</p>
                    
                    <h3>What's Next?</h3>
                    <ul>
                        <li>Track your package using the link above</li>
                        <li>Ensure someone is available to receive the delivery</li>
                        <li>Contact us if you have any questions</li>
                    </ul>
                    
                    <p>Thank you for choosing ElectroRide Pro!</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_newsletter_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ElectroRide Pro Newsletter</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background: #f8fafc; }
                .container { max-width: 600px; margin: 0 auto; background: white; }
                .header { background: linear-gradient(135deg, #2563eb, #f59e0b); padding: 2rem; text-align: center; }
                .header h1 { color: white; margin: 0; }
                .content { padding: 2rem; }
                .product { border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
                .product img { width: 100%; height: 200px; object-fit: cover; border-radius: 8px; }
                .button { display: inline-block; background: #2563eb; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 8px; margin: 0.5rem 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚡ ElectroRide Pro Newsletter</h1>
                    <p style="color: white; margin: 0;">Latest Updates & Offers</p>
                </div>
                <div class="content">
                    <h2>Hi {{ customer_name }},</h2>
                    <p>Check out what's new at ElectroRide Pro this month!</p>
                    
                    <h3>🎆 Featured Products</h3>
                    {% for product in featured_products %}
                    <div class="product">
                        <img src="{{ product.image }}" alt="{{ product.name }}">
                        <h4>{{ product.name }}</h4>
                        <p>{{ product.description }}</p>
                        <p><strong>€{{ product.price }}</strong> <span style="text-decoration: line-through; color: #64748b;">€{{ product.original_price }}</span></p>
                        <a href="{{ product.url }}" class="button">Learn More</a>
                    </div>
                    {% endfor %}
                    
                    <h3>🎁 Special Offers</h3>
                    {% for offer in special_offers %}
                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; margin: 1rem 0;">
                        <h4>{{ offer.title }}</h4>
                        <p>{{ offer.description }}</p>
                        <p><strong>Code: {{ offer.code }}</strong></p>
                    </div>
                    {% endfor %}
                    
                    <p>Don't miss out on these amazing deals!</p>
                    <a href="https://electroridepro.com" class="button">Shop Now</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> tuple:
        """Render email template with variables"""
        if template_name not in self.templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = self.templates[template_name]
        
        # Render HTML content
        html_template = Template(template.html_content)
        html_content = html_template.render(**variables)
        
        # Render text content
        text_template = Template(template.text_content)
        text_content = text_template.render(**variables)
        
        # Render subject
        subject_template = Template(template.subject)
        subject = subject_template.render(**variables)
        
        return subject, html_content, text_content

class EmailAutomationManager:
    """Manage automated email campaigns and triggers"""
    
    def __init__(self, email_service: EmailService, template_manager: EmailTemplateManager):
        self.email_service = email_service
        self.template_manager = template_manager
        self.db_path = "data/email_automation.db"
        self.init_database()
    
    def init_database(self):
        """Initialize email automation database"""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_subscribers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    subscribed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    tags TEXT,
                    last_email_sent TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_campaigns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    template TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    scheduled_at TEXT,
                    sent_at TEXT,
                    recipients_count INTEGER DEFAULT 0,
                    opened_count INTEGER DEFAULT 0,
                    clicked_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS abandoned_carts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_email TEXT NOT NULL,
                    cart_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    email_sent TEXT,
                    recovered INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient TEXT NOT NULL,
                    template TEXT NOT NULL,
                    subject TEXT,
                    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    success INTEGER,
                    error_message TEXT
                )
            """)
    
    async def subscribe_user(self, email: str, name: str = None, tags: List[str] = None) -> bool:
        """Subscribe a user to the email list"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                tags_str = json.dumps(tags) if tags else None
                conn.execute("""
                    INSERT OR REPLACE INTO email_subscribers (email, name, tags)
                    VALUES (?, ?, ?)
                """, (email, name, tags_str))
            
            # Send welcome email
            await self.send_welcome_email(email, name or 'Valued Customer')
            
            return True
        except Exception as e:
            logger.error(f"Error subscribing user {email}: {e}")
            return False
    
    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email to new subscriber"""
        try:
            variables = {
                'customer_name': name,
                'discount_code': 'WELCOME10'
            }
            
            subject, html_content, text_content = self.template_manager.render_template(
                'welcome', variables
            )
            
            success = await self.email_service.send_email(
                email, subject, html_content, text_content
            )
            
            self.log_email(email, 'welcome', subject, success)
            return success
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {email}: {e}")
            return False
    
    async def track_abandoned_cart(self, customer_email: str, cart_data: Dict) -> None:
        """Track abandoned cart for recovery email"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO abandoned_carts (customer_email, cart_data)
                    VALUES (?, ?)
                """, (customer_email, json.dumps(cart_data)))
            
            # Schedule abandoned cart email (after 1 hour)
            await asyncio.sleep(3600)  # In production, use a task queue
            await self.send_abandoned_cart_email(customer_email, cart_data)
            
        except Exception as e:
            logger.error(f"Error tracking abandoned cart for {customer_email}: {e}")
    
    async def send_abandoned_cart_email(self, customer_email: str, cart_data: Dict) -> bool:
        """Send abandoned cart recovery email"""
        try:
            # Check if email was already sent
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id FROM abandoned_carts 
                    WHERE customer_email = ? AND email_sent IS NOT NULL 
                    ORDER BY created_at DESC LIMIT 1
                """, (customer_email,))
                
                if cursor.fetchone():
                    return False  # Email already sent recently
            
            variables = {
                'customer_name': cart_data.get('customer_name', 'Valued Customer'),
                'cart_items': cart_data.get('items', []),
                'cart_total': cart_data.get('total', 0),
                'checkout_url': f"https://electroridepro.com/checkout?recover={customer_email}"
            }
            
            subject, html_content, text_content = self.template_manager.render_template(
                'abandoned_cart', variables
            )
            
            success = await self.email_service.send_email(
                customer_email, subject, html_content, text_content
            )
            
            if success:
                # Mark email as sent
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE abandoned_carts 
                        SET email_sent = CURRENT_TIMESTAMP 
                        WHERE customer_email = ?
                    """, (customer_email,))
            
            self.log_email(customer_email, 'abandoned_cart', subject, success)
            return success
            
        except Exception as e:
            logger.error(f"Error sending abandoned cart email to {customer_email}: {e}")
            return False
    
    async def send_order_confirmation(self, order_data: Dict) -> bool:
        """Send order confirmation email"""
        try:
            variables = {
                'customer_name': order_data['customer_info']['name'],
                'order_id': order_data['id'],
                'order_date': datetime.now().strftime('%B %d, %Y'),
                'order_items': order_data['items'],
                'total_amount': order_data['total'],
                'shipping_address': order_data['shipping_address']
            }
            
            subject, html_content, text_content = self.template_manager.render_template(
                'order_confirmation', variables
            )
            
            success = await self.email_service.send_email(
                order_data['customer_info']['email'], subject, html_content, text_content
            )
            
            self.log_email(
                order_data['customer_info']['email'], 
                'order_confirmation', 
                subject, 
                success
            )
            return success
            
        except Exception as e:
            logger.error(f"Error sending order confirmation: {e}")
            return False
    
    async def send_shipping_notification(self, order_data: Dict, tracking_number: str) -> bool:
        """Send shipping notification email"""
        try:
            variables = {
                'customer_name': order_data['customer_info']['name'],
                'order_id': order_data['id'],
                'tracking_number': tracking_number,
                'tracking_url': f"https://track.example.com/{tracking_number}"
            }
            
            subject, html_content, text_content = self.template_manager.render_template(
                'shipping_notification', variables
            )
            
            success = await self.email_service.send_email(
                order_data['customer_info']['email'], subject, html_content, text_content
            )
            
            self.log_email(
                order_data['customer_info']['email'], 
                'shipping_notification', 
                subject, 
                success
            )
            return success
            
        except Exception as e:
            logger.error(f"Error sending shipping notification: {e}")
            return False
    
    async def send_newsletter(self, campaign_data: Dict) -> Dict:
        """Send newsletter to all subscribers"""
        try:
            # Get all active subscribers
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT email, name FROM email_subscribers 
                    WHERE status = 'active'
                """)
                subscribers = cursor.fetchall()
            
            sent_count = 0
            failed_count = 0
            
            for email, name in subscribers:
                try:
                    variables = {
                        'customer_name': name or 'Valued Customer',
                        'featured_products': campaign_data.get('featured_products', []),
                        'special_offers': campaign_data.get('special_offers', [])
                    }
                    
                    subject, html_content, text_content = self.template_manager.render_template(
                        'newsletter', variables
                    )
                    
                    success = await self.email_service.send_email(
                        email, subject, html_content, text_content
                    )
                    
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                    
                    self.log_email(email, 'newsletter', subject, success)
                    
                    # Small delay to avoid overwhelming SMTP server
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error sending newsletter to {email}: {e}")
                    failed_count += 1
            
            return {
                'sent': sent_count,
                'failed': failed_count,
                'total': len(subscribers)
            }
            
        except Exception as e:
            logger.error(f"Error sending newsletter: {e}")
            return {'sent': 0, 'failed': 0, 'total': 0}
    
    def log_email(self, recipient: str, template: str, subject: str, success: bool, error: str = None):
        """Log email sending attempt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO email_logs (recipient, template, subject, success, error_message)
                    VALUES (?, ?, ?, ?, ?)
                """, (recipient, template, subject, 1 if success else 0, error))
        except Exception as e:
            logger.error(f"Error logging email: {e}")
    
    def get_email_stats(self) -> Dict:
        """Get email statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total subscribers
                cursor = conn.execute("SELECT COUNT(*) FROM email_subscribers WHERE status = 'active'")
                total_subscribers = cursor.fetchone()[0]
                
                # Emails sent today
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM email_logs 
                    WHERE DATE(sent_at) = DATE('now') AND success = 1
                """)
                emails_today = cursor.fetchone()[0]
                
                # Success rate
                cursor = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                        COUNT(*) as total
                    FROM email_logs 
                    WHERE DATE(sent_at) >= DATE('now', '-7 days')
                """)
                result = cursor.fetchone()
                success_rate = (result[0] / result[1] * 100) if result[1] > 0 else 0
                
                # Abandoned cart recovery rate
                cursor = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN recovered = 1 THEN 1 ELSE 0 END) as recovered,
                        COUNT(*) as total
                    FROM abandoned_carts 
                    WHERE email_sent IS NOT NULL
                """)
                result = cursor.fetchone()
                recovery_rate = (result[0] / result[1] * 100) if result[1] > 0 else 0
                
                return {
                    'total_subscribers': total_subscribers,
                    'emails_sent_today': emails_today,
                    'success_rate': round(success_rate, 1),
                    'cart_recovery_rate': round(recovery_rate, 1)
                }
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            return {
                'total_subscribers': 0,
                'emails_sent_today': 0,
                'success_rate': 0,
                'cart_recovery_rate': 0
            }

# Example usage
if __name__ == "__main__":
    # SMTP configuration
    smtp_config = {
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'from_email': 'noreply@electroridepro.com'
    }
    
    # Initialize email system
    email_service = EmailService(smtp_config)
    template_manager = EmailTemplateManager()
    automation_manager = EmailAutomationManager(email_service, template_manager)
    
    print("Email marketing system initialized successfully!")