"""
SIMPLE PAYMENT SYSTEM - HOW IT WORKS
=====================================

✅ COMPLETE SETUP DONE!

## What Happens Automatically:

### 1. ADMIN CREATES SERVICE FEE
   - Admin fills out form in /admin-service-fee
   - Sets amount (₱500), due date, month/year
   - Clicks "Create Service Fee"
   
   → System automatically:
   ✓ Generates PayMongo payment link
   ✓ Creates reference number (e.g., 4PX7TK)
   ✓ Saves checkout URL
   ✓ Sends email to homeowner with payment link
   
   Admin sees in table:
   ┌─────────────────────────────────────┐
   │ Juan Cruz │ ₱500 │ 🔵 UNPAID       │
   │           │      │ Ref: 4PX7TK     │
   │           │      │ 📋 Link         │
   └─────────────────────────────────────┘

### 2. HOMEOWNER RECEIVES EMAIL
   Subject: 💰 New Service Fee - ₱500
   
   Hi Juan Cruz,
   Amount: ₱500
   Due Date: January 15, 2026
   Reference: 4PX7TK
   
   [Pay Now via GCash/PayMaya] ← button
   
### 3. HOMEOWNER PAYS
   - Clicks link or goes to /billing
   - Sees big "Pay Now" button
   - Clicks → redirected to PayMongo page
   - Scans QR with GCash/bank app
   - Pays ₱500
   - Done in 30 seconds!

### 4. WEBHOOK FIRES (Instant!)
   - PayMongo sends notification to your server
   - Database updates:
     ✓ payment_link.paid = True
     ✓ service_fee.status = 'paid'
   - Sends confirmation emails:
     ✓ To homeowner: "Payment Received!"
     ✓ To admin: "Juan Cruz paid ₱500"

### 5. ADMIN SEES UPDATE (No refresh needed!)
   ┌─────────────────────────────────────┐
   │ Juan Cruz │ ₱500 │ ✅ PAID         │
   │           │      │ Ref: 4PX7TK     │
   │           │      │ 2:30 PM         │
   └─────────────────────────────────────┘

## STATUS LOGIC:

🔵 UNPAID  → Before due date, not paid
🔴 OVERDUE → Past due date, not paid (auto-checks)
✅ PAID    → Payment received via webhook

## EMAIL NOTIFICATIONS:

1. **When Admin Creates:**
   - Homeowner gets email with payment link
   
2. **When Homeowner Pays:**
   - Homeowner gets: "✅ Payment Received!"
   - Admin gets: "✅ Payment from Juan Cruz"

## TESTING:

1. Create service fee as admin
2. Check your terminal - you'll see:
   ✅ Payment link created: 4PX7TK
   ✅ Email sent to homeowner@email.com

3. Login as homeowner
4. Go to /billing
5. See payment link with "Pay Now" button

6. Click link (goes to PayMongo test page)
7. Use test payment (PayMongo sandbox)
8. Webhook fires
9. Status updates to PAID!

## WEBHOOK URL (for PayMongo dashboard):

http://your-domain.com/api/webhook/payment/

For local testing with ngrok:
1. Run: ngrok http 8000
2. Copy URL: https://xxxx.ngrok.io
3. Add to PayMongo webhook: https://xxxx.ngrok.io/api/webhook/payment/

## FILES CREATED:

✅ backend/api/simple_paymongo.py - Payment link generator + emails
✅ backend/api/simple_webhook.py - Webhook handler
✅ backend/api/models.py - PaymentLink model added
✅ backend/api/views.py - Auto-creates links when admin creates fee
✅ backend/api/serializers.py - Returns payment link data
✅ backend/api/urls.py - Webhook endpoint added
✅ frontend Billing.tsx - Simple payment display
✅ frontend AdminServiceFee.tsx - Reference numbers in table

## NO COMPLICATED FORMS!

Homeowners just click "Pay Now" → redirected to PayMongo → done!
No need to fill billing info, payment method, etc.
Everything is auto-generated when admin creates the fee.

🎉 READY TO USE!
"""
