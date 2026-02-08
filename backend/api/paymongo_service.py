"""
PayMongo Service for QRPh/GCash/E-Wallet Payments
"""

import requests
import base64
from decimal import Decimal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paymongo_config import (
    PAYMONGO_SECRET_KEY,
    PAYMONGO_PUBLIC_KEY,
    PAYMONGO_BASE_URL,
    PAYMENT_SUCCESS_URL,
    PAYMENT_FAILED_URL,
    IS_TEST_MODE
)


class PayMongoService:
    """Service for handling PayMongo payments"""
    
    def __init__(self):
        self.secret_key = PAYMONGO_SECRET_KEY
        self.public_key = PAYMONGO_PUBLIC_KEY
        self.base_url = PAYMONGO_BASE_URL
        self.headers = self._get_headers()
        print(f"✅ PayMongo Service initialized with secret key: {self.secret_key[:15]}...")
    
    def _get_headers(self):
        """Generate authorization headers"""
        auth_string = f'{self.secret_key}:'
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        return {
            'Authorization': f'Basic {auth_bytes}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def create_payment_source(self, amount, billing_details, payment_method='qrph', metadata=None):
        """
        Create a payment source (supports QRPh, GCash, GrabPay, PayMaya)
        
        Args:
            amount (Decimal): Amount in PHP
            billing_details (dict): {name, email, phone}
            payment_method (str): 'qrph', 'gcash', 'grab_pay', 'paymaya'
            metadata (dict): Custom metadata
            
        Returns:
            dict: Payment source details with checkout_url
        """
        # Convert to centavos
        amount_centavos = int(Decimal(str(amount)) * 100)
        
        # Map payment methods - grab_pay uses QRPh which works with all QRPh-enabled wallets/banks
        payment_type_map = {
            'gcash': 'gcash',
            'grab_pay': 'grab_pay',
            'paymaya': 'paymaya',
            'qrph': 'grab_pay'  # QRPh uses grab_pay type
        }
        
        payment_type = payment_type_map.get(payment_method.lower(), 'grab_pay')
        
        payload = {
            "data": {
                "attributes": {
                    "type": payment_type,
                    "amount": amount_centavos,
                    "currency": "PHP",
                    "redirect": {
                        "success": metadata.get('success_url', PAYMENT_SUCCESS_URL) if metadata else PAYMENT_SUCCESS_URL,
                        "failed": metadata.get('failed_url', PAYMENT_FAILED_URL) if metadata else PAYMENT_FAILED_URL
                    },
                    "billing": {
                        "name": billing_details.get('name'),
                        "email": billing_details.get('email'),
                        "phone": billing_details.get('phone')
                    }
                }
            }
        }
        
        # Add metadata if provided
        if metadata:
            payload["data"]["attributes"]["metadata"] = metadata
        
        try:
            print(f"📤 Creating {payment_method.upper()} payment source for ₱{amount}...")
            response = requests.post(
                f'{self.base_url}/sources',
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            data = result.get('data', {})
            attributes = data.get('attributes', {})
            redirect = attributes.get('redirect', {})
            
            checkout_url = redirect.get('checkout_url')
            print(f"✅ {payment_method.upper()} source created: {data.get('id')}")
            print(f"🔗 Checkout URL: {checkout_url}")
            
            return {
                'success': True,
                'source_id': data.get('id'),
                'type': attributes.get('type'),
                'payment_method': payment_method,
                'amount': amount,
                'currency': attributes.get('currency'),
                'status': attributes.get('status'),
                'checkout_url': checkout_url,
                'test_mode': IS_TEST_MODE,
                'raw_response': result
            }
            
        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except:
                pass
            
            print(f"❌ HTTP Error: {e}")
            print(f"❌ Error data: {error_data}")
            
            return {
                'success': False,
                'error': str(e),
                'error_data': error_data,
                'message': f'Failed to create {payment_method} payment source'
            }
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Unexpected error occurred'
            }
    
    def create_payment_from_source(self, source_id, description=''):
        """Create a payment from a chargeable source"""
        payload = {
            "data": {
                "attributes": {
                    "description": description,
                    "source": {
                        "id": source_id,
                        "type": "source"
                    },
                    "currency": "PHP"
                }
            }
        }
        
        try:
            print(f"📤 Creating payment from source: {source_id}...")
            response = requests.post(
                f'{self.base_url}/payments',
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            data = result.get('data', {})
            attributes = data.get('attributes', {})
            
            print(f"✅ Payment created: {data.get('id')} - Status: {attributes.get('status')}")
            
            return {
                'success': True,
                'payment_id': data.get('id'),
                'status': attributes.get('status'),
                'amount': attributes.get('amount', 0) / 100,
                'currency': attributes.get('currency'),
                'paid_at': attributes.get('paid_at'),
                'raw_response': result
            }
            
        except Exception as e:
            print(f"❌ Payment creation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create payment'
            }
    
    def retrieve_source(self, source_id):
        """Retrieve source details"""
        try:
            response = requests.get(
                f'{self.base_url}/sources/{source_id}',
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            data = result.get('data', {})
            attributes = data.get('attributes', {})
            
            return {
                'success': True,
                'source_id': data.get('id'),
                'type': attributes.get('type'),
                'status': attributes.get('status'),
                'amount': attributes.get('amount', 0) / 100,
                'currency': attributes.get('currency'),
                'metadata': attributes.get('metadata', {}),
                'raw_response': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve source'
            }
    
    def retrieve_payment(self, payment_id):
        """Retrieve payment details"""
        try:
            response = requests.get(
                f'{self.base_url}/payments/{payment_id}',
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            data = result.get('data', {})
            attributes = data.get('attributes', {})
            
            return {
                'success': True,
                'payment_id': data.get('id'),
                'status': attributes.get('status'),
                'amount': attributes.get('amount', 0) / 100,
                'currency': attributes.get('currency'),
                'paid_at': attributes.get('paid_at'),
                'fee': attributes.get('fee', 0) / 100,
                'net_amount': attributes.get('net_amount', 0) / 100,
                'source': attributes.get('source', {}),
                'raw_response': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve payment'
            }


# Singleton instance
paymongo_service = PayMongoService()
