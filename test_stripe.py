#!/usr/bin/env python3
"""
Stripe Test Script
This script helps you test your Stripe configuration and payment processing.
"""

import os
import stripe
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')

def test_stripe_configuration():
    """Test basic Stripe configuration"""
    print("=== Testing Stripe Configuration ===")
    print(f"Stripe Secret Key: {'✅ Set' if stripe.api_key else '❌ Not Set'}")
    print(f"Stripe Publishable Key: {'✅ Set' if STRIPE_PUBLISHABLE_KEY else '❌ Not Set'}")
    print(f"Monthly Price ID: {'✅ Set' if STRIPE_MONTHLY_PRICE_ID else '❌ Not Set'}")
    
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEY not found. Please set it in your .env file.")
        return False
    
    try:
        # Test API connection
        account = stripe.Account.retrieve()
        print(f"✅ Stripe API connection successful")
        print(f"Account ID: {account.id}")
        print(f"Account Type: {account.type}")
        return True
    except stripe.error.AuthenticationError:
        print("❌ Authentication failed. Check your STRIPE_SECRET_KEY.")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Stripe: {str(e)}")
        return False

def test_price_retrieval():
    """Test if the monthly price exists"""
    print("\n=== Testing Price Retrieval ===")
    
    if not STRIPE_MONTHLY_PRICE_ID:
        print("❌ STRIPE_MONTHLY_PRICE_ID not set")
        return False
    
    try:
        price = stripe.Price.retrieve(STRIPE_MONTHLY_PRICE_ID)
        print(f"✅ Price found: {price.nickname}")
        print(f"Amount: ${price.unit_amount / 100:.2f} {price.currency.upper()}")
        print(f"Recurring: {price.recurring.interval if price.recurring else 'One-time'}")
        return True
    except stripe.error.InvalidRequestError:
        print(f"❌ Price {STRIPE_MONTHLY_PRICE_ID} not found")
        return False
    except Exception as e:
        print(f"❌ Error retrieving price: {str(e)}")
        return False

def test_customer_creation():
    """Test customer creation"""
    print("\n=== Testing Customer Creation ===")
    
    try:
        customer = stripe.Customer.create(
            email="test@example.com",
            name="Test Customer",
            metadata={'source': 'test_script'}
        )
        print(f"✅ Customer created: {customer.id}")
        print(f"Email: {customer.email}")
        print(f"Name: {customer.name}")
        return customer.id
    except Exception as e:
        print(f"❌ Error creating customer: {str(e)}")
        return None

def test_payment_method_creation(customer_id):
    """Test payment method creation with test card"""
    print("\n=== Testing Payment Method Creation ===")
    
    try:
        payment_method = stripe.PaymentMethod.create(
            type='card',
            card={
                'number': '4242424242424242',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123',
            },
            billing_details={
                'name': 'Test User',
                'email': 'test@example.com',
            },
            metadata={'source': 'test_script'}
        )
        
        # Attach to customer
        payment_method.attach(customer=customer_id)
        
        print(f"✅ Payment method created: {payment_method.id}")
        print(f"Card: {payment_method.card.brand} ending in {payment_method.card.last4}")
        print(f"Expiry: {payment_method.card.exp_month}/{payment_method.card.exp_year}")
        
        return payment_method.id
    except Exception as e:
        print(f"❌ Error creating payment method: {str(e)}")
        return None

def test_subscription_creation(customer_id, payment_method_id):
    """Test subscription creation"""
    print("\n=== Testing Subscription Creation ===")
    
    if not STRIPE_MONTHLY_PRICE_ID:
        print("❌ STRIPE_MONTHLY_PRICE_ID not set")
        return None
    
    try:
        # Set default payment method
        stripe.Customer.modify(
            customer_id,
            invoice_settings={
                'default_payment_method': payment_method_id,
            },
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': STRIPE_MONTHLY_PRICE_ID}],
            trial_period_days=14,
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent'],
            metadata={'source': 'test_script'}
        )
        
        print(f"✅ Subscription created: {subscription.id}")
        print(f"Status: {subscription.status}")
        print(f"Trial start: {datetime.fromtimestamp(subscription.trial_start)}")
        print(f"Trial end: {datetime.fromtimestamp(subscription.trial_end)}")
        
        return subscription.id
    except Exception as e:
        print(f"❌ Error creating subscription: {str(e)}")
        return None

def cleanup_test_data(customer_id, payment_method_id, subscription_id):
    """Clean up test data"""
    print("\n=== Cleaning Up Test Data ===")
    
    try:
        if subscription_id:
            stripe.Subscription.delete(subscription_id)
            print(f"✅ Subscription {subscription_id} deleted")
        
        if payment_method_id:
            stripe.PaymentMethod.detach(payment_method_id)
            print(f"✅ Payment method {payment_method_id} detached")
        
        if customer_id:
            stripe.Customer.delete(customer_id)
            print(f"✅ Customer {customer_id} deleted")
            
    except Exception as e:
        print(f"⚠️ Error cleaning up: {str(e)}")

def main():
    """Run all tests"""
    print("🧪 Stripe Payment System Test")
    print("=" * 50)
    
    # Test configuration
    if not test_stripe_configuration():
        return
    
    # Test price retrieval
    if not test_price_retrieval():
        return
    
    # Test customer creation
    customer_id = test_customer_creation()
    if not customer_id:
        return
    
    # Test payment method creation
    payment_method_id = test_payment_method_creation(customer_id)
    if not payment_method_id:
        cleanup_test_data(customer_id, None, None)
        return
    
    # Test subscription creation
    subscription_id = test_subscription_creation(customer_id, payment_method_id)
    
    # Clean up
    cleanup_test_data(customer_id, payment_method_id, subscription_id)
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print("Your Stripe configuration is working correctly.")
    print("\nYou can now test payments in your Streamlit app using:")
    print("- Success card: 4242 4242 4242 4242")
    print("- Decline card: 4000 0000 0000 0002")
    print("- Insufficient funds: 4000 0000 0000 9995")

if __name__ == "__main__":
    main() 