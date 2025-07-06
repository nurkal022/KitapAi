import stripe
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Debug: Print loaded environment variables in payment_service
print("=== DEBUG: Payment Service Environment Variables ===")
print(f"STRIPE_SECRET_KEY: {os.getenv('STRIPE_SECRET_KEY')}")
print(f"STRIPE_PUBLISHABLE_KEY: {os.getenv('STRIPE_PUBLISHABLE_KEY')}")
print(f"STRIPE_MONTHLY_PRICE_ID: {os.getenv('STRIPE_MONTHLY_PRICE_ID')}")
print("==================================================")

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.monthly_price_id = os.getenv('STRIPE_MONTHLY_PRICE_ID')
        self.trial_days = 14
        
        if not stripe.api_key:
            logger.error("STRIPE_SECRET_KEY not found in environment variables")
        if not self.monthly_price_id:
            logger.error("STRIPE_MONTHLY_PRICE_ID not found in environment variables")
    
    def create_customer(self, email: str, name: str) -> Optional[str]:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'source': 'kitap_ai'
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            return None
    
    def create_subscription(self, customer_id: str, trial_days: int = 0) -> Optional[Dict[str, Any]]:
        """Create a subscription with immediate payment"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': self.monthly_price_id}],
                payment_settings={'save_default_payment_method': 'on_subscription'},
                metadata={
                    'source': 'kitap_ai'
                }
            )
            
            # Debug: Print subscription object
            print("=== DEBUG: Stripe Subscription Object ===")
            print(f"subscription.id: {subscription.id}")
            print(f"subscription.status: {subscription.status}")
            
            # Handle different subscription statuses
            print(f"=== DEBUG: Subscription Status: {subscription.status} ===")
            
            if subscription.status == 'trialing':
                print(f"subscription.trial_start: {subscription.trial_start}")
                print(f"subscription.trial_end: {subscription.trial_end}")
                # For trialing subscriptions, use trial dates as current period dates
                current_period_start = subscription.trial_start
                current_period_end = subscription.trial_end
            elif subscription.status == 'incomplete':
                print("Subscription is incomplete - payment required")
                # For incomplete subscriptions, we need to handle payment confirmation
                try:
                    current_period_start = subscription.current_period_start
                    current_period_end = subscription.current_period_end
                except (AttributeError, KeyError):
                    print("No current_period dates available for incomplete subscription")
                    current_period_start = None
                    current_period_end = None
            elif subscription.status == 'past_due':
                print("Subscription is past due")
                try:
                    current_period_start = subscription.current_period_start
                    current_period_end = subscription.current_period_end
                except (AttributeError, KeyError):
                    print("No current_period dates available for past_due subscription")
                    current_period_start = None
                    current_period_end = None
            else:
                try:
                    print(f"subscription.current_period_start: {subscription.current_period_start}")
                    print(f"subscription.current_period_end: {subscription.current_period_end}")
                    current_period_start = subscription.current_period_start
                    current_period_end = subscription.current_period_end
                except (AttributeError, KeyError):
                    print(f"No current_period dates available for {subscription.status} subscription")
                    current_period_start = None
                    current_period_end = None
            
            print("=========================================")
            
            # For regular subscriptions, we don't need client_secret
            client_secret = None
            
            # If subscription is incomplete, try to confirm it
            if subscription.status == 'incomplete':
                print("=== DEBUG: Attempting to confirm incomplete subscription ===")
                try:
                    # Retrieve the subscription to get the latest status
                    subscription = stripe.Subscription.retrieve(subscription.id)
                    print(f"Subscription status after retrieval: {subscription.status}")
                except Exception as e:
                    print(f"Error retrieving subscription: {str(e)}")
            
            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_start': datetime.fromtimestamp(current_period_start) if current_period_start else None,
                'current_period_end': datetime.fromtimestamp(current_period_end) if current_period_end else None,
                'trial_start': datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                'trial_end': datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                'client_secret': client_secret
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return None



    def create_test_payment_method(self, card_number: str, expiry_month: int, expiry_year: int, cvc: str, customer_id: str) -> Optional[Dict[str, Any]]:
        """Create a test payment method using Stripe's test tokens"""
        try:
            # For testing, we'll create a payment method using Stripe's test approach
            # In production, you'd use Stripe Elements to collect card data securely
            
            # Create a test payment method (this is for testing only)
            payment_method = stripe.PaymentMethod.create(
                type='card',
                card={
                    'token': 'tok_visa',  # Use Stripe's test token for Visa
                },
                billing_details={
                    'name': 'Test User',
                    'email': 'test@example.com',
                },
                metadata={
                    'source': 'kitap_ai',
                    'test_mode': 'true'
                }
            )
            
            # Attach to customer
            payment_method.attach(customer=customer_id)
            
            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method.id,
                },
            )
            
            print(f"=== DEBUG: Test Payment Method Created ===")
            print(f"payment_method.id: {payment_method.id}")
            print(f"payment_method.type: {payment_method.type}")
            print(f"payment_method.card.last4: {payment_method.card.last4}")
            print(f"Card brand: {payment_method.card.brand}")
            print("===========================================")
            
            return {
                'payment_method_id': payment_method.id,
                'card_last4': payment_method.card.last4,
                'card_brand': payment_method.card.brand,
                'card_exp_month': payment_method.card.exp_month,
                'card_exp_year': payment_method.card.exp_year
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating test payment method: {str(e)}")
            return None

    def confirm_payment_intent(self, payment_intent_id: str, payment_method_id: str) -> Optional[Dict[str, Any]]:
        """Confirm a payment intent with a payment method"""
        try:
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method_id,
                return_url='https://your-domain.com/success'
            )
            
            print(f"=== DEBUG: Payment Intent Confirmed ===")
            print(f"payment_intent.id: {payment_intent.id}")
            print(f"payment_intent.status: {payment_intent.status}")
            print("=====================================")
            
            return {
                'payment_intent_id': payment_intent.id,
                'status': payment_intent.status,
                'amount': payment_intent.amount
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error confirming payment intent: {str(e)}")
            return None
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                'trial_start': datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                'trial_end': datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return subscription.status == 'active'
        except stripe.error.StripeError as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            return False
    
    def reactivate_subscription(self, subscription_id: str) -> bool:
        """Reactivate a canceled subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return subscription.status == 'active'
        except stripe.error.StripeError as e:
            logger.error(f"Error reactivating subscription: {str(e)}")
            return False
    
    def create_payment_intent(self, amount: int, currency: str = 'usd', customer_id: str = None) -> Optional[Dict[str, Any]]:
        """Create a payment intent for one-time payments"""
        try:
            payment_intent_data = {
                'amount': amount,
                'currency': currency,
                'metadata': {
                    'source': 'kitap_ai'
                }
            }
            
            if customer_id:
                payment_intent_data['customer'] = customer_id
            
            payment_intent = stripe.PaymentIntent.create(**payment_intent_data)
            
            return {
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'status': payment_intent.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return None
    
    def get_payment_intent(self, payment_intent_id: str) -> Optional[Dict[str, Any]]:
        """Get payment intent details"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'payment_intent_id': payment_intent.id,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'status': payment_intent.status,
                'customer_id': payment_intent.customer
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent: {str(e)}")
            return None
    
    def create_checkout_session(self, customer_id: str, success_url: str, cancel_url: str) -> Optional[str]:
        """Create a Stripe checkout session for subscription"""
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': self.monthly_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                trial_period_days=self.trial_days,
                allow_promotion_codes=True,
                metadata={
                    'source': 'kitap_ai'
                }
            )
            return checkout_session.id
        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return None
    
    def get_checkout_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get checkout session details"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'session_id': session.id,
                'payment_status': session.payment_status,
                'subscription_id': session.subscription,
                'customer_id': session.customer,
                'status': session.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving checkout session: {str(e)}")
            return None

# Global payment service instance
payment_service = PaymentService() 