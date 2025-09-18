#!/usr/bin/env python3
"""
Marketing Automation API Integration
Author: MiniMax Agent

This module adds marketing automation endpoints to the main API server.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
from datetime import datetime
import logging

# Import marketing automation
from .marketing_automation import BehaviorTracker, MarketingAutomation, NotificationService

logger = logging.getLogger(__name__)

# Pydantic models for API requests
class BehaviorEvent(BaseModel):
    userId: str
    sessionId: str
    eventType: str
    eventData: Dict[str, Any]
    pageUrl: Optional[str] = None
    userAgent: Optional[str] = None
    ipAddress: Optional[str] = None
    deviceType: Optional[str] = None
    referrer: Optional[str] = None

class BehaviorBatch(BaseModel):
    behaviors: List[BehaviorEvent]
    userId: str
    sessionId: str

class EmailRequest(BaseModel):
    userId: str
    type: str
    template: Optional[str] = None
    productData: Optional[Dict] = None
    cartData: Optional[List] = None
    cartTotal: Optional[float] = None
    oldPrice: Optional[float] = None
    newPrice: Optional[float] = None
    savings: Optional[float] = None
    timestamp: str

class WhatsAppRequest(BaseModel):
    userId: str
    message: str
    phoneNumber: Optional[str] = None
    timestamp: str

class PushSubscription(BaseModel):
    userId: str
    subscription: Dict[str, Any]
    timestamp: str

def add_marketing_routes(app: FastAPI):
    """Add marketing automation routes to the FastAPI app"""
    
    # Initialize marketing components
    behavior_tracker = BehaviorTracker()
    marketing_automation = MarketingAutomation()
    notification_service = NotificationService()
    
    @app.post("/api/marketing/track-behavior")
    async def track_behavior_batch(batch: BehaviorBatch, request: Request):
        """Track batch of behavior events"""
        try:
            client_ip = request.client.host
            
            for behavior in batch.behaviors:
                # Track each behavior event
                behavior_tracker.track_behavior(
                    user_id=behavior.userId,
                    session_id=behavior.sessionId,
                    event_type=behavior.eventType,
                    event_data=behavior.eventData,
                    page_url=behavior.pageUrl,
                    user_agent=behavior.userAgent,
                    ip_address=client_ip,
                    device_type=behavior.deviceType,
                    referrer=behavior.referrer
                )
            
            return {
                "status": "success",
                "tracked_events": len(batch.behaviors),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error tracking behavior batch: {e}")
            raise HTTPException(status_code=500, detail="Error tracking behavior")
    
    @app.post("/api/marketing/send-email")
    async def send_marketing_email(email_request: EmailRequest, background_tasks: BackgroundTasks):
        """Send marketing email"""
        try:
            if email_request.type == 'cart_abandonment':
                background_tasks.add_task(
                    notification_service.send_abandoned_cart_email,
                    email_request.userId,
                    {
                        'cart_data': json.dumps(email_request.cartData) if email_request.cartData else '[]',
                        'total_value': email_request.cartTotal or 0
                    },
                    email_request.template or 'abandoned_cart'
                )
            
            elif email_request.type == 'wishlist_confirmation':
                background_tasks.add_task(
                    notification_service.send_wishlist_confirmation,
                    email_request.userId,
                    email_request.productData.get('productName', 'Product') if email_request.productData else 'Product'
                )
            
            elif email_request.type == 'price_drop':
                background_tasks.add_task(
                    notification_service.send_price_drop_alert,
                    email_request.userId,
                    email_request.productData.get('productName', 'Product') if email_request.productData else 'Product',
                    email_request.oldPrice or 0,
                    email_request.newPrice or 0
                )
            
            return {
                "status": "scheduled",
                "message": f"Email of type '{email_request.type}' scheduled for delivery",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling email: {e}")
            raise HTTPException(status_code=500, detail="Error scheduling email")
    
    @app.post("/api/marketing/send-whatsapp")
    async def send_whatsapp_message(whatsapp_request: WhatsAppRequest, background_tasks: BackgroundTasks):
        """Send WhatsApp message"""
        try:
            background_tasks.add_task(
                notification_service.send_whatsapp_message,
                whatsapp_request.userId,
                whatsapp_request.message,
                whatsapp_request.phoneNumber
            )
            
            return {
                "status": "scheduled",
                "message": "WhatsApp message scheduled for delivery",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling WhatsApp message: {e}")
            raise HTTPException(status_code=500, detail="Error scheduling WhatsApp message")
    
    @app.post("/api/marketing/push-subscription")
    async def register_push_subscription(subscription: PushSubscription):
        """Register push notification subscription"""
        try:
            # Store push subscription in database
            # In a real implementation, this would save to the marketing database
            logger.info(f"Push subscription registered for user {subscription.userId}")
            
            return {
                "status": "success",
                "message": "Push subscription registered",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error registering push subscription: {e}")
            raise HTTPException(status_code=500, detail="Error registering push subscription")
    
    @app.get("/api/marketing/customer-segments/{user_id}")
    async def get_customer_segments(user_id: str):
        """Get customer segment information"""
        try:
            segments = behavior_tracker.get_customer_segment(user_id)
            
            return {
                "userId": user_id,
                "segments": segments,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting customer segments: {e}")
            raise HTTPException(status_code=500, detail="Error getting customer segments")
    
    @app.get("/api/marketing/analytics/{user_id}")
    async def get_user_analytics(user_id: str, days: int = 30):
        """Get user behavior analytics"""
        try:
            # In a real implementation, this would query the behavior database
            # and return analytics data for the user
            
            analytics = {
                "userId": user_id,
                "period": f"last_{days}_days",
                "metrics": {
                    "page_views": 0,
                    "product_views": 0,
                    "cart_additions": 0,
                    "purchases": 0,
                    "wishlist_additions": 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            raise HTTPException(status_code=500, detail="Error getting user analytics")
    
    @app.get("/api/marketing/notifications/{user_id}")
    async def get_user_notifications(user_id: str, limit: int = 10):
        """Get user notifications history"""
        try:
            # In a real implementation, this would query the notifications database
            notifications = []
            
            return {
                "userId": user_id,
                "notifications": notifications,
                "count": len(notifications),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            raise HTTPException(status_code=500, detail="Error getting user notifications")
    
    @app.post("/api/marketing/trigger-campaign")
    async def trigger_marketing_campaign(campaign_data: Dict[str, Any], background_tasks: BackgroundTasks):
        """Trigger a specific marketing campaign"""
        try:
            campaign_type = campaign_data.get('type')
            user_ids = campaign_data.get('user_ids', [])
            
            if not campaign_type or not user_ids:
                raise HTTPException(status_code=400, detail="Campaign type and user IDs required")
            
            # Schedule campaign execution
            background_tasks.add_task(
                execute_marketing_campaign,
                campaign_type,
                user_ids,
                campaign_data
            )
            
            return {
                "status": "scheduled",
                "campaign_type": campaign_type,
                "target_users": len(user_ids),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error triggering marketing campaign: {e}")
            raise HTTPException(status_code=500, detail="Error triggering marketing campaign")
    
    @app.get("/api/marketing/stats")
    async def get_marketing_stats():
        """Get overall marketing statistics"""
        try:
            # In a real implementation, this would query the marketing database
            # for comprehensive statistics
            
            stats = {
                "total_tracked_events": 0,
                "active_users_today": 0,
                "emails_sent_today": 0,
                "push_notifications_sent_today": 0,
                "cart_abandonment_rate": 0.0,
                "email_open_rate": 0.0,
                "conversion_rate": 0.0,
                "timestamp": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting marketing stats: {e}")
            raise HTTPException(status_code=500, detail="Error getting marketing stats")

async def execute_marketing_campaign(campaign_type: str, user_ids: List[str], campaign_data: Dict[str, Any]):
    """Execute marketing campaign in background"""
    try:
        notification_service = NotificationService()
        
        if campaign_type == 'product_promotion':
            # Send product promotion emails
            for user_id in user_ids:
                await notification_service.send_email(
                    await notification_service.get_user_email(user_id),
                    campaign_data.get('subject', 'Special Offer'),
                    campaign_data.get('content', 'Check out our latest products!')
                )
        
        elif campaign_type == 'price_drop_batch':
            # Send batch price drop alerts
            for user_id in user_ids:
                product_data = campaign_data.get('product_data', {})
                await notification_service.send_price_drop_alert(
                    user_id,
                    product_data.get('name', 'Product'),
                    campaign_data.get('old_price', 0),
                    campaign_data.get('new_price', 0)
                )
        
        logger.info(f"Marketing campaign '{campaign_type}' executed for {len(user_ids)} users")
        
    except Exception as e:
        logger.error(f"Error executing marketing campaign '{campaign_type}': {e}")

# Service Worker for Push Notifications
SERVICE_WORKER_JS = """
self.addEventListener('push', function(event) {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.message,
            icon: '/images/logo-notification.png',
            badge: '/images/badge.png',
            tag: 'nle-bike-notification',
            requireInteraction: true,
            actions: [
                { action: 'view', title: 'View Details' },
                { action: 'dismiss', title: 'Dismiss' }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action === 'view') {
        // Open the app or specific page
        event.waitUntil(
            clients.openWindow(event.notification.data?.url || '/')
        );
    }
});
"""

def create_service_worker_file():
    """Create service worker file for push notifications"""
    try:
        with open('deployment-package/sw.js', 'w') as f:
            f.write(SERVICE_WORKER_JS)
        logger.info("Service worker file created for push notifications")
    except Exception as e:
        logger.error(f"Error creating service worker file: {e}")

if __name__ == "__main__":
    # Create service worker file
    create_service_worker_file()
    print("Marketing automation API integration ready!")
