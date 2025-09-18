#!/usr/bin/env python3
"""
Payment Gateway Integration Module
Author: MiniMax Agent

Integrates multiple payment gateways including Stripe, PayPal, Apple Pay, Google Pay
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
import logging
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib
import hmac

# External payment libraries (install with pip)
try:
    import stripe
except ImportError:
    stripe = None

try:
    import paypalrestsdk
except ImportError:
    paypalrestsdk = None

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    BANK_TRANSFER = "bank_transfer"

@dataclass
class PaymentRequest:
    amount: Decimal
    currency: str
    customer_email: str
    payment_method: PaymentMethod
    order_id: str
    customer_info: Dict[str, Any]
    billing_address: Dict[str, Any]
    items: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PaymentResponse:
    success: bool
    payment_id: str
    status: PaymentStatus
    message: str
    transaction_id: Optional[str] = None
    redirect_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PaymentGatewayManager:
    """
    Unified payment gateway manager supporting multiple payment providers
    """
    
    def __init__(self, config: Dict[str, Dict[str, str]]):
        self.config = config
        self.gateways = {}
        self.initialize_gateways()
    
    def initialize_gateways(self):
        """Initialize all configured payment gateways"""
        if 'stripe' in self.config and stripe:
            self.gateways['stripe'] = StripeGateway(self.config['stripe'])
        
        if 'paypal' in self.config and paypalrestsdk:
            self.gateways['paypal'] = PayPalGateway(self.config['paypal'])
        
        if 'apple_pay' in self.config:
            self.gateways['apple_pay'] = ApplePayGateway(self.config['apple_pay'])
        
        if 'google_pay' in self.config:
            self.gateways['google_pay'] = GooglePayGateway(self.config['google_pay'])
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process payment through the specified gateway"""
        gateway_name = request.payment_method.value
        
        if gateway_name not in self.gateways:
            return PaymentResponse(
                success=False,
                payment_id="",
                status=PaymentStatus.FAILED,
                message=f"Payment gateway {gateway_name} not configured"
            )
        
        gateway = self.gateways[gateway_name]
        
        try:
            return await gateway.process_payment(request)
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            return PaymentResponse(
                success=False,
                payment_id="",
                status=PaymentStatus.FAILED,
                message=f"Payment processing failed: {str(e)}"
            )
    
    async def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> PaymentResponse:
        """Refund a payment"""
        # Implementation for refunds
        pass
    
    async def get_payment_status(self, payment_id: str) -> PaymentResponse:
        """Get status of a payment"""
        # Implementation for status checking
        pass

class StripeGateway:
    """Stripe payment gateway implementation"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        if stripe:
            stripe.api_key = config.get('secret_key')
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process payment through Stripe"""
        if not stripe:
            raise Exception("Stripe library not installed")
        
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(request.amount * 100),  # Convert to cents
                currency=request.currency.lower(),
                customer_email=request.customer_email,
                metadata={
                    'order_id': request.order_id,
                    **(request.metadata or {})
                },
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            return PaymentResponse(
                success=True,
                payment_id=intent.id,
                status=PaymentStatus.PENDING,
                message="Payment intent created successfully",
                transaction_id=intent.id,
                metadata={
                    'client_secret': intent.client_secret,
                    'publishable_key': self.config.get('publishable_key')
                }
            )
            
        except stripe.error.StripeError as e:
            return PaymentResponse(
                success=False,
                payment_id="",
                status=PaymentStatus.FAILED,
                message=f"Stripe error: {str(e)}"
            )
    
    async def confirm_payment(self, payment_intent_id: str) -> PaymentResponse:
        """Confirm a Stripe payment"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                return PaymentResponse(
                    success=True,
                    payment_id=intent.id,
                    status=PaymentStatus.COMPLETED,
                    message="Payment completed successfully",
                    transaction_id=intent.id
                )
            else:
                return PaymentResponse(
                    success=False,
                    payment_id=intent.id,
                    status=PaymentStatus.FAILED,
                    message=f"Payment status: {intent.status}"
                )
                
        except stripe.error.StripeError as e:
            return PaymentResponse(
                success=False,
                payment_id="",
                status=PaymentStatus.FAILED,
                message=f"Stripe error: {str(e)}"
            )

class PayPalGateway:
    """PayPal payment gateway implementation"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        if paypalrestsdk:
            paypalrestsdk.configure({
                "mode": config.get('mode', 'sandbox'),
                "client_id": config.get('client_id'),
                "client_secret": config.get('client_secret')
            })
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process payment through PayPal"""
        if not paypalrestsdk:
            raise Exception("PayPal SDK not installed")
        
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal",
                    "payer_info": {
                        "email": request.customer_email
                    }
                },
                "redirect_urls": {
                    "return_url": self.config.get('return_url'),
                    "cancel_url": self.config.get('cancel_url')
                },
                "transactions": [{
                    "item_list": {
                        "items": [
                            {
                                "name": item['name'],
                                "sku": item['id'],
                                "price": str(item['price']),
                                "currency": request.currency,
                                "quantity": item['quantity']
                            } for item in request.items
                        ]
                    },
                    "amount": {
                        "total": str(request.amount),
                        "currency": request.currency
                    },
                    "description": f"Order {request.order_id}"
                }]
            })
            
            if payment.create():
                # Find approval URL
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return PaymentResponse(
                    success=True,
                    payment_id=payment.id,
                    status=PaymentStatus.PENDING,
                    message="PayPal payment created successfully",
                    redirect_url=approval_url
                )
            else:
                return PaymentResponse(
                    success=False,
                    payment_id="",
                    status=PaymentStatus.FAILED,
                    message=f"PayPal error: {payment.error}"
                )
                
        except Exception as e:
            return PaymentResponse(
                success=False,
                payment_id="",
                status=PaymentStatus.FAILED,
                message=f"PayPal error: {str(e)}"
            )

class ApplePayGateway:
    """Apple Pay gateway implementation"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process Apple Pay payment"""
        # Apple Pay integration would require Apple Pay JS and merchant validation
        # This is a simplified implementation
        
        return PaymentResponse(
            success=True,
            payment_id=f"apple_pay_{request.order_id}",
            status=PaymentStatus.PENDING,
            message="Apple Pay integration required",
            metadata={
                'merchant_id': self.config.get('merchant_id'),
                'supported_networks': ['visa', 'mastercard', 'amex']
            }
        )

class GooglePayGateway:
    """Google Pay gateway implementation"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Process Google Pay payment"""
        # Google Pay integration would require Google Pay API setup
        # This is a simplified implementation
        
        return PaymentResponse(
            success=True,
            payment_id=f"google_pay_{request.order_id}",
            status=PaymentStatus.PENDING,
            message="Google Pay integration required",
            metadata={
                'merchant_id': self.config.get('merchant_id'),
                'gateway': 'stripe'  # Usually processed through another gateway
            }
        )

class ShippingManager:
    """Manage shipping options and calculations"""
    
    def __init__(self):
        self.shipping_methods = {
            'standard': {
                'name': 'Standard Shipping',
                'price': Decimal('9.99'),
                'delivery_time': '5-7 business days',
                'description': 'Standard delivery via postal service'
            },
            'express': {
                'name': 'Express Shipping',
                'price': Decimal('19.99'),
                'delivery_time': '2-3 business days',
                'description': 'Fast delivery via express courier'
            },
            'overnight': {
                'name': 'Overnight Shipping',
                'price': Decimal('39.99'),
                'delivery_time': '1 business day',
                'description': 'Next business day delivery'
            },
            'free': {
                'name': 'Free Shipping',
                'price': Decimal('0.00'),
                'delivery_time': '7-10 business days',
                'description': 'Free standard shipping (orders over €100)',
                'min_order': Decimal('100.00')
            }
        }
    
    def get_shipping_options(self, order_total: Decimal, destination_country: str = 'DE') -> List[Dict]:
        """Get available shipping options for an order"""
        options = []
        
        for method_id, method in self.shipping_methods.items():
            # Check if free shipping is available
            if method_id == 'free' and order_total < method.get('min_order', Decimal('0')):
                continue
            
            # Apply country-specific pricing (simplified)
            price = method['price']
            if destination_country not in ['DE', 'FR', 'ES', 'IT', 'NL']:  # EU countries
                price = price * Decimal('1.5')  # International shipping
            
            options.append({
                'id': method_id,
                'name': method['name'],
                'price': float(price),
                'delivery_time': method['delivery_time'],
                'description': method['description']
            })
        
        return options
    
    def calculate_shipping_cost(self, method_id: str, order_total: Decimal, destination_country: str = 'DE') -> Decimal:
        """Calculate shipping cost for a specific method"""
        if method_id not in self.shipping_methods:
            raise ValueError(f"Unknown shipping method: {method_id}")
        
        method = self.shipping_methods[method_id]
        
        # Free shipping logic
        if method_id == 'free' and order_total >= method.get('min_order', Decimal('0')):
            return Decimal('0.00')
        
        # Base price
        price = method['price']
        
        # International shipping surcharge
        if destination_country not in ['DE', 'FR', 'ES', 'IT', 'NL']:
            price = price * Decimal('1.5')
        
        return price

class CouponManager:
    """Manage discount coupons and promotional codes"""
    
    def __init__(self):
        self.coupons = {
            'WELCOME10': {
                'discount_type': 'percentage',
                'discount_value': Decimal('0.10'),
                'min_order': Decimal('0'),
                'max_uses': 1000,
                'used_count': 0,
                'active': True,
                'expires': None
            },
            'SAVE20': {
                'discount_type': 'percentage',
                'discount_value': Decimal('0.20'),
                'min_order': Decimal('500'),
                'max_uses': 500,
                'used_count': 0,
                'active': True,
                'expires': None
            },
            'FREESHIP': {
                'discount_type': 'free_shipping',
                'discount_value': Decimal('0'),
                'min_order': Decimal('0'),
                'max_uses': None,
                'used_count': 0,
                'active': True,
                'expires': None
            },
            'NEWBIE15': {
                'discount_type': 'percentage',
                'discount_value': Decimal('0.15'),
                'min_order': Decimal('200'),
                'max_uses': 200,
                'used_count': 0,
                'active': True,
                'expires': None
            }
        }
    
    def validate_coupon(self, code: str, order_total: Decimal) -> Dict:
        """Validate a coupon code"""
        code = code.upper().strip()
        
        if code not in self.coupons:
            return {'valid': False, 'message': 'Invalid coupon code'}
        
        coupon = self.coupons[code]
        
        if not coupon['active']:
            return {'valid': False, 'message': 'Coupon is no longer active'}
        
        if coupon['expires'] and datetime.now() > coupon['expires']:
            return {'valid': False, 'message': 'Coupon has expired'}
        
        if coupon['max_uses'] and coupon['used_count'] >= coupon['max_uses']:
            return {'valid': False, 'message': 'Coupon usage limit reached'}
        
        if order_total < coupon['min_order']:
            return {
                'valid': False, 
                'message': f'Minimum order of €{coupon["min_order"]} required'
            }
        
        return {'valid': True, 'coupon': coupon}
    
    def apply_coupon(self, code: str, order_total: Decimal, shipping_cost: Decimal = Decimal('0')) -> Dict:
        """Apply a coupon and calculate discount"""
        validation = self.validate_coupon(code, order_total)
        
        if not validation['valid']:
            return validation
        
        coupon = validation['coupon']
        discount_amount = Decimal('0')
        free_shipping = False
        
        if coupon['discount_type'] == 'percentage':
            discount_amount = order_total * coupon['discount_value']
        elif coupon['discount_type'] == 'fixed':
            discount_amount = min(coupon['discount_value'], order_total)
        elif coupon['discount_type'] == 'free_shipping':
            free_shipping = True
            discount_amount = shipping_cost
        
        return {
            'valid': True,
            'discount_amount': float(discount_amount),
            'free_shipping': free_shipping,
            'message': f'Coupon applied successfully'
        }
    
    def use_coupon(self, code: str):
        """Mark a coupon as used"""
        code = code.upper().strip()
        if code in self.coupons:
            self.coupons[code]['used_count'] += 1

class OrderManager:
    """Manage order processing and fulfillment"""
    
    def __init__(self, payment_manager: PaymentGatewayManager, shipping_manager: ShippingManager):
        self.payment_manager = payment_manager
        self.shipping_manager = shipping_manager
        self.orders = {}  # In production, this would be a database
    
    async def create_order(self, order_data: Dict) -> Dict:
        """Create a new order"""
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{len(self.orders) + 1:04d}"
        
        # Calculate totals
        subtotal = sum(item['price'] * item['quantity'] for item in order_data['items'])
        shipping_cost = self.shipping_manager.calculate_shipping_cost(
            order_data['shipping_method'],
            Decimal(str(subtotal)),
            order_data.get('shipping_address', {}).get('country', 'DE')
        )
        
        # Apply coupon if provided
        discount_amount = Decimal('0')
        if order_data.get('coupon_code'):
            coupon_manager = CouponManager()
            coupon_result = coupon_manager.apply_coupon(
                order_data['coupon_code'],
                Decimal(str(subtotal)),
                shipping_cost
            )
            if coupon_result['valid']:
                discount_amount = Decimal(str(coupon_result['discount_amount']))
                if coupon_result['free_shipping']:
                    shipping_cost = Decimal('0')
        
        total = subtotal + shipping_cost - discount_amount
        
        order = {
            'id': order_id,
            'status': 'pending',
            'customer_info': order_data['customer_info'],
            'billing_address': order_data['billing_address'],
            'shipping_address': order_data['shipping_address'],
            'items': order_data['items'],
            'subtotal': float(subtotal),
            'shipping_cost': float(shipping_cost),
            'discount_amount': float(discount_amount),
            'total': float(total),
            'currency': order_data.get('currency', 'EUR'),
            'payment_method': order_data['payment_method'],
            'shipping_method': order_data['shipping_method'],
            'coupon_code': order_data.get('coupon_code'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.orders[order_id] = order
        
        # Process payment
        if order_data['payment_method'] != 'bank_transfer':
            payment_request = PaymentRequest(
                amount=Decimal(str(total)),
                currency=order['currency'],
                customer_email=order['customer_info']['email'],
                payment_method=PaymentMethod(order['payment_method']),
                order_id=order_id,
                customer_info=order['customer_info'],
                billing_address=order['billing_address'],
                items=order['items']
            )
            
            payment_response = await self.payment_manager.process_payment(payment_request)
            order['payment_id'] = payment_response.payment_id
            order['payment_status'] = payment_response.status.value
            
            if payment_response.redirect_url:
                order['payment_redirect_url'] = payment_response.redirect_url
        
        return order
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        if order_id in self.orders:
            self.orders[order_id]['status'] = status
            self.orders[order_id]['updated_at'] = datetime.now().isoformat()
            return True
        return False
    
    async def fulfill_order(self, order_id: str) -> Dict:
        """Process order fulfillment (send to supplier)"""
        order = self.get_order(order_id)
        if not order:
            return {'success': False, 'message': 'Order not found'}
        
        # In a real dropshipping scenario, this would:
        # 1. Send order details to supplier
        # 2. Update inventory
        # 3. Generate tracking information
        # 4. Send confirmation emails
        
        # Simulate fulfillment
        tracking_number = f"TRK{order_id[-8:]}"
        
        self.update_order_status(order_id, 'processing')
        order['tracking_number'] = tracking_number
        
        return {
            'success': True,
            'message': 'Order sent to supplier for fulfillment',
            'tracking_number': tracking_number
        }

# Example usage and configuration
if __name__ == "__main__":
    # Payment gateway configuration
    payment_config = {
        'stripe': {
            'publishable_key': 'pk_test_...',
            'secret_key': 'sk_test_...'
        },
        'paypal': {
            'client_id': 'your_paypal_client_id',
            'client_secret': 'your_paypal_client_secret',
            'mode': 'sandbox',  # or 'live'
            'return_url': 'https://yoursite.com/payment/success',
            'cancel_url': 'https://yoursite.com/payment/cancel'
        }
    }
    
    # Initialize managers
    payment_manager = PaymentGatewayManager(payment_config)
    shipping_manager = ShippingManager()
    order_manager = OrderManager(payment_manager, shipping_manager)
    
    print("Payment and shipping systems initialized successfully!")