"""
PayMongo Configuration for QRPh/GCash Payments
"""

import os

# PayMongo Mode: 'test' or 'live'
PAYMONGO_MODE = os.getenv('PAYMONGO_MODE', 'test')

# Your PayMongo API Keys
PAYMONGO_TEST_SECRET_KEY = 'sk_test_JQtwE2qw3Ra2jx3gb2XejUrv'
PAYMONGO_TEST_PUBLIC_KEY = 'pk_test_G4tPrDqW7SpqfzK2xbTX2yVT'

# Live API Keys (for production later)
PAYMONGO_LIVE_PUBLIC_KEY = os.getenv('PAYMONGO_LIVE_PUBLIC_KEY', '')
PAYMONGO_LIVE_SECRET_KEY = os.getenv('PAYMONGO_LIVE_SECRET_KEY', '')

# Select keys based on mode
PAYMONGO_PUBLIC_KEY = PAYMONGO_TEST_PUBLIC_KEY if PAYMONGO_MODE == 'test' else PAYMONGO_LIVE_PUBLIC_KEY
PAYMONGO_SECRET_KEY = PAYMONGO_TEST_SECRET_KEY if PAYMONGO_MODE == 'test' else PAYMONGO_LIVE_SECRET_KEY

# API Base URL
PAYMONGO_BASE_URL = 'https://api.paymongo.com/v1'

# Frontend URLs
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
PAYMENT_SUCCESS_URL = f'{FRONTEND_URL}/billing?payment=success'
PAYMENT_FAILED_URL = f'{FRONTEND_URL}/billing?payment=failed'

# Test Mode Flag
IS_TEST_MODE = PAYMONGO_MODE == 'test'

print(f"🔧 PayMongo Config Loaded - Mode: {PAYMONGO_MODE}, Test: {IS_TEST_MODE}")
