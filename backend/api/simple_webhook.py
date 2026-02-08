from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import PaymentLink
from .simple_paymongo import simple_paymongo


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def payment_webhook(request):
    """Auto-update when payment received from PayMongo"""
    try:
        data = request.data
        event_type = data.get('data', {}).get('attributes', {}).get('type')
        
        print(f"📥 Webhook received: {event_type}")
        
        if event_type == 'link.payment.paid':
            link_data = data.get('data', {}).get('attributes', {}).get('data', {})
            link_id = link_data.get('id')
            
            print(f"🔍 Looking for link_id: {link_id}")
            
            # Find payment link
            payment_link = PaymentLink.objects.filter(link_id=link_id).first()
            
            if payment_link:
                # Update payment link
                payment_link.paid = True
                payment_link.paid_at = timezone.now()
                payment_link.save()
                
                # Update service fee status
                service_fee = payment_link.service_fee
                service_fee.status = 'paid'
                service_fee.save()
                
                print(f"✅ PAID! Ref: {payment_link.reference_number}")
                
                # Send confirmation email to homeowner
                if service_fee.homeowner.email:
                    simple_paymongo.send_payment_confirmation(
                        to_email=service_fee.homeowner.email,
                        homeowner_name=service_fee.homeowner.username,
                        amount=payment_link.amount,
                        reference=payment_link.reference_number
                    )
                
                # Notify admin
                simple_paymongo.send_admin_notification(
                    homeowner_name=service_fee.homeowner.username,
                    amount=payment_link.amount,
                    reference=payment_link.reference_number
                )
            else:
                print(f"⚠️ Payment link not found for link_id: {link_id}")
        
        return Response({'status': 'ok'}, status=200)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=400)
