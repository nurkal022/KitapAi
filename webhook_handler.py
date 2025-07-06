import stripe
import os
from datetime import datetime
from typing import Dict, Any
import logging
from dotenv import load_dotenv
from database import (
    update_subscription_status,
    update_payment_status,
    get_user_subscription_status
)

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self):
        self.endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Handle incoming webhook from Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.endpoint_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return {"error": "Invalid payload"}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return {"error": "Invalid signature"}
        
        # Handle the event
        if event['type'] == 'customer.subscription.created':
            return self.handle_subscription_created(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            return self.handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            return self.handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            return self.handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            return self.handle_payment_failed(event['data']['object'])
        elif event['type'] == 'payment_intent.succeeded':
            return self.handle_payment_intent_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            return self.handle_payment_intent_failed(event['data']['object'])
        else:
            logger.info(f"Unhandled event type: {event['type']}")
            return {"status": "ignored"}
    
    def handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription creation event"""
        try:
            logger.info(f"Subscription created: {subscription['id']}")
            
            # Update subscription status in database
            current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
            update_subscription_status(
                subscription['id'],
                subscription['status'],
                current_period_end
            )
            
            return {"status": "success", "message": "Subscription created"}
        except Exception as e:
            logger.error(f"Error handling subscription created: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription update event"""
        try:
            logger.info(f"Subscription updated: {subscription['id']}")
            
            # Update subscription status in database
            current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
            update_subscription_status(
                subscription['id'],
                subscription['status'],
                current_period_end
            )
            
            return {"status": "success", "message": "Subscription updated"}
        except Exception as e:
            logger.error(f"Error handling subscription updated: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deletion event"""
        try:
            logger.info(f"Subscription deleted: {subscription['id']}")
            
            # Update subscription status in database
            current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
            update_subscription_status(
                subscription['id'],
                'canceled',
                current_period_end
            )
            
            return {"status": "success", "message": "Subscription deleted"}
        except Exception as e:
            logger.error(f"Error handling subscription deleted: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment event"""
        try:
            logger.info(f"Payment succeeded for invoice: {invoice['id']}")
            
            # Update payment status if it's a payment intent
            if 'payment_intent' in invoice and invoice['payment_intent']:
                update_payment_status(
                    invoice['payment_intent'],
                    'succeeded'
                )
            
            return {"status": "success", "message": "Payment succeeded"}
        except Exception as e:
            logger.error(f"Error handling payment succeeded: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment event"""
        try:
            logger.info(f"Payment failed for invoice: {invoice['id']}")
            
            # Update payment status if it's a payment intent
            if 'payment_intent' in invoice and invoice['payment_intent']:
                update_payment_status(
                    invoice['payment_intent'],
                    'failed'
                )
            
            return {"status": "success", "message": "Payment failed"}
        except Exception as e:
            logger.error(f"Error handling payment failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def handle_payment_intent_succeeded(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment intent event"""
        try:
            logger.info(f"Payment intent succeeded: {payment_intent['id']}")
            
            # Update payment status
            update_payment_status(
                payment_intent['id'],
                'succeeded'
            )
            
            return {"status": "success", "message": "Payment intent succeeded"}
        except Exception as e:
            logger.error(f"Error handling payment intent succeeded: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def handle_payment_intent_failed(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment intent event"""
        try:
            logger.info(f"Payment intent failed: {payment_intent['id']}")
            
            # Update payment status
            update_payment_status(
                payment_intent['id'],
                'failed'
            )
            
            return {"status": "success", "message": "Payment intent failed"}
        except Exception as e:
            logger.error(f"Error handling payment intent failed: {str(e)}")
            return {"status": "error", "message": str(e)}

# Global webhook handler instance
webhook_handler = WebhookHandler() 