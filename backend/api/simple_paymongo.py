"""Simple PayMongo + Gmail Notifications"""
import requests
import base64
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paymongo_config import PAYMONGO_SECRET_KEY, PAYMONGO_BASE_URL

User = get_user_model()


class SimplePayMongo:
    def __init__(self):
        self.secret_key = PAYMONGO_SECRET_KEY
        self.base_url = PAYMONGO_BASE_URL
        auth = base64.b64encode(f'{self.secret_key}:'.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json'
        }
    
    def create_payment_link(self, amount, description):
        """Create payment link"""
        amount_centavos = int(Decimal(str(amount)) * 100)
        
        try:
            response = requests.post(
                f'{self.base_url}/links',
                json={
                    'data': {
                        'attributes': {
                            'amount': amount_centavos,
                            'description': description,
                            'currency': 'PHP'
                        }
                    }
                },
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            data = result.get('data', {})
            attrs = data.get('attributes', {})
            
            return {
                'success': True,
                'link_id': data.get('id'),
                'reference_number': attrs.get('reference_number'),
                'checkout_url': attrs.get('checkout_url'),
                'amount': amount
            }
        except Exception as e:
            print(f"❌ Payment Link Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {'success': False, 'error': str(e)}
    
    def send_payment_email(self, to_email, homeowner_name, amount, due_date, reference, checkout_url):
        """Send payment notification to homeowner"""
        try:
            subject = f"💰 New Service Fee - ₱{amount}"
            message = f"""
Hi {homeowner_name},

You have a new service fee bill:

Amount: ₱{amount}
Due Date: {due_date}
Reference Number: {reference}

Pay online via GCash/PayMaya/QRPh:
{checkout_url}

Thank you!
Happy Homes Administration
            """
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2c7c4b;">💰 New Service Fee Bill</h2>
                <p>Hi <strong>{homeowner_name}</strong>,</p>
                <p>You have a new service fee bill:</p>
                <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Amount:</strong> ₱{amount}</p>
                    <p style="margin: 5px 0;"><strong>Due Date:</strong> {due_date}</p>
                    <p style="margin: 5px 0;"><strong>Reference:</strong> {reference}</p>
                </div>
                <a href="{checkout_url}" style="display: inline-block; background: #2c7c4b; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    Pay Now via GCash/PayMaya
                </a>
                <p style="margin-top: 20px; color: #666;">Thank you!<br>Happy Homes Administration</p>
            </body>
            </html>
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def send_payment_confirmation(self, to_email, homeowner_name, amount, reference):
        """Send confirmation when paid"""
        try:
            subject = f"✅ Payment Received - ₱{amount}"
            message = f"""
Hi {homeowner_name},

Your payment has been received!

Amount: ₱{amount}
Reference: {reference}
Status: PAID ✅

Thank you for your payment!
Happy Homes Administration
            """
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #10b981;">✅ Payment Received!</h2>
                <p>Hi <strong>{homeowner_name}</strong>,</p>
                <p>Your payment has been successfully received!</p>
                <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
                    <p style="margin: 5px 0;"><strong>Amount:</strong> ₱{amount}</p>
                    <p style="margin: 5px 0;"><strong>Reference:</strong> {reference}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #10b981; font-weight: bold;">PAID ✅</span></p>
                </div>
                <p style="color: #666;">Thank you for your payment!<br>Happy Homes Administration</p>
            </body>
            </html>
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False
            )
            print(f"✅ Confirmation email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def send_admin_notification(self, homeowner_name, amount, reference):
        """Notify admin when payment received"""
        try:
            admin_emails = list(User.objects.filter(is_staff=True).values_list('email', flat=True))
            
            if not admin_emails:
                return False
            
            subject = f"✅ Payment Received - {homeowner_name}"
            message = f"""
Payment received from {homeowner_name}

Amount: ₱{amount}
Reference: {reference}
Status: PAID

Happy Homes System
            """
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #10b981;">✅ Payment Received</h2>
                <p>Payment received from <strong>{homeowner_name}</strong></p>
                <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Amount:</strong> ₱{amount}</p>
                    <p style="margin: 5px 0;"><strong>Reference:</strong> {reference}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #10b981; font-weight: bold;">PAID</span></p>
                </div>
                <p style="color: #666;">Happy Homes System</p>
            </body>
            </html>
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                html_message=html_message,
                fail_silently=True
            )
            print(f"✅ Admin notification sent")
            return True
        except Exception as e:
            print(f"❌ Admin email error: {e}")
            return False


# Singleton instance
simple_paymongo = SimplePayMongo()
