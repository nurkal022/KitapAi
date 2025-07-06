# Payment System Setup Guide

This guide will help you set up the payment system for Kitap AI with Stripe integration, including a 14-day free trial and monthly billing.

## Overview

The payment system includes:

- **14-day free trial** for new users
- **Monthly subscription** at $9.99/month
- **Stripe integration** for secure payment processing
- **Webhook handling** for subscription management
- **Database tracking** of subscriptions and payments

## Prerequisites

1. **Stripe Account**: Sign up at [stripe.com](https://stripe.com)
2. **Python Environment**: Python 3.7+ with pip
3. **Database**: SQLite (included) or PostgreSQL

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

Create a `.env` file in your project root:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_MONTHLY_PRICE_ID=price_your_monthly_price_id_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Application Configuration
IS_PRODUCTION=false
OPENAI_API_KEY=your_openai_api_key_here
```

## Step 3: Setup Stripe Products and Prices

Run the setup script to create Stripe products and prices:

```bash
python setup_payment.py
```

This will:

- Create a "Kitap AI Pro" product
- Create monthly ($9.99) and yearly ($99.90) prices
- Output the price IDs to add to your `.env` file

## Step 4: Configure Webhooks

1. Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Enter your webhook URL (e.g., `https://yourdomain.com/webhook`)
4. Select these events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Copy the webhook signing secret and add it to your `.env` file

## Step 5: Database Migration

The payment system adds new tables to your database. Run your application once to create the new tables:

```bash
streamlit run app.py
```

## Step 6: Test the Payment Flow

1. **Register a new user** - they should automatically get a 14-day trial
2. **Test payment processing** - use Stripe test cards
3. **Verify webhook handling** - check logs for webhook events

## Payment Flow

### New User Registration

1. User registers → 14-day trial starts automatically
2. User can access all features during trial
3. Before trial ends, payment form is shown

### Payment Process

1. User enters payment information
2. Stripe customer is created
3. Subscription is created with trial period
4. Payment method is saved for future billing
5. User gets access to service

### Subscription Management

- **Active subscription**: Full access to service
- **Trial period**: Full access for 14 days
- **Expired trial**: Payment required to continue
- **Failed payments**: Access suspended until payment

## API Reference

### Payment Service (`payment_service.py`)

```python
from payment_service import payment_service

# Create customer
customer_id = payment_service.create_customer(email, name)

# Create subscription
subscription = payment_service.create_subscription(customer_id)

# Get subscription details
subscription_data = payment_service.get_subscription(subscription_id)

# Cancel subscription
payment_service.cancel_subscription(subscription_id)
```

### Database Functions (`database.py`)

```python
from database import (
    start_user_trial,
    get_user_subscription_status,
    create_subscription,
    update_subscription_status
)

# Start trial for user
start_user_trial(user_id)

# Get subscription status
status = get_user_subscription_status(user_id)

# Create subscription record
create_subscription(user_id, stripe_subscription_id, price_id, start_date, end_date)
```

## Webhook Handling

The webhook handler processes Stripe events:

- **Subscription events**: Update subscription status
- **Payment events**: Update payment records
- **Trial events**: Handle trial period changes

## Testing

### Test Cards (Stripe Test Mode)

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **Insufficient funds**: `4000 0000 0000 9995`

### Test Scenarios

1. **New user registration**
2. **Trial period access**
3. **Payment processing**
4. **Subscription renewal**
5. **Payment failure handling**
6. **Subscription cancellation**

## Production Deployment

### Environment Variables

Set `IS_PRODUCTION=true` for production:

```env
IS_PRODUCTION=true
STRIPE_SECRET_KEY=sk_live_your_live_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key
```

### Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **Webhook verification**: Verify webhook signatures
3. **API keys**: Keep Stripe keys secure
4. **Database**: Use secure database connections

### Monitoring

1. **Payment logs**: Monitor payment success/failure rates
2. **Webhook delivery**: Check webhook delivery status
3. **Subscription metrics**: Track trial conversions
4. **Error handling**: Monitor payment errors

## Troubleshooting

### Common Issues

1. **"Stripe key not found"**

   - Check `.env` file configuration
   - Verify Stripe API keys

2. **"Webhook signature verification failed"**

   - Check webhook secret in `.env`
   - Verify webhook URL configuration

3. **"Subscription not found"**

   - Check database connection
   - Verify subscription creation process

4. **"Payment failed"**
   - Check Stripe dashboard for errors
   - Verify payment method details

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues with:

- **Stripe integration**: Check [Stripe documentation](https://stripe.com/docs)
- **Payment processing**: Review Stripe dashboard logs
- **Webhook handling**: Check webhook delivery status
- **Database issues**: Verify database schema and connections

## License

This payment system is part of Kitap AI and follows the same license terms.
