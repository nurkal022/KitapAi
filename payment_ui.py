import streamlit as st
import streamlit.components.v1 as stc
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

class PaymentUI:
    def __init__(self):
        pass
    
    def get_stripe_publishable_key(self):
        """Get Stripe publishable key from environment or secrets"""
        try:
            # Try to get from Streamlit secrets first
            return st.secrets.get("STRIPE_PUBLISHABLE_KEY", "")
        except:
            # Fallback to environment variable
            import os
            return os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    
    def show_pricing_page(self):
        """Display the pricing page with subscription options"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1>Choose Your Plan</h1>
            <p style="font-size: 1.2rem; color: #666;">Start with a 14-day free trial, then $9.99/month</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,75,224,0.1); text-align: center;">
                <h2 style="color: #004be0; margin-bottom: 1rem;">Pro Plan</h2>
                <div style="font-size: 2.5rem; font-weight: bold; color: #004be0; margin-bottom: 1rem;">
                    $9.99<span style="font-size: 1rem; color: #666;">/month</span>
                </div>
                <div style="text-align: left; margin: 2rem 0;">
                    <p>✓ 14-day free trial</p>
                    <p>✓ Unlimited mindmaps</p>
                    <p>✓ PDF upload and processing</p>
                    <p>✓ Export to multiple formats</p>
                    <p>✓ Priority support</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def show_payment_form(self, user_id: int, user_email: str, user_name: str):
        """Display the payment form for subscription"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1>Complete Your Subscription</h1>
            <p style="font-size: 1.1rem; color: #666;">Enter your payment information to start your 14-day free trial</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display trial information
        trial_end = datetime.now() + timedelta(days=14)
        st.info(f"🎉 You'll get a 14-day free trial! Your trial ends on {trial_end.strftime('%B %d, %Y')}")
        
        # Show test card information
        with st.expander("🧪 Test Card Information", expanded=True):
            st.markdown("""
            **Use these test cards to test the payment system:**
            
            - **✅ Success:** `4242 4242 4242 4242`
            - **❌ Decline:** `4000 0000 0000 0002`
            - **💰 Insufficient Funds:** `4000 0000 0000 9995`
            - **🏦 Requires Authentication:** `4000 0025 0000 3155`
            
            **Test Details:**
            - **Expiry:** Any future date (e.g., 12/25)
            - **CVC:** Any 3 digits (e.g., 123)
            - **ZIP:** Any 5 digits (e.g., 12345)
            """)
        
        # Payment form with card details for testing
        with st.form("payment_form"):
            st.markdown("### Payment Information")
            
            # Card details for testing
            card_number = st.text_input("Card Number", placeholder="4242 4242 4242 4242", help="Use test card numbers from the information above")
            
            col1, col2 = st.columns(2)
            with col1:
                expiry_month = st.selectbox("Expiry Month", range(1, 13), format_func=lambda x: f"{x:02d}")
            with col2:
                expiry_year = st.selectbox("Expiry Year", range(datetime.now().year, datetime.now().year + 10))
            
            cvc = st.text_input("CVC", placeholder="123", max_chars=4, help="Any 3 digits for testing")
            
            # Billing information
            st.markdown("### Billing Information")
            billing_name = st.text_input("Full Name", value=user_name)
            billing_email = st.text_input("Email", value=user_email)
            
            # Terms and conditions
            agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            # Submit button
            submit_button = st.form_submit_button("Start Free Trial", type="primary")
            
            if submit_button:
                if not all([card_number, cvc, billing_name, billing_email, agree_terms]):
                    st.error("Please fill in all required fields and agree to the terms.")
                    return None
                
                # Validate card number format (basic validation for testing)
                card_number_clean = card_number.replace(' ', '').replace('-', '')
                if not card_number_clean.isdigit() or len(card_number_clean) < 13:
                    st.error("Please enter a valid card number.")
                    return None
                
                return {
                    'card_number': card_number_clean,
                    'expiry_month': expiry_month,
                    'expiry_year': expiry_year,
                    'cvc': cvc,
                    'billing_name': billing_name,
                    'billing_email': billing_email,
                    'test_mode': True
                }
        
        return None
    
    def show_subscription_status(self, subscription_data: Dict[str, Any]):
        """Display current subscription status"""
        st.markdown("### Subscription Status")
        
        if subscription_data.get('is_trial_active'):
            trial_end = datetime.fromisoformat(subscription_data['trial_end_date'])
            days_left = (trial_end - datetime.now()).days
            
            st.success(f"🎉 You're on a free trial! {days_left} days remaining.")
            
            if days_left <= 3:
                st.warning("⚠️ Your trial is ending soon. Please add payment information to continue.")
        
        elif subscription_data.get('is_subscription_active'):
            subscription_end = datetime.fromisoformat(subscription_data['subscription_end_date'])
            st.success(f"✅ Active subscription until {subscription_end.strftime('%B %d, %Y')}")
        
        else:
            st.error("❌ No active subscription or trial")
    
    def show_billing_history(self, payment_history: list):
        """Display billing history"""
        if not payment_history:
            st.info("No payment history available.")
            return
        
        st.markdown("### Billing History")
        
        for payment in payment_history:
            amount = payment['amount'] / 100  # Convert from cents
            status_color = {
                'succeeded': 'green',
                'failed': 'red',
                'pending': 'orange'
            }.get(payment['status'], 'gray')
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid {status_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${amount:.2f} {payment['currency'].upper()}</strong>
                        <br>
                        <small>{payment['created_at'][:10]}</small>
                    </div>
                    <div style="color: {status_color}; font-weight: bold; text-transform: uppercase;">
                        {payment['status']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def show_subscription_management(self, subscription_data: Dict[str, Any]):
        """Display subscription management options"""
        st.markdown("### Subscription Management")
        
        if subscription_data.get('is_subscription_active'):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Cancel Subscription", type="secondary"):
                    st.session_state.cancel_subscription = True
            
            with col2:
                if st.button("Update Payment Method", type="secondary"):
                    st.session_state.update_payment = True
            
            if st.session_state.get('cancel_subscription'):
                st.warning("Are you sure you want to cancel your subscription?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Cancel", type="primary"):
                        st.session_state.confirm_cancel = True
                with col2:
                    if st.button("No, Keep It"):
                        st.session_state.cancel_subscription = False
                        st.session_state.confirm_cancel = False
        
        else:
            st.info("No active subscription to manage.")
    
    def show_payment_success(self):
        """Display payment success message"""
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🎉</div>
            <h1 style="color: #004be0;">Welcome to Kitap AI!</h1>
            <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
                Your 14-day free trial has started. You can now access all features.
            </p>
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 2rem 0;">
                <p><strong>What's next?</strong></p>
                <p>• Upload your first PDF</p>
                <p>• Create mindmaps</p>
                <p>• Export your work</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Go to Dashboard", type="primary"):
            st.session_state.show_payment = False
            st.session_state.show_dashboard = True
            st.rerun()
    
    def show_payment_error(self, error_message: str):
        """Display payment error message"""
        st.error(f"Payment failed: {error_message}")
        
        st.markdown("### What went wrong?")
        st.markdown("""
        Common issues:
        - Insufficient funds
        - Incorrect card information
        - Card declined by bank
        - Expired card
        """)
        
        if st.button("Try Again", type="primary"):
            st.session_state.payment_error = None
            st.rerun()
    
    def show_trial_expired(self):
        """Display trial expired message"""
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">⏰</div>
            <h1 style="color: #dc3545;">Trial Expired</h1>
            <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
                Your 14-day free trial has ended. Subscribe to continue using Kitap AI.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Subscribe Now", type="primary"):
            st.session_state.show_payment = True
            st.rerun()

# Global payment UI instance
payment_ui = PaymentUI() 