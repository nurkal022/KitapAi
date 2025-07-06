#!/usr/bin/env python3
"""
Setup script for Kitap AI payment system
This script helps configure Stripe products and prices
"""

import stripe
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def setup_stripe():
    """Setup Stripe products and prices"""
    api_key = os.getenv('STRIPE_SECRET_KEY')
    if not api_key:
        print("❌ STRIPE_SECRET_KEY not found in environment variables")
        print("Please add your Stripe secret key to .env file")
        return False
    
    stripe.api_key = api_key
    
    try:
        # Create product
        print("📦 Creating product...")
        product = stripe.Product.create(
            name="Kitap AI Pro",
            description="AI-powered mind map generation with PDF processing",
            metadata={
                'source': 'kitap_ai'
            }
        )
        print(f"✅ Product created: {product.id}")
        
        # Create monthly price
        print("💰 Creating monthly price...")
        price = stripe.Price.create(
            product=product.id,
            unit_amount=999,  # $9.99 in cents
            currency='usd',
            recurring={
                'interval': 'month'
            },
            metadata={
                'source': 'kitap_ai'
            }
        )
        print(f"✅ Monthly price created: {price.id}")
        
        # Create yearly price (optional)
        print("💰 Creating yearly price...")
        yearly_price = stripe.Price.create(
            product=product.id,
            unit_amount=9990,  # $99.90 in cents (2 months free)
            currency='usd',
            recurring={
                'interval': 'year'
            },
            metadata={
                'source': 'kitap_ai'
            }
        )
        print(f"✅ Yearly price created: {yearly_price.id}")
        
        print("\n🎉 Stripe setup completed successfully!")
        print("\n📋 Configuration details:")
        print(f"Product ID: {product.id}")
        print(f"Monthly Price ID: {price.id}")
        print(f"Yearly Price ID: {yearly_price.id}")
        
        print("\n📝 Add these to your .env file:")
        print(f"STRIPE_MONTHLY_PRICE_ID={price.id}")
        print(f"STRIPE_YEARLY_PRICE_ID={yearly_price.id}")
        
        return True
        
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def setup_webhook():
    """Setup Stripe webhook endpoint"""
    print("\n🔗 Webhook Setup Instructions:")
    print("1. Go to https://dashboard.stripe.com/webhooks")
    print("2. Click 'Add endpoint'")
    print("3. Enter your webhook URL (e.g., https://yourdomain.com/webhook)")
    print("4. Select these events:")
    print("   - customer.subscription.created")
    print("   - customer.subscription.updated")
    print("   - customer.subscription.deleted")
    print("   - invoice.payment_succeeded")
    print("   - invoice.payment_failed")
    print("   - payment_intent.succeeded")
    print("   - payment_intent.payment_failed")
    print("5. Copy the webhook signing secret")
    print("6. Add to your .env file: STRIPE_WEBHOOK_SECRET=whsec_...")

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

def main():
    """Main setup function"""
    print("🚀 Kitap AI Payment System Setup")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup Stripe
    if not setup_stripe():
        sys.exit(1)
    
    # Setup webhook instructions
    setup_webhook()
    
    print("\n🎯 Next steps:")
    print("1. Update your .env file with the price IDs")
    print("2. Set up webhook endpoint")
    print("3. Test the payment flow")
    print("4. Deploy your application")

if __name__ == "__main__":
    main() 