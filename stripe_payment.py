"""
Stripe Payment Integration for MathQuest
======================================
Handles Stripe Checkout session creation and webhook verification.
"""

import stripe
import os
import json
import hmac
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger("stripe")

# ── Stripe Keys ─────────────────────────────────────────────────────────────
# SET THESE ENVIRONMENT VARIABLES before deploying:
#   STRIPE_SECRET_KEY=sk_test_...
#   STRIPE_WEBHOOK_SECRET=whsec_...
#   STRIPE_PUBLISHABLE_KEY=pk_test_...

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

# ── Product Config ──────────────────────────────────────────────────────────
PRODUCT_NAME = "MathQuest Home Access"
PRODUCT_PRICE_PENCE = 500  # £5.00
PRODUCT_DESCRIPTION = "Lifetime access for up to 4 children. One-time payment, no subscription."


def is_configured() -> bool:
    """Check if Stripe keys are configured."""
    return bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.startswith("sk_"))


def create_checkout_session(email: str, success_url: str, cancel_url: str) -> dict:
    """
    Create a Stripe Checkout Session.
    
    Args:
        email: Buyer's email address (pre-filled in Stripe)
        success_url: URL to redirect to after successful payment
        cancel_url: URL to redirect to if payment is cancelled
    
    Returns:
        dict with 'id' (session ID) and 'url' (checkout URL)
    """
    if not is_configured():
        raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY environment variable.")

    stripe.api_key = STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=email,
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "unit_amount": PRODUCT_PRICE_PENCE,
                "product_data": {
                    "name": PRODUCT_NAME,
                    "description": PRODUCT_DESCRIPTION,
                    "images": [
                        "https://mathquest.app/static/images/hero-kids.png"
                        # Add your product image URL here
                    ],
                },
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "product": "mathquest_home_access",
            "price_gbp": "5.00",
        },
        billing_address_collection="auto",
        phone_number_collection={"enabled": False},
        custom_text={
            "submit": {
                "message": "You'll receive your access code by email within seconds of completing your purchase."
            }
        },
    )

    logger.info(f"Checkout session created: {session.id} for {email}")
    return {"id": session.id, "url": session.url}


def construct_webhook_event(payload: bytes, signature_header: str) -> dict:
    """
    Verify and parse a Stripe webhook event.
    
    Args:
        payload: Raw request body (bytes)
        signature_header: Stripe-Signature header value
    
    Returns:
        Parsed Stripe event dict
    """
    if not is_configured():
        raise ValueError("Stripe webhook secret not configured.")

    try:
        event = stripe.Webhook.construct_event(
            payload, signature_header, STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError:
        logger.error("Stripe webhook signature verification failed")
        raise ValueError("Invalid webhook signature")


def get_session_customer_email(session_id: str) -> str:
    """Get the customer email from a completed checkout session."""
    if not is_configured():
        raise ValueError("Stripe not configured.")
    
    stripe.api_key = STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(session_id)
    return session.get("customer_email", "") or session.get("customer_details", {}).get("email", "")


# ── Email Access Code ───────────────────────────────────────────────────────
def send_access_code_email(email: str, access_code: str) -> bool:
    """
    Send the access code to a buyer via email.
    Uses the Yahoo SMTP email sender.
    """
    import smtplib
    import ssl
    from email.message import EmailMessage
    from email.utils import formataddr

    SMTP_HOST = "smtp.mail.yahoo.com"
    SMTP_PORT = 587
    FROM_EMAIL = "nelson6737@yahoo.com"
    APP_PASSWORD = "fowqctnp rprtkuvd"
    FROM_NAME = "MathQuest"

    subject = "Your MathQuest Access Code 🎮"
    body = f"""Hi there!

Thank you for purchasing MathQuest Home Access!

Your access code is:

    {access_code}

Use this code to create your parent account at:
  https://mathquest.app/parent/register/step1

Here's how it works:
1. Go to the link above
2. Enter your access code
3. Create your parent account
4. Add up to 4 children

That's it — you're all set!

Questions? Just reply to this email.

Best wishes,
The MathQuest Team
"""

    try:
        msg = EmailMessage()
        msg['From'] = formataddr((FROM_NAME, FROM_EMAIL))
        msg['To'] = email
        msg['Subject'] = subject
        msg.set_content(body)

        ctx = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=ctx)
            server.login(FROM_EMAIL, APP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Access code sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
        return False


# ── Pending payments tracker ────────────────────────────────────────────────
# Simple JSON-based tracker (use Redis/DB in production)
import sqlite3
from pathlib import Path

PENDING_FILE = Path(__file__).parent / "pending_payments.json"


def save_pending_payment(session_id: str, email: str, access_code: str):
    """Record a pending payment so we can match it to the webhook."""
    import json
    pending = {}
    if PENDING_FILE.exists():
        try:
            pending = json.loads(PENDING_FILE.read_text())
        except:
            pending = {}
    
    pending[session_id] = {
        "email": email,
        "access_code": access_code,
        "created_at": datetime.now().isoformat(),
    }
    
    PENDING_FILE.write_text(json.dumps(pending, indent=2))


def get_pending_payment(session_id: str) -> dict | None:
    """Get pending payment info for a session ID."""
    import json
    if not PENDING_FILE.exists():
        return None
    try:
        pending = json.loads(PENDING_FILE.read_text())
        return pending.get(session_id)
    except:
        return None


def remove_pending_payment(session_id: str):
    """Remove a pending payment after it's been fulfilled."""
    import json
    if not PENDING_FILE.exists():
        return
    try:
        pending = json.loads(PENDING_FILE.read_text())
        pending.pop(session_id, None)
        PENDING_FILE.write_text(json.dumps(pending, indent=2))
    except:
        pass
