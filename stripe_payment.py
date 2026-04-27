"""
Stripe Payment Integration for MathQuest
======================================
Handles Stripe Checkout session creation and webhook verification.
"""

import stripe
import os
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("stripe")

# ── Stripe Keys ─────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

PRODUCT_NAME = "MathQuest Home Access"
PRODUCT_PRICE_PENCE = 500
PRODUCT_DESCRIPTION = "Lifetime access for up to 4 children. One-time payment, no subscription."


def is_configured() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.startswith("sk_"))


def create_checkout_session(email: str, success_url: str, cancel_url: str) -> dict:
    if not is_configured():
        raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY.")
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
                },
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"product": "mathquest_home_access", "price_gbp": "5.00"},
        billing_address_collection="auto",
        custom_text={"submit": {"message": "You'll receive your access code by email within seconds."}},
    )
    logger.info(f"Checkout session: {session.id} for {email}")
    return {"id": session.id, "url": session.url}


def construct_webhook_event(payload: bytes, signature_header: str) -> dict:
    if not is_configured():
        raise ValueError("Stripe not configured.")
    try:
        event = stripe.Webhook.construct_event(payload, signature_header, STRIPE_WEBHOOK_SECRET)
        return event
    except stripe.error.SignatureVerificationError:
        logger.error("Webhook signature verification failed")
        raise ValueError("Invalid webhook signature")


# ── Email ─────────────────────────────────────────────────────────────────
def send_access_code_email(email: str, access_code: str) -> bool:
    """Send access code via Resend (preferred) or Yahoo SMTP (fallback)."""
    resend_key = os.environ.get("RESEND_API_KEY", "")
    if resend_key:
        try:
            import resend
            resend.api_key = resend_key
            params = {
                "from": "MathQuest <resend@resend.dev>",
                "to": [email],
                "subject": "Your MathQuest Access Code",
                "html": _build_html(access_code),
                "text": _build_text(access_code),
            }
            r = resend.Emails.send(params)
            logger.info(f"Email sent via Resend: {r}")
            return True
        except Exception as e:
            logger.error(f"Resend failed: {e}")
    return _send_yahoo(email, access_code)


def _build_html(code: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><style>
body{{font-family:Arial,sans-serif;background:#F5F3FF;margin:0;padding:20px}}
.c{{max-width:560px;margin:0 auto;background:white;border-radius:16px;overflow:hidden}}
.h{{background:linear-gradient(135deg,#667eea,#764ba2);padding:32px;text-align:center}}
h1{{color:white;font-size:24px;margin:0}}
.b{{padding:32px}}
.cbox{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;text-align:center;padding:24px;border-radius:14px;margin:20px 0}}
.code{{font-size:36px;font-weight:900;letter-spacing:6px;font-family:monospace}}
.btn{{display:inline-block;width:100%;padding:16px;background:linear-gradient(135deg,#7C3AED,#6D28D9);color:white;text-align:center;text-decoration:none;border-radius:12px;font-weight:800;font-size:16px;margin:16px 0}}
.steps{{background:#F5F3FF;border-radius:12px;padding:20px 24px;margin:20px 0}}
.steps li{{margin:8px 0;color:#374151;font-size:15px}}
.f{{text-align:center;color:#9CA3AF;font-size:12px;padding:20px 32px 32px}}
</style></head><body>
<div class="c">
  <div class="h"><h1>Your MathQuest Access Code</h1></div>
  <div class="b">
    <p>Hi there!</p>
    <p>Thank you for purchasing <strong>MathQuest Home Access</strong>!</p>
    <p>Your access code is:</p>
    <div class="cbox"><div class="code">{code}</div></div>
    <p><strong>Next steps:</strong></p>
    <ol class="steps">
      <li>Go to <strong>mathquest-fbkr.onrender.com/parent/register/step1</strong></li>
      <li>Enter your access code above</li>
      <li>Create your parent account</li>
      <li>Add up to 4 children — you're all set!</li>
    </ol>
    <p>Questions? Reply to this email.</p>
    <p><strong>The MathQuest Team</strong></p>
  </div>
  <div class="f">MathQuest — Fun maths for kids<br>mathquest-fbkr.onrender.com</div>
</div></body></html>"""


def _build_text(code: str) -> str:
    return f"""Your MathQuest Access Code
===========================
Hi!
Thank you for purchasing MathQuest Home Access.
Your access code: {code}
Next steps:
1. Go to mathquest-fbkr.onrender.com/parent/register/step1
2. Enter your access code
3. Create your parent account
4. Add up to 4 children
Questions? Reply to this email.
The MathQuest Team"""


def _send_yahoo(email: str, access_code: str) -> bool:
    import smtplib, ssl
    from email.message import EmailMessage
    from email.utils import formataddr
    try:
        msg = EmailMessage()
        msg["From"] = formataddr(("MathQuest", "nelson6737@yahoo.com"))
        msg["To"] = email
        msg["Subject"] = "Your MathQuest Access Code"
        msg.set_content(_build_text(access_code))
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.mail.yahoo.com", 587) as server:
            server.starttls(context=ctx)
            server.login("nelson6737@yahoo.com", "fowqctnp rprtkuvd")
            server.send_message(msg)
        logger.info(f"Email sent to {email} via Yahoo")
        return True
    except Exception as e:
        logger.error(f"Yahoo email failed: {e}")
        return False


# ── Pending payments tracker ────────────────────────────────────────────────
PENDING_FILE = Path(__file__).parent / "pending_payments.json"


def save_pending_payment(session_id: str, email: str, access_code: str):
    pending = {}
    if PENDING_FILE.exists():
        try:
            pending = json.loads(PENDING_FILE.read_text())
        except:
            pass
    pending[session_id] = {"email": email, "access_code": access_code, "created_at": datetime.now().isoformat()}
    PENDING_FILE.write_text(json.dumps(pending, indent=2))


def get_pending_payment(session_id: str):
    if not PENDING_FILE.exists():
        return None
    try:
        pending = json.loads(PENDING_FILE.read_text())
        return pending.get(session_id)
    except:
        return None


def remove_pending_payment(session_id: str):
    if not PENDING_FILE.exists():
        return
    try:
        pending = json.loads(PENDING_FILE.read_text())
        pending.pop(session_id, None)
        PENDING_FILE.write_text(json.dumps(pending, indent=2))
    except:
        pass
