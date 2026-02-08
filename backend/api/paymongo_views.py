"""
PayMongo Payment API Views (QRPh/GCash/E-Wallet)
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .models import ServiceFee, PayMongoTransaction
from .paymongo_service import paymongo_service
from paymongo_config import IS_TEST_MODE, FRONTEND_URL


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request, service_fee_id):
    """
    Create E-Wallet payment via PayMongo (QRPh/GCash/GrabPay)
    
    POST /api/service-fees/{id}/paymongo-payment/
    Body: {
        "payment_method": "qrph",  // or "gcash", "grab_pay", "paymaya"
        "billing_name": "...",
        "billing_email": "...",
        "billing_phone": "..."
    }
    """
    user = request.user
    service_fee = get_object_or_404(ServiceFee, id=service_fee_id)
    
    # Check ownership
    if service_fee.homeowner != user:
        return Response({
            'error': 'You can only pay for your own service fees'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if already paid
    if service_fee.status == 'paid':
        return Response({
            'error': 'This service fee is already paid'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get billing details
    billing_name = request.data.get('billing_name', f"{user.first_name} {user.last_name}".strip() or user.username)
    billing_email = request.data.get('billing_email', user.email)
    billing_phone = request.data.get('billing_phone', '')
    payment_method = request.data.get('payment_method', 'qrph')  # Default to QRPh
    
    if not billing_phone:
        return Response({
            'error': 'Phone number is required for payment'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not billing_email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Prepare metadata
    metadata = {
        'service_fee_id': str(service_fee_id),
        'homeowner_id': str(user.id),
        'homeowner_name': user.username,
        'month': service_fee.month or '',
        'year': str(service_fee.year) if service_fee.year else '',
        'success_url': f'{FRONTEND_URL}/billing?payment=success&service_fee={service_fee_id}',
        'failed_url': f'{FRONTEND_URL}/billing?payment=failed&service_fee={service_fee_id}'
    }
    
    # Create payment source (supports QRPh, GCash, etc.)
    result = paymongo_service.create_payment_source(
        amount=service_fee.amount,
        billing_details={
            'name': billing_name,
            'email': billing_email,
            'phone': billing_phone
        },
        payment_method=payment_method,
        metadata=metadata
    )
    
    if not result['success']:
        return Response({
            'error': result.get('message', 'Failed to create payment'),
            'details': result.get('error_data')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Save transaction
    transaction = PayMongoTransaction.objects.create(
        service_fee=service_fee,
        source_id=result['source_id'],
        amount=service_fee.amount,
        currency='PHP',
        status='pending',
        checkout_url=result['checkout_url'],
        billing_name=billing_name,
        billing_email=billing_email,
        billing_phone=billing_phone,
        test_mode=IS_TEST_MODE,
        raw_data=result.get('raw_response')
    )
    
    return Response({
        'success': True,
        'transaction_id': transaction.id,
        'source_id': result['source_id'],
        'checkout_url': result['checkout_url'],
        'payment_method': payment_method,
        'amount': float(service_fee.amount),
        'currency': 'PHP',
        'status': 'pending',
        'test_mode': IS_TEST_MODE,
        'message': f'Redirect to checkout URL to complete payment via {payment_method.upper()}'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_transaction_status(request, transaction_id):
    """Check PayMongo transaction status"""
    transaction = get_object_or_404(PayMongoTransaction, id=transaction_id)
    
    # Check access
    if transaction.service_fee.homeowner != request.user and not request.user.is_staff:
        return Response({
            'error': 'Unauthorized'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Fetch latest status from PayMongo
    source_result = paymongo_service.retrieve_source(transaction.source_id)
    
    if source_result['success']:
        transaction.status = source_result['status']
        
        if source_result['status'] == 'chargeable':
            payment_result = paymongo_service.create_payment_from_source(
                source_id=transaction.source_id,
                description=f"Service Fee - {transaction.service_fee.month} {transaction.service_fee.year}"
            )
            
            if payment_result['success']:
                transaction.payment_id = payment_result['payment_id']
                transaction.status = payment_result['status']
                
                if payment_result['status'] == 'paid':
                    transaction.paid_at = timezone.now()
                    transaction.service_fee.status = 'paid'
                    transaction.service_fee.save()
        
        transaction.save()
    
    return Response({
        'transaction_id': transaction.id,
        'source_id': transaction.source_id,
        'payment_id': transaction.payment_id,
        'status': transaction.status,
        'amount': float(transaction.amount),
        'paid_at': transaction.paid_at,
        'test_mode': transaction.test_mode
    })


@csrf_exempt
@api_view(['POST'])
def paymongo_webhook(request):
    """Handle PayMongo webhooks"""
    try:
        data = request.data
        event_type = data.get('data', {}).get('attributes', {}).get('type')
        
        print(f"📥 Webhook received: {event_type}")
        
        if event_type == 'source.chargeable':
            source_data = data.get('data', {}).get('attributes', {}).get('data', {})
            source_id = source_data.get('id')
            
            try:
                transaction = PayMongoTransaction.objects.get(source_id=source_id)
                transaction.status = 'chargeable'
                transaction.save()
                
                payment_result = paymongo_service.create_payment_from_source(
                    source_id=source_id,
                    description=f"Service Fee - {transaction.service_fee.month} {transaction.service_fee.year}"
                )
                
                if payment_result['success']:
                    transaction.payment_id = payment_result['payment_id']
                    transaction.status = payment_result['status']
                    transaction.save()
                    
            except PayMongoTransaction.DoesNotExist:
                pass
        
        elif event_type == 'payment.paid':
            payment_data = data.get('data', {}).get('attributes', {}).get('data', {})
            payment_id = payment_data.get('id')
            
            try:
                transaction = PayMongoTransaction.objects.get(payment_id=payment_id)
                transaction.status = 'paid'
                transaction.paid_at = timezone.now()
                transaction.service_fee.status = 'paid'
                transaction.service_fee.save()
                transaction.save()
            except PayMongoTransaction.DoesNotExist:
                pass
        
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return HttpResponse(status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_transactions(request):
    """Get all PayMongo transactions for current user"""
    user = request.user
    
    if user.is_staff:
        transactions = PayMongoTransaction.objects.all()
    else:
        transactions = PayMongoTransaction.objects.filter(service_fee__homeowner=user)
    
    data = [{
        'id': t.id,
        'service_fee_id': t.service_fee.id,
        'amount': float(t.amount),
        'status': t.status,
        'checkout_url': t.checkout_url,
        'paid_at': t.paid_at,
        'created_at': t.created_at,
        'test_mode': t.test_mode
    } for t in transactions]
    
    return Response(data)
