import os
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

# DRF imports
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_decode

from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rest_framework import generics
from django.core.cache import cache
from django.utils.crypto import get_random_string
# Standard library imports
import requests
import json

# Local app imports
from .models import (
    BillingRecord,
    Review,
    AvailableSlot,
    Maintenance,
    MaintenanceRequest,
    MaintenanceProvider,
    Post,
    Message,
    Subdivision,
    Pin,
    UserProfile,
    Booking,
    Facility,
    News,
    Alert,
    ContactInfo,
    ContactMessage,
    EmergencyContact,
    FAQ,
    ServiceFee,
    BlogComment,
    Bulletin,
    BulletinComment,
    CommunityMedia,
    VisitorRequest,
    ResidentPin,
    Visitor,
    House,
    HouseImage,
)
from .serializers import (
    BillingSerializer,
    BillingUploadSerializer,
    HistoricalRecordSerializer,
    PostSerializer,
    MessageSerializer,
    SubdivisionSerializer,
    PinSerializer,
    ReviewSerializer,
    UserProfileSerializer,
    UserSerializer,
    BookingSerializer,
    FacilitySerializer,
    AvailableSlotSerializer,
    MaintenanceSerializer,
    NewsSerializer,
    AlertSerializer,
    ContactInfoSerializer,
    ContactMessageSerializer,
    EmergencyContactSerializer,
    HistoricalRecordSerializer,
    FAQSerializer,
    ServiceFeeSerializer,
    BlogCommentSerializer,
    BulletinCommentSerializer,
    BulletinSerializer,
    CommunityMediaSerializer,
    VisitorRequestSerializer,
    VisitorSerializer,
    MaintenanceRequestSerializer,
    MaintenanceProviderSerializer,
)

from itertools import chain


@api_view(['POST'])
@permission_classes([AllowAny])
def send_verification_email(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email required'}, status=400)
    
    code = get_random_string(6, allowed_chars='0123456789')
    cache.set(email, code, timeout=300)  # valid for 5 minutes

    send_mail(
        'Your Verification Code',
        f'Your Happy Homes verification code is: {code}',
        'no-reply@happyhomes.com',
        [email],
        fail_silently=False,
    )

    return Response({'message': 'Verification code sent'})

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_code(request):
    email = request.data.get('email')
    code = request.data.get('code')

    if not email or not code:
        return Response({'error': 'Email and code required'}, status=400)

    stored_code = cache.get(email)
    if stored_code == code:
        return Response({'verified': True})
    else:
        return Response({'verified': False}, status=400)
# Get pending verifications
@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_verifications(request):
    pending_profiles = UserProfile.objects.filter(is_verified=False, document__isnull=False)
    data = []
    for profile in pending_profiles:
        data.append({
            'id': profile.user.id,
            'username': profile.user.username,
            'email': profile.user.email,
            'document': profile.document.url if profile.document else None,
            'is_verified': profile.is_verified
        })
    return Response(data)

# Verify user
# Verify user
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def verify_user(request, user_id):
    try:
        profile = UserProfile.objects.get(user__id=user_id)
        profile.is_verified = True
        profile.save()
        return Response({'message': 'User verified successfully'})
    except UserProfile.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """
    Allows a user to upload their own document.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if 'document' not in request.FILES:
        return Response({'detail': 'No document provided.'}, status=400)

    profile.document = request.FILES['document']
    profile.save()

    return Response({'detail': 'Document uploaded successfully.'})

from .serializers import UserAdminSerializer
from django.shortcuts import get_object_or_404

# ✅ Approve (verify) uploaded document
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def verify_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.profile  # assumes OneToOne relationship

    if not profile.document:
        return Response({"error": "No document uploaded to verify."}, status=status.HTTP_400_BAD_REQUEST)

    profile.is_verified = True
    profile.save()

    # ✅ Send approval email about verified document
    try:
        send_mail(
            subject="✅ Document Verification Approved - Happy Homes System",
            message=(
                f"Hello {user.username},\n\n"
                f"We have reviewed your submitted verification document, and it has been approved.\n\n"
                f"Your account is now fully verified and you may continue using Happy Homes.\n\n"
                f"Thank you for using Happy Homes!\n\n"
                f"Thank you for providing a valid document!\n\n"
                f"Best regards,\nHappy Homes Admin Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending approval email: {e}")

    return Response({"detail": "User document verified successfully"})


# ❌ Reject uploaded document or Unverify user
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def reject_user(request, user_id):
    try:
        profile = UserProfile.objects.get(user__id=user_id)
        user = profile.user

        # Check if this is a rejection (has document) or unverification (no document but was verified)
        is_rejection = profile.document is not None
        was_verified = profile.is_verified

        if is_rejection:
            # Rejecting a document submission
            profile.is_verified = False
            # Optional: remove invalid document from storage
            if profile.document:
                profile.document.delete(save=True)
            profile.save()

            # ✅ Send rejection email
            try:
                send_mail(
                    subject="❌ Document Verification Rejected - Happy Homes System",
                    message=(
                        f"Hello {user.username},\n\n"
                        f"Unfortunately, your submitted verification document could not be approved.\n"
                        f"Please ensure the uploaded document is clear, complete, and legitimate, then re-upload for review.\n\n"
                        f"If you have any questions, please contact the admin.\n\n"
                        f"Best regards,\nHappy Homes Admin Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending rejection email: {e}")

            return Response({'message': 'User document rejected successfully'})
        elif was_verified:
            # Unverifying a previously verified user
            profile.is_verified = False
            profile.save()

            # ✅ Send unverification email
            try:
                send_mail(
                    subject="⚠️ Account Verification Revoked - Happy Homes System",
                    message=(
                        f"Hello {user.username},\n\n"
                        f"Your account verification has been revoked by an administrator.\n"
                        f"Your account status has been changed to unverified.\n\n"
                        f"If you believe this is an error or have questions, please contact the admin.\n\n"
                        f"Best regards,\nHappy Homes Admin Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending unverification email: {e}")

            return Response({'message': 'User unverified successfully'})
        else:
            return Response({"error": "User is not verified and has no document to reject."}, status=status.HTTP_400_BAD_REQUEST)

    except UserProfile.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    

class UserHistoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = HistoricalRecordSerializer
    pagination_class = None  # Return all records without pagination

    def get_queryset(self):
        """
        Combine history from all models that have HistoricalRecords.
        Support filtering by model_name and history_user.
        Sort by most recent first.
        """
        try:
            # Get filter parameters from query string
            filter_model = self.request.query_params.get('model', None)
            filter_user = self.request.query_params.get('user', None)
            
            # Collect all history records from models with HistoricalRecords
            # Include all models that have history = HistoricalRecords()
            qs = list(chain(
                UserProfile.history.all(),
                Post.history.all(),
                Message.history.all(),
                Subdivision.history.all(),
                Pin.history.all(),
                Facility.history.all(),
                Booking.history.all(),
                News.history.all(),
                Alert.history.all(),
                ContactInfo.history.all(),
                ContactMessage.history.all(),
                EmergencyContact.history.all(),
                ResidentPin.history.all(),
                Visitor.history.all(),
                FAQ.history.all(),
                ServiceFee.history.all(),
                Bulletin.history.all(),
                BulletinComment.history.all(),
                CommunityMedia.history.all(),
                Maintenance.history.all(),
                Review.history.all(),
                BlogComment.history.all(),
                BillingRecord.history.all(),
                AvailableSlot.history.all(),
                VisitorRequest.history.all(),
                MaintenanceRequest.history.all(),
                MaintenanceProvider.history.all(),
            ))

            # Filter out None/invalid values and get model names for filtering
            valid_records = []
            for x in qs:
                if x and hasattr(x, 'history_date') and x.history_date:
                    # Get model name for filtering
                    try:
                        if x.instance:
                            model_name = x.instance.__class__.__name__
                        else:
                            model_name = x.__class__.__name__.replace('Historical', '').replace('History', '')
                    except:
                        model_name = 'Unknown'
                    
                    # Get username for filtering
                    try:
                        username = x.history_user.username if x.history_user else 'System'
                    except:
                        username = 'System'
                    
                    # Apply filters
                    if filter_model and filter_model != 'all' and model_name != filter_model:
                        continue
                    
                    if filter_user and filter_user != 'all' and username != filter_user:
                        continue
                    
                    valid_records.append(x)

            # Sort by history_date descending
            qs_sorted = sorted(
                valid_records,
                key=lambda x: x.history_date,
                reverse=True
            )
            return qs_sorted
        except Exception as e:
            # Log the error and return empty queryset
            import traceback
            print(f"Error fetching user history: {str(e)}\n{traceback.format_exc()}")
            return []

@api_view(['POST'])
@permission_classes([AllowAny])  # ✅ allow anyone
def send_email(request):
    data = request.data
    subject = data.get('subject')
    message = data.get('message')
    recipient = data.get('recipient')

    if not subject or not message or not recipient:
        return Response({"error": "subject, message, and recipient are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        return Response({"success": "Email sent successfully"})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    email = request.data.get("email")
    if not email:
        return Response({"error": "Email is required."}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"message": "If the email exists, a reset link will be sent."}, status=200)  # do not reveal

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

    subject = "Reset Your Password"
    message = f"Hi {user.username},\n\nClick the link below to reset your password:\n{reset_link}\n\nIf you didn't request this, ignore this email."
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

    return Response({"message": "If the email exists, a reset link will be sent."})
    
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    uidb64 = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not uidb64 or not token or not new_password:
        return Response({"error": "All fields are required."}, status=400)

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid link"}, status=400)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "Invalid or expired token."}, status=400)

    user.set_password(new_password)
    user.save()

    return Response({"message": "Password reset successful."}, status=200)

# Pin statistics for dashboard
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_pin_stats(request):
    total_pins = Pin.objects.count()
    # Consider either explicit status or legacy name marker
    occupied = Pin.objects.filter(Q(status__iexact="occupied") | Q(name__icontains="occupied")).count()
    # Use fixed capacity of 200 slots for subdivision capacity
    capacity = 200
    max_subdivisions = capacity
    available = max(capacity - occupied, 0)
    return Response({
        "total_pins": total_pins,
        "occupied": occupied,
        "available": available,
        "max_subdivisions": max_subdivisions
    })

# Admin dashboard stats endpoint
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard_stats(request):
    total_users = User.objects.count()
    active_bookings = Booking.objects.filter(status="approved").count()
    pending_approvals = Booking.objects.filter(status="pending").count()
    return Response({
        "total_users": total_users,
        "active_bookings": active_bookings,
        "pending_approvals": pending_approvals
    })

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"detail": "Both old and new passwords are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        # Keep user logged in after password change
        update_session_auth_hash(request, user)

        return Response({"detail": "Password updated successfully!"}, status=status.HTTP_200_OK)

# Admin-only user list
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_user_list(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

# Admin can delete a user
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_user_delete(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if user.is_superuser:
            return Response({'detail': 'Cannot delete superuser.'}, status=status.HTTP_403_FORBIDDEN)
        user.delete()
        return Response({'detail': 'User deleted.'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

# Admin can update a user (basic fields)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_user_update(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.email = request.data.get('email', user.email)
    user.username = request.data.get('username', user.username)
    user.is_staff = request.data.get('is_staff', user.is_staff)
    user.save()

    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_user_detail(request, pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """Root API endpoint that provides basic API information"""
    return Response({
        'message': 'Happy Homes API',
        'version': '1.0',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/',
            'token': '/api/token/',
            'register': '/api/register/',
        }
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    try:
        data = request.data

        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()  # normalize email
        password = data.get('password', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        contact_number = data.get('contact_number', '')

        # ✅ Validate required fields
        if not username:
            return Response({'detail': 'Username is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'detail': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if username already exists
        if User.objects.filter(username=username).exists():
            return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response({'detail': 'This email is already registered.'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        # ✅ Create or update user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.contact_number = contact_number
        profile.save()

        # ✅ Serialize and return tokens
        serializer = UserSerializer(user)
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': serializer.data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'detail': f'Registration failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_create_user(request):
    """Admin endpoint to create a new user with default password 'user123'"""
    try:
        data = request.data
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        contact_number = data.get('contact_number', '').strip()
        
        # Validate required fields
        if not username:
            return Response({'detail': 'Username is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response({'detail': 'This email is already registered.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user with default password
        DEFAULT_PASSWORD = 'user123'
        user = User.objects.create_user(
            username=username,
            password=DEFAULT_PASSWORD,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        
        # Create or update user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if contact_number:
            profile.contact_number = contact_number
        profile.save()
        
        # Serialize and return user data
        serializer = UserSerializer(user)
        return Response({
            'user': serializer.data,
            'detail': 'User created successfully with default password: user123'
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        import traceback
        print(f"Error creating user: {e}")
        print(traceback.format_exc())
        return Response({'detail': f'Failed to create user: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_user(request, id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found'}, status=404)

    # Update basic user info
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.email = request.data.get('email', user.email)
    user.username = request.data.get('username', user.username)
    user.save()

    # Update profile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile_data = request.data.get('profile', {})

    profile.contact_number = profile_data.get('contact_number', profile.contact_number)

    # Update verification status if provided
    if 'is_verified' in profile_data:
        profile.is_verified = profile_data['is_verified']

    # Update profile image if provided
    if 'profile_image' in request.FILES:
        profile.profile_image = request.FILES['profile_image']

    # Update document if provided
    if 'document' in request.FILES:
        profile.document = request.FILES['document']

    profile.save()

    return Response({'detail': 'User updated successfully'})
# --- Register ---
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def register(request):
#     data = request.data
#     if User.objects.filter(username=data.get('username')).exists():
#         return Response({'detail': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

#     user = User.objects.create_user(
#         username=data.get('username'),
#         password=data.get('password'),
#         first_name=data.get('first_name', ''),
#         last_name=data.get('last_name', ''),
#         email=data.get('email', '')
#     )

    

#     # Create UserProfile and save contact_number
#     contact_number = data.get('contact_number', '')
#     profile, created = UserProfile.objects.get_or_create(user=user)
#     profile.contact_number = contact_number
#     profile.save()

#     serializer = UserSerializer(user)
#     refresh = RefreshToken.for_user(user)

#     return Response({
#         'user': serializer.data,
#         'access': str(refresh.access_token),
#         'refresh': str(refresh),
#     })


# --- Posts ---
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # Allow public access for GET, will check auth in POST handler
def get_posts(request):
    if request.method == 'GET':
        # Anyone can view posts
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    elif request.method == 'POST':
        # Only authenticated users (preferably admins) can create posts
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required to create posts'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = PostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            post = serializer.save()
            # Re-serialize with image URL
            response_serializer = PostSerializer(post, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_posts(request):
    # Post model doesn't have a user field, so return all posts for now
    # or filter by some other criteria if needed
    posts = Post.objects.all()
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])  # GET is public, PUT/DELETE require auth check inside
def post_detail(request, pk):
    """
    Retrieve, update or delete a post instance.
    GET: Public access
    PUT/DELETE: Only admin or post owner can modify/delete
    """
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response(
            {'detail': 'Post not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        # Anyone can view posts
        serializer = PostSerializer(post)
        return Response(serializer.data)

    elif request.method == 'PUT':
        # Only authenticated users can update posts
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required to update posts'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        # Only admin or post owner can update
        # Note: Post model doesn't have a user field, so only admins can update for now
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only admins can update posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Only authenticated users can delete posts
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required to delete posts'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        # Only admin or post owner can delete
        # Note: Post model doesn't have a user field, so only admins can delete for now
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only admins can delete posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            from django.db import transaction
            
            # Store image path before deletion (if exists)
            image_path = None
            try:
                if post.image:
                    image_path = str(post.image.name) if hasattr(post.image, 'name') and post.image.name else None
            except Exception as img_path_error:
                print(f"[WARNING] Could not get image path: {img_path_error}")
            
            # Use transaction to ensure atomic deletion
            with transaction.atomic():
                post_id = post.id
                # Delete the post (BlogComment will be deleted automatically due to CASCADE)
                # HistoricalRecords will handle the history entry
                post.delete()
            
            # Delete the image file after post deletion (if it exists)
            # Do this outside the transaction to avoid file system issues affecting DB
            if image_path:
                try:
                    from django.core.files.storage import default_storage
                    if default_storage.exists(image_path):
                        default_storage.delete(image_path)
                        print(f"[INFO] Deleted image file: {image_path}")
                except Exception as img_error:
                    # Log but don't fail if image deletion fails
                    print(f"[WARNING] Could not delete post image file {image_path}: {img_error}")
            
            print(f"[INFO] Successfully deleted post {post_id}")
            return Response({'detail': 'Post deleted successfully'}, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response(
                {'detail': 'Post not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e)
            error_type = type(e).__name__
            print(f"[ERROR] Error deleting post {pk}: {error_msg}")
            print(f"[ERROR] Error type: {error_type}")
            print(f"[ERROR] Traceback:\n{error_trace}")
            
            # Return more detailed error for debugging
            return Response(
                {
                    'detail': f'Error deleting post: {error_msg}',
                    'error_type': error_type
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)

# --- Profile GET ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# --- Profile UPDATE (with image) ---
# ✅ Update profile (name, email, password, image, etc.)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Update User fields
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.email = request.data.get('email', user.email)
    user.username = request.data.get('username', user.username)
    if 'password' in request.data and request.data['password']:
        user.set_password(request.data['password'])
    user.save()

    # Update UserProfile fields (IMPORTANT: include contact_number)
    profile.contact_number = request.data.get('contact_number', profile.contact_number)
    if 'profile_image' in request.FILES:
        profile.profile_image = request.FILES['profile_image']
    profile.save()

    # Refresh both user and profile to ensure updated data
    user.refresh_from_db()
    profile.refresh_from_db()

    # Serialize full user including profile
    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# --- Messenger (temporary) ---
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def message_list_create(request):
    if request.method == 'GET':
        messages = Message.objects.all().order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# --- Subdivisions ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def subdivision_list_create(request):
    if request.method == 'GET':
        subdivisions = Subdivision.objects.all()
        serializer = SubdivisionSerializer(subdivisions, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = SubdivisionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def subdivision_detail(request, pk):
    try:
        subdivision = Subdivision.objects.get(pk=pk)
    except Subdivision.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SubdivisionSerializer(subdivision)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = SubdivisionSerializer(subdivision, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        subdivision.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [AllowAny]  # Allow public access by default
    authentication_classes = []  # No authentication required by default
    
    def get_authenticators(self):
        """Override to require authentication only for write operations"""
        # Check request method - GET requests don't need authentication
        request = getattr(self, 'request', None)
        if request and request.method in ['GET', 'OPTIONS', 'HEAD']:
            return []  # No authentication for read
        # Require authentication for create, update, delete (POST, PUT, PATCH, DELETE)
        return [JWTAuthentication()]
    
    def get_permissions(self):
        # Allow public read access, but require admin for write operations
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        # For write operations, require authentication and admin
        return [IsAuthenticated(), IsAdminUser()]

class IsAdminOrOwner(permissions.BasePermission):
    """
    Custom permission to only allow admins or the owner of the object to access it.
    """
    def has_permission(self, request, view):
        """Allow authenticated users to create/list bookings"""
        # For create/list actions, just check if user is authenticated
        # The IsAuthenticated permission class already handles this, but we add it here for clarity
        if not request.user or not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        """For retrieve/update/delete, check if user is admin or owner"""
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or obj.user == request.user

from rest_framework.exceptions import PermissionDenied
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        facility_id = self.request.query_params.get("facility_id")

        # Ensure user is authenticated
        if not self.request.user or not self.request.user.is_authenticated:
            return Booking.objects.none()

        # Admins can see all bookings
        if self.request.user.is_staff:
            qs = Booking.objects.select_related('facility', 'user').all()
        else:
            # Homeowners/residents see only their own bookings
            qs = Booking.objects.select_related('facility', 'user').filter(user=self.request.user)

        if facility_id:
            qs = qs.filter(facility_id=facility_id)

        return qs.order_by("-date", "-start_time")  # Order by newest first
    
    def get_serializer_context(self):
        """Ensure request is always in serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        """Override create to reload booking with relationships before response"""
        import traceback
        # Import exceptions explicitly to avoid scoping issues
        from rest_framework.exceptions import ValidationError as VE, PermissionDenied as PD
        try:
            # Validate input data first
            print(f"[INFO] Received booking data: {request.data}")
            print(f"[INFO] Request user: {request.user.username if request.user.is_authenticated else 'Not authenticated'}")
            print(f"[INFO] User is staff: {request.user.is_staff if request.user.is_authenticated else False}")
            
            # Check if user is authenticated
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {"detail": "Authentication required."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Validate serializer
            serializer = self.get_serializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
                print(f"[SUCCESS] Serializer validated: {serializer.validated_data}")
            except Exception as validation_error:
                print(f"[ERROR] Serializer validation failed: {validation_error}")
                print(traceback.format_exc())
                # Return validation error as 400
                error_detail = str(validation_error)
                if hasattr(validation_error, 'detail'):
                    error_detail = validation_error.detail
                return Response(
                    {"detail": error_detail},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Perform create (this saves the booking)
            try:
                self.perform_create(serializer)
            except VE as ve:
                # Re-raise ValidationError so it can be caught by outer handler
                print(f"[ERROR] ValidationError in perform_create: {ve}")
                raise
            except PD as pd:
                # Re-raise PermissionDenied so it can be caught by outer handler
                print(f"[ERROR] PermissionDenied in perform_create: {pd}")
                raise
            except Exception as perform_error:
                print(f"[ERROR] perform_create failed with unexpected error: {perform_error}")
                print(traceback.format_exc())
                # Return as 400 error
                return Response(
                    {"detail": f"An error occurred: {str(perform_error)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the created booking instance
            booking = serializer.instance
            if not booking:
                return Response(
                    {"detail": "Booking instance was not created"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            if not hasattr(booking, 'pk') or not booking.pk:
                return Response(
                    {"detail": "Booking was not saved properly"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            print(f"[SUCCESS] Booking created with ID: {booking.pk}")
            
            # Reload booking with all relationships for proper serialization
            try:
                booking = Booking.objects.select_related('facility', 'user').get(pk=booking.pk)
                print(f"[SUCCESS] Booking reloaded with relationships")
            except Booking.DoesNotExist:
                print(f"[WARNING] Could not reload booking, using original instance")
                booking = serializer.instance
            except Exception as reload_error:
                print(f"[WARNING] Error reloading booking: {reload_error}")
                booking = serializer.instance
            
            # Create response serializer with reloaded booking
            try:
                response_serializer = self.get_serializer(booking)
                response_data = response_serializer.data
                print(f"[SUCCESS] Response serialized successfully")
            except Exception as serialize_error:
                print(f"[ERROR] Error serializing booking response: {serialize_error}")
                print(traceback.format_exc())
                # Fallback to basic data
                try:
                    facility_name = 'Unknown'
                    if hasattr(booking, 'facility') and booking.facility:
                        try:
                            facility_name = booking.facility.get_name_display()
                        except:
                            try:
                                facility_name = str(booking.facility.name)
                            except:
                                facility_name = 'Unknown'
                except:
                    facility_name = 'Unknown'
                
                try:
                    user_name = 'Unknown'
                    if hasattr(booking, 'user') and booking.user:
                        user_name = booking.user.username
                except:
                    user_name = 'Unknown'
                
                response_data = {
                    'id': getattr(booking, 'id', None),
                    'facility_id': getattr(booking, 'facility_id', None),
                    'facility_name': facility_name,
                    'date': str(getattr(booking, 'date', '')) if hasattr(booking, 'date') else '',
                    'start_time': str(getattr(booking, 'start_time', '')) if hasattr(booking, 'start_time') else '',
                    'end_time': str(getattr(booking, 'end_time', '')) if hasattr(booking, 'end_time') else '',
                    'status': getattr(booking, 'status', 'pending'),
                    'user_name': user_name,
                }
            
            headers = self.get_success_headers(response_data)
            return Response(
                response_data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except VE as e:
            print(f"[ERROR] Validation error in create: {e}")
            print(traceback.format_exc())
            # Return validation error
            error_detail = e.detail if hasattr(e, 'detail') else str(e)
            return Response(
                {"detail": error_detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PD as e:
            print(f"[ERROR] Permission denied in create: {e}")
            print(traceback.format_exc())
            # Return permission error
            error_detail = e.detail if hasattr(e, 'detail') else "Permission denied."
            return Response(
                {"detail": error_detail},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"[ERROR] Unexpected error in create: {e}")
            print(error_trace)
            # Return a user-friendly error message
            error_message = str(e)
            if "facility" in error_message.lower():
                error_message = "Invalid facility selected. Please try again."
            elif "time" in error_message.lower() or "date" in error_message.lower():
                error_message = "Invalid date or time selected. Please check your selection."
            elif "verified" in error_message.lower() or "permission" in error_message.lower():
                error_message = "Your account needs to be verified before booking facilities. Please contact admin."
            else:
                error_message = "An error occurred while creating the booking. Please try again or contact support."
            return Response(
                {"detail": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Handle booking creation with validation"""
        # Import ValidationError at the start to ensure it's in scope
        from rest_framework.exceptions import ValidationError as VE, PermissionDenied as PD
        
        try:
            user = self.request.user
            profile = getattr(user, "profile", None)

            # Admins can book without verification
            if not user.is_staff:
                if not profile or not profile.is_verified:
                    raise PD( 
                        detail="Your account is not verified. "
                               "Please upload your documents and wait for admin approval before booking."
                    )

            # Check if booking date/time is in the past
            booking_data = serializer.validated_data
            booking_date = booking_data.get('date')
            booking_start_time = booking_data.get('start_time')
            booking_end_time = booking_data.get('end_time')
            facility = booking_data.get('facility')
            
            from django.utils import timezone
            
            # Validate required fields
            if not booking_date or not booking_start_time or not booking_end_time or not facility:
                raise VE({"detail": "Missing required booking information."})
            
            # Check for past dates/times
            now = timezone.now()
            current_date = now.date()
            current_time = now.time()
            
            if booking_date < current_date:
                raise VE({"detail": "Cannot book dates in the past."})
            
            if booking_date == current_date and booking_start_time < current_time:
                raise VE({"detail": "Cannot book times in the past for today's date."})
            
            # Validate time range
            if booking_end_time <= booking_start_time:
                raise VE({"detail": "End time must be after start time."})
            
            # Check for duplicate/overlapping bookings (pending or approved only)
            # Rejected bookings don't block the slot
            existing_bookings = Booking.objects.filter(
                facility=facility,
                date=booking_date,
                status__in=['pending', 'approved']  # Only pending and approved block the slot
            )
            
            for existing_booking in existing_bookings:
                # Check if time slots overlap
                # Overlap occurs if: new_start < existing_end AND new_end > existing_start
                if not (booking_end_time <= existing_booking.start_time or 
                        booking_start_time >= existing_booking.end_time):
                    raise VE({
                        "detail": f"This time slot is already booked. "
                                 f"Existing booking: {existing_booking.start_time.strftime('%I:%M %p')} - "
                                 f"{existing_booking.end_time.strftime('%I:%M %p')} (Status: {existing_booking.status.upper()})"
                    })
            
            # Check if facility is under maintenance
            maintenance_periods = Maintenance.objects.filter(
                facility=facility,
                start_date__lte=booking_date,
                end_date__gte=booking_date
            )
            
            for maintenance in maintenance_periods:
                if maintenance.start_time and maintenance.end_time:
                    # Specific time maintenance - check if booking overlaps
                    if not (booking_end_time <= maintenance.start_time or booking_start_time >= maintenance.end_time):
                        raise VE({
                            "detail": f"Facility is under maintenance from {maintenance.start_time.strftime('%I:%M %p')} "
                                     f"to {maintenance.end_time.strftime('%I:%M %p')} on {maintenance.start_date.strftime('%B %d, %Y')}. "
                                     f"Reason: {maintenance.reason or 'Maintenance period'}"
                        })
                else:
                    # All-day maintenance
                    raise VE({
                        "detail": f"Facility is under maintenance all day on {maintenance.start_date.strftime('%B %d, %Y')}. "
                                 f"Reason: {maintenance.reason or 'Maintenance period'}"
                    })

            # Save the booking
            try:
                booking = serializer.save(user=user)
                print(f"[SUCCESS] Booking saved successfully: ID={booking.id if hasattr(booking, 'id') else 'N/A'}")
                
                # Reload booking with relationships before sending emails
                try:
                    booking = Booking.objects.select_related('facility', 'user').get(pk=booking.pk)
                    print(f"[DEBUG] Booking reloaded - User: {booking.user.username}, Email: {booking.user.email}")
                except Booking.DoesNotExist:
                    print(f"[WARNING] Could not reload booking for email notification")
                
                # Send email notifications after successful booking creation
                # Use try-except to prevent email errors from breaking booking creation
                try:
                    self._send_booking_created_emails(booking)
                except Exception as email_error:
                    print(f"[WARNING] Email notification failed (booking still created): {email_error}")
                    import traceback
                    print(traceback.format_exc())
            except Exception as save_error:
                import traceback
                print(f"[ERROR] Error saving booking: {save_error}")
                print(traceback.format_exc())
                # Re-raise the error so it can be caught by the create method
                raise
        except VE as ve:
            # Re-raise validation errors as-is so they can be caught by create method
            print(f"[ERROR] ValidationError in perform_create: {ve}")
            raise
        except PD as pd:
            # Re-raise permission errors as-is
            print(f"[ERROR] PermissionDenied in perform_create: {pd}")
            raise
        except Exception as e:
            # Log unexpected errors and convert to ValidationError
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] Unexpected error in perform_create: {e}")
            print(error_trace)
            # Use VE which was imported at the start of the method
            raise VE({"detail": f"An error occurred while creating the booking: {str(e)}"})
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to handle deletion properly"""
        booking_id = kwargs.get('pk')
        try:
            # Get booking with relationships pre-loaded from queryset
            queryset = self.get_queryset()
            try:
                instance = queryset.get(pk=booking_id)
            except Booking.DoesNotExist:
                return Response(
                    {"detail": "Booking not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check permissions
            if not request.user.is_staff and instance.user_id != request.user.id:
                raise PermissionDenied("You can only delete your own bookings.")
            
            # Store booking info for email notification (before deletion)
            # Safely access relationships with fallbacks
            booking_id_val = instance.id
            user_id = instance.user_id
            facility_id = instance.facility_id
            booking_date = instance.date
            start_time = instance.start_time
            end_time = instance.end_time
            
            # Safely get user email
            user_email = None
            try:
                if hasattr(instance, 'user') and instance.user:
                    user_email = getattr(instance.user, 'email', None)
            except (AttributeError, TypeError):
                # If user relationship fails, try to get email from user_id
                try:
                    from django.contrib.auth.models import User
                    user = User.objects.get(id=user_id)
                    user_email = user.email
                except (User.DoesNotExist, AttributeError):
                    user_email = None
            
            # Safely get facility name
            facility_name = "Unknown Facility"
            try:
                if hasattr(instance, 'facility') and instance.facility:
                    # Use get_name_display() for proper display name
                    if hasattr(instance.facility, 'get_name_display'):
                        facility_name = instance.facility.get_name_display()
                    else:
                        facility_name = getattr(instance.facility, 'name', 'Unknown Facility')
            except (AttributeError, TypeError):
                # If facility relationship fails, try to get name from facility_id
                try:
                    facility = Facility.objects.get(id=facility_id)
                    if hasattr(facility, 'get_name_display'):
                        facility_name = facility.get_name_display()
                    else:
                        facility_name = getattr(facility, 'name', 'Unknown Facility')
                except (Facility.DoesNotExist, AttributeError):
                    facility_name = "Unknown Facility"
            
            was_admin_delete = request.user.is_staff and instance.user_id != request.user.id
            
            # Delete using queryset to avoid relationship access issues
            Booking.objects.filter(pk=booking_id_val).delete()
            
            # Send email notification if admin deleted homeowner's booking
            if was_admin_delete and user_email:
                try:
                    self._send_booking_deleted_email(user_email, facility_name, booking_date, start_time, end_time)
                except Exception as email_error:
                    # Don't fail deletion if email fails
                    print(f"[WARNING] Failed to send deletion email: {email_error}")
            
            return Response(
                {"detail": "Booking deleted successfully"},
                status=status.HTTP_200_OK
            )
        except PermissionDenied:
            raise
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] Error deleting booking {booking_id}: {e}")
            print(error_trace)
            return Response(
                {"detail": f"Failed to delete booking: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Utility: format time
    def format_time_am_pm(self, time_input) -> str:
        """Format time to AM/PM format. Accepts time object or string."""
        try:
            # If it's already a time object, format it directly
            if hasattr(time_input, 'strftime'):
                return time_input.strftime("%I:%M %p")
            
            # If it's a string, try to parse it
            time_str = str(time_input)
            
            # Try different time formats
            for fmt in ["%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"]:
                try:
                    time_obj = datetime.strptime(time_str, fmt)
                    return time_obj.strftime("%I:%M %p")
                except (ValueError, TypeError):
                    continue
            
            # If all parsing fails, return as-is
            return time_str
        except Exception as e:
            print(f"[WARNING] Error formatting time {time_input}: {e}")
            return str(time_input)
    
    # Send email notifications when booking is created
    def _send_booking_created_emails(self, booking):
        """Send emails to homeowner (pending status) and all admins (new booking notification)"""
        from django.template.loader import strip_tags
        
        try:
            # Ensure relationships are loaded
            if not hasattr(booking, 'facility') or not booking.facility:
                print("[ERROR] Booking facility not loaded")
                return
            if not hasattr(booking, 'user') or not booking.user:
                print("[ERROR] Booking user not loaded")
                return
            
            # Get facility name (use get_name_display() for choice fields)
            facility_name = booking.facility.get_name_display() if hasattr(booking.facility, 'get_name_display') else str(booking.facility.name)
            
            # Format time for display
            start_time = self.format_time_am_pm(str(booking.start_time))
            end_time = self.format_time_am_pm(str(booking.end_time))
            booking_date = booking.date.strftime('%B %d, %Y')
            
            # 1. Email to Homeowner - Booking Pending
            homeowner_email = booking.user.email
            print(f"[DEBUG] Homeowner email check: {homeowner_email}")
            print(f"[DEBUG] User: {booking.user.username}, Email: {homeowner_email}")
            
            if homeowner_email:
                print(f"[DEBUG] Preparing to send email to homeowner: {homeowner_email}")
                homeowner_subject = f"Booking Request Submitted - {facility_name}"
                homeowner_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2e6F40;">Booking Request Submitted</h2>
                        <p>Dear {booking.user.first_name or booking.user.username},</p>
                        <p>Your booking request has been successfully submitted and is now <strong style="color: #f0ad4e;">PENDING</strong> admin approval.</p>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2e6F40;">
                            <p style="margin: 5px 0;"><strong>Facility:</strong> {facility_name}</p>
                            <p style="margin: 5px 0;"><strong>Date:</strong> {booking_date}</p>
                            <p style="margin: 5px 0;"><strong>Time:</strong> {start_time} - {end_time}</p>
                            <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #f0ad4e; font-weight: bold;">PENDING</span></p>
                        </div>
                        <p>You will receive an email notification once the admin reviews your booking request.</p>
                        <p>You can view your booking status at: <a href="{settings.FRONTEND_URL}/booking-amenities" style="color: #2e6F40;">View My Bookings</a></p>
                        <p style="margin-top: 30px;">Thank you,<br><strong>Happy Homes Administration</strong></p>
                    </div>
                </body>
                </html>
                """
                homeowner_plain = strip_tags(homeowner_html)
                
                try:
                    print(f"[DEBUG] Sending email from: {settings.DEFAULT_FROM_EMAIL}")
                    print(f"[DEBUG] Sending email to: {homeowner_email}")
                    print(f"[DEBUG] Email subject: {homeowner_subject}")
                    
                    # Try sending email - catch errors but don't break booking
                    try:
                        result = send_mail(
                            subject=homeowner_subject,
                            message=homeowner_plain,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[homeowner_email],
                            html_message=homeowner_html,
                            fail_silently=False,  # Set to False to see actual errors
                        )
                        print(f"[SUCCESS] ✅ Email sent to homeowner: {homeowner_email} (result: {result})")
                        if result == 0:
                            print(f"[WARNING] Email send returned 0 - email may not have been sent")
                    except Exception as email_send_error:
                        print(f"[ERROR] ❌ Failed to send email to homeowner: {email_send_error}")
                        import traceback
                        print(traceback.format_exc())
                        # Try with fail_silently=True as fallback
                        try:
                            result2 = send_mail(
                                subject=homeowner_subject,
                                message=homeowner_plain,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[homeowner_email],
                                html_message=homeowner_html,
                                fail_silently=True,
                            )
                            print(f"[INFO] Email sent with fail_silently=True (result: {result2})")
                        except Exception as e2:
                            print(f"[ERROR] Email completely failed even with fail_silently=True: {e2}")
                    # Don't raise - email failure shouldn't break booking
                except Exception as outer_error:
                    print(f"[ERROR] Unexpected error in email sending block: {outer_error}")
                    import traceback
                    print(traceback.format_exc())
                    # Don't raise - email failure shouldn't break booking
            else:
                print(f"[WARNING] Homeowner email is empty or not set for user: {booking.user.username}")
                print(f"[WARNING] User ID: {booking.user.id}, Username: {booking.user.username}")
            
            # 2. Email to All Admins - New Booking Notification
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            admin_emails = [admin.email for admin in admin_users if admin.email]
            
            if admin_emails:
                admin_subject = f"New Booking Request - {facility_name}"
                admin_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2e6F40;">New Booking Request</h2>
                        <p>Dear Admin,</p>
                        <p>A new booking request has been submitted and requires your review.</p>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2e6F40;">
                            <p style="margin: 5px 0;"><strong>Homeowner:</strong> {booking.user.first_name or ''} {booking.user.last_name or ''} ({booking.user.username})</p>
                            <p style="margin: 5px 0;"><strong>Email:</strong> {booking.user.email}</p>
                            <p style="margin: 5px 0;"><strong>Facility:</strong> {facility_name}</p>
                            <p style="margin: 5px 0;"><strong>Date:</strong> {booking_date}</p>
                            <p style="margin: 5px 0;"><strong>Time:</strong> {start_time} - {end_time}</p>
                            <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #f0ad4e; font-weight: bold;">PENDING</span></p>
                            <p style="margin: 5px 0;"><strong>Booking ID:</strong> #{booking.id}</p>
                        </div>
                        <p>Please review and approve or reject this booking request.</p>
                        <p><a href="{settings.FRONTEND_URL}/booking-amenities" style="background-color: #2e6F40; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Review Booking</a></p>
                        <p style="margin-top: 30px;">Thank you,<br><strong>Happy Homes System</strong></p>
                    </div>
                </body>
                </html>
                """
                admin_plain = strip_tags(admin_html)
                
                try:
                    result = send_mail(
                        subject=admin_subject,
                        message=admin_plain,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=admin_emails,
                        html_message=admin_html,
                        fail_silently=True,
                    )
                    print(f"[SUCCESS] Email sent to {len(admin_emails)} admin(s) (result: {result})")
                    print(f"[SUCCESS] Email sent to {len(admin_emails)} admin(s)")
                except Exception as e:
                    print(f"[ERROR] Failed to send email to admins: {e}")
        except Exception as e:
            print(f"[ERROR] Error in _send_booking_created_emails: {e}")
            import traceback
            print(traceback.format_exc())

    # Update method to send email when status changes
    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        old_status = booking.status
        print(f"[INFO] Update booking {booking.id}: old_status={old_status}, new_data={request.data}")
        print(f"[INFO] User is staff: {request.user.is_staff if request.user.is_authenticated else False}")
        
        response = super().update(request, *args, **kwargs)
        booking.refresh_from_db()
        
        print(f"[INFO] After update: booking.status={booking.status}, old_status={old_status}")

        if old_status != booking.status:
            print(f"[INFO] Status changed from {old_status} to {booking.status}, sending email")
            self._send_booking_status_change_email(booking, old_status)
        else:
            print(f"[WARNING] Status did not change! Still {booking.status}")

        return response

    # Partial update to send email when status changes
    def partial_update(self, request, *args, **kwargs):
        try:
            booking = self.get_object()
            old_status = booking.status
            print(f"[INFO] Partial update booking {booking.id}: old_status={old_status}, new_data={request.data}")
            print(f"[INFO] User is staff: {request.user.is_staff if request.user.is_authenticated else False}")
            
            # Ensure serializer has request context
            serializer = self.get_serializer(booking, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # Reload booking with relationships to ensure proper serialization
            booking.refresh_from_db()
            # Reload with relationships for proper serialization
            booking = Booking.objects.select_related('facility', 'user').get(pk=booking.pk)
            
            print(f"[INFO] After partial_update: booking.status={booking.status}, old_status={old_status}")
            
            # Create fresh serializer with reloaded booking for response
            response_serializer = self.get_serializer(booking)
            response_data = response_serializer.data
            print(f"[INFO] Serializer response data: {response_data}")

            # Send email notification (don't let email errors break the response)
            if old_status != booking.status:
                print(f"[INFO] Status changed from {old_status} to {booking.status}, sending email")
                try:
                    self._send_booking_status_change_email(booking, old_status)
                except Exception as email_error:
                    # Log email error but don't fail the request
                    print(f"[WARNING] Failed to send status change email: {email_error}")
                    import traceback
                    print(traceback.format_exc())
            else:
                print(f"[WARNING] Status did not change! Still {booking.status}")

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] Error in partial_update: {e}")
            print(error_trace)
            # Return a proper error response instead of letting it bubble up as 500
            return Response(
                {"detail": f"Failed to update booking: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Send email when booking is deleted by admin
    def _send_booking_deleted_email(self, user_email, facility_name, booking_date, start_time, end_time):
        """Send email to homeowner when admin deletes their booking"""
        from django.template.loader import strip_tags
        
        try:
            start_time_str = self.format_time_am_pm(str(start_time))
            end_time_str = self.format_time_am_pm(str(end_time))
            booking_date_str = booking_date.strftime('%B %d, %Y')
            
            subject = f"Booking Cancelled - {facility_name}"
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545;">Booking Cancelled</h2>
                    <p>Dear Homeowner,</p>
                    <p>Your booking has been cancelled by the administrator.</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <p style="margin: 5px 0;"><strong>Facility:</strong> {facility_name}</p>
                        <p style="margin: 5px 0;"><strong>Date:</strong> {booking_date_str}</p>
                        <p style="margin: 5px 0;"><strong>Time:</strong> {start_time_str} - {end_time_str}</p>
                        <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #dc3545; font-weight: bold;">CANCELLED</span></p>
                    </div>
                    <p>If you have any questions or concerns, please contact the administration.</p>
                    <p>You can make a new booking at: <a href="{settings.FRONTEND_URL}/booking-amenities" style="color: #2e6F40;">Book Facility</a></p>
                    <p style="margin-top: 30px;">Thank you,<br><strong>Happy Homes Administration</strong></p>
                </div>
            </body>
            </html>
            """
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=True,
            )
            print(f"[SUCCESS] Deletion email sent to homeowner: {user_email}")
        except Exception as e:
            print(f"[ERROR] Failed to send deletion email: {e}")
            import traceback
            print(traceback.format_exc())
    
    # Send email when booking status changes (approved/rejected)
    def _send_booking_status_change_email(self, booking, old_status):
        """Send email to homeowner when booking status changes"""
        from django.template.loader import strip_tags
        
        # Safely get user email
        user_email = None
        try:
            if hasattr(booking, 'user') and booking.user:
                user_email = getattr(booking.user, 'email', None)
        except (AttributeError, TypeError):
            # If user relationship fails, try to get email from user_id
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(id=booking.user_id)
                user_email = user.email
            except (User.DoesNotExist, AttributeError):
                user_email = None
        
        if not user_email:
            print(f"[WARNING] No email found for booking {booking.id}, skipping email")
            return
        
        try:
            start_time = self.format_time_am_pm(str(booking.start_time))
            end_time = self.format_time_am_pm(str(booking.end_time))
            booking_date = booking.date.strftime('%B %d, %Y')
            
            # Determine status color and message
            if booking.status == 'approved':
                status_color = '#2e6F40'
                status_message = 'APPROVED'
                action_message = 'Your booking request has been approved!'
            elif booking.status == 'rejected':
                status_color = '#dc3545'
                status_message = 'REJECTED'
                action_message = 'Your booking request has been rejected.'
            else:
                status_color = '#f0ad4e'
                status_message = booking.status.upper()
                action_message = f'Your booking status has been changed to {status_message}.'
            
            # Safely get facility name
            facility_name = "Unknown Facility"
            try:
                if hasattr(booking, 'facility') and booking.facility:
                    if hasattr(booking.facility, 'get_name_display'):
                        facility_name = booking.facility.get_name_display()
                    else:
                        facility_name = str(getattr(booking.facility, 'name', 'Unknown Facility'))
            except (AttributeError, TypeError):
                # If facility relationship fails, try to get name from facility_id
                try:
                    facility = Facility.objects.get(id=booking.facility_id)
                    if hasattr(facility, 'get_name_display'):
                        facility_name = facility.get_name_display()
                    else:
                        facility_name = str(getattr(facility, 'name', 'Unknown Facility'))
                except (Facility.DoesNotExist, AttributeError):
                    facility_name = "Unknown Facility"
            
            # Safely get user name
            user_name = "Homeowner"
            try:
                if hasattr(booking, 'user') and booking.user:
                    user_name = booking.user.first_name or booking.user.username or "Homeowner"
            except (AttributeError, TypeError):
                user_name = "Homeowner"
            
            subject = f"Booking {booking.status.capitalize()} - {facility_name}"
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: {status_color};">Booking {status_message}</h2>
                    <p>Dear {user_name},</p>
                    <p>{action_message}</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {status_color};">
                        <p style="margin: 5px 0;"><strong>Facility:</strong> {facility_name}</p>
                        <p style="margin: 5px 0;"><strong>Date:</strong> {booking_date}</p>
                        <p style="margin: 5px 0;"><strong>Time:</strong> {start_time} - {end_time}</p>
                        <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_message}</span></p>
                    </div>
                    <p>You can view your booking status at: <a href="{settings.FRONTEND_URL}/booking-amenities" style="color: #2e6F40;">View My Bookings</a></p>
                    <p style="margin-top: 30px;">Thank you,<br><strong>Happy Homes Administration</strong></p>
                </div>
            </body>
            </html>
            """
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=True,
            )
            print(f"[SUCCESS] Status change email sent to homeowner: {user_email}")
        except Exception as e:
            print(f"[ERROR] Failed to send status change email: {e}")
            import traceback
            print(traceback.format_exc())

# --- Available Slot ViewSet (All users can view, only admins can manage) ---
class AvailableSlotViewSet(viewsets.ModelViewSet):
    serializer_class = AvailableSlotSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # All authenticated users can view

    def get_queryset(self):
        facility_id = self.request.query_params.get("facility_id")
        qs = AvailableSlot.objects.all()
        
        if facility_id:
            qs = qs.filter(facility_id=facility_id)
        
        return qs.order_by("date", "start_time")

    def get_permissions(self):
        """
        Allow all authenticated users to view (GET, LIST),
        but only admins can create, update, or delete.
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

# --- Maintenance ViewSet (All users can view, only admins can manage) ---
class MaintenanceViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # All authenticated users can view

    def get_queryset(self):
        facility_id = self.request.query_params.get("facility_id")
        qs = Maintenance.objects.all()
        
        if facility_id:
            qs = qs.filter(facility_id=facility_id)
        
        return qs.order_by("start_date", "start_time")
    
    def get_permissions(self):
        """
        Allow all authenticated users to view (GET, LIST),
        but only admins can create, update, or delete.
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]
    
    def perform_create(self, serializer):
        """Override to save maintenance and notify all verified users"""
        maintenance = serializer.save()
        
        # Send email notifications to all verified users after successful creation
        # Use try-except to prevent email errors from breaking maintenance creation
        try:
            self._send_maintenance_notification_emails(maintenance)
        except Exception as email_error:
            print(f"[WARNING] Email notification failed (maintenance still created): {email_error}")
            import traceback
            print(traceback.format_exc())
    
    def _send_maintenance_notification_emails(self, maintenance):
        """Send email notifications to all verified users about the maintenance period"""
        from django.template.loader import strip_tags
        
        try:
            # Ensure facility is loaded
            if not hasattr(maintenance, 'facility') or not maintenance.facility:
                print("[ERROR] Maintenance facility not loaded")
                return
            
            # Get facility name
            facility_name = maintenance.facility.get_name_display() if hasattr(maintenance.facility, 'get_name_display') else str(maintenance.facility.name)
            
            # Format dates and times
            start_date_str = maintenance.start_date.strftime('%B %d, %Y')
            end_date_str = maintenance.end_date.strftime('%B %d, %Y')
            
            # Get all verified users (homeowners)
            verified_users = User.objects.filter(
                profile__is_verified=True,
                is_active=True
            ).exclude(email='').exclude(email__isnull=True)
            
            verified_emails = [user.email for user in verified_users if user.email]
            
            if not verified_emails:
                print("[INFO] No verified users with email addresses found")
                return
            
            print(f"[INFO] Sending maintenance notification to {len(verified_emails)} verified user(s)")
            
            # Format time display - if all day, show 12:00 AM to 11:59 PM, otherwise show the specific times
            if maintenance.start_time and maintenance.end_time:
                start_time_str = self._format_time_am_pm(maintenance.start_time)
                end_time_str = self._format_time_am_pm(maintenance.end_time)
                time_display = f"{start_time_str} to {end_time_str}"
            else:
                time_display = "12:00 AM to 11:59 PM"
            
            # Format date - if same start and end date, show single date, otherwise show range
            if maintenance.start_date == maintenance.end_date:
                date_display = start_date_str
            else:
                date_display = f"{start_date_str} to {end_date_str}"
            
            # Create email content matching the sample format
            subject = f"Maintenance Scheduled - {facility_name}"
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <p>Hello,</p>
                    <p>This is to inform you that <strong>{facility_name}</strong> will be under maintenance:</p>
                    <p><strong>Date:</strong> {date_display}</p>
                    <p><strong>Time:</strong> {time_display}</p>
                    <p>Please note that this facility will be unavailable for booking during this period.</p>
                    <p>We apologize for any inconvenience this may cause.</p>
                    <p style="margin-top: 30px;">Thank you,<br><strong>Happy Homes Admin</strong></p>
                </div>
            </body>
            </html>
            """
            plain_message = strip_tags(html_message)
            
            # Send email to all verified users
            try:
                result = send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=verified_emails,
                    html_message=html_message,
                    fail_silently=True,
                )
                print(f"[SUCCESS] ✅ Maintenance notification sent to {len(verified_emails)} verified user(s) (result: {result})")
            except Exception as e:
                print(f"[ERROR] Failed to send maintenance notification emails: {e}")
                import traceback
                print(traceback.format_exc())
        except Exception as e:
            print(f"[ERROR] Error in _send_maintenance_notification_emails: {e}")
            import traceback
            print(traceback.format_exc())
    
    def _format_time_am_pm(self, time_input) -> str:
        """Format time to AM/PM format. Accepts time object or string."""
        try:
            # If it's already a time object, format it directly
            if hasattr(time_input, 'strftime'):
                return time_input.strftime("%I:%M %p")
            
            # If it's a string, try to parse it
            time_str = str(time_input)
            
            # Try different time formats
            for fmt in ["%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"]:
                try:
                    time_obj = datetime.strptime(time_str, fmt)
                    return time_obj.strftime("%I:%M %p")
                except (ValueError, TypeError):
                    continue
            
            # If all parsing fails, return as-is
            return time_str
        except Exception as e:
            print(f"[WARNING] Error formatting time {time_input}: {e}")
            return str(time_input)

# class BookingViewSet(viewsets.ModelViewSet):
#     serializer_class = BookingSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated, IsAdminOrOwner]

#     def get_queryset(self):
#         facility_id = self.request.query_params.get('facility_id')
#         if self.request.user.is_staff:
#             qs = Booking.objects.all()
#         else:
#             qs = Booking.objects.filter(user=self.request.user)

#         if facility_id:
#             qs = qs.filter(facility_id=facility_id)

#         return qs.order_by("date", "start_time")

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all().order_by('-created_at')
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        news = serializer.save()
        # Send email to all users
        recipients = list(User.objects.values_list('email', flat=True))
        send_mail(
            subject=f"📰 New News: {news.title}",
            message=f"{news.content}\n\nView on site.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all().order_by('-created_at')
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        alert = serializer.save()
        # Send email to all users
        recipients = list(User.objects.values_list('email', flat=True))
        send_mail(
            subject=f"🚨 New Alert: {alert.title}",
            message=f"Severity: {alert.severity}\n\n{alert.message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )


class BulletinViewSet(viewsets.ModelViewSet):
    """ViewSet for Bulletin Board - Admin can CRUD, users can read published"""
    serializer_class = BulletinSerializer
    queryset = Bulletin.objects.none()  # Will be set by get_queryset
    
    def get_queryset(self):
        # If user is admin, show all bulletins
        try:
            if self.request.user.is_authenticated and self.request.user.is_staff:
                return Bulletin.objects.all().order_by('-created_at')
        except (AttributeError, TypeError):
            pass
        # Otherwise, only show published bulletins
        return Bulletin.objects.filter(is_published=True).order_by('-created_at')
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def perform_create(self, serializer):
        try:
            if hasattr(self.request, 'user') and self.request.user.is_authenticated:
                serializer.save(created_by=self.request.user)
            else:
                serializer.save()
        except Exception as e:
            import traceback
            print(f"Error in perform_create: {e}")
            print(traceback.format_exc())
            raise

# --- News ---
# class NewsViewSet(viewsets.ModelViewSet):
#     queryset = News.objects.all().order_by('-created_at')
#     serializer_class = NewsSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]


# # --- Alerts ---
# class AlertViewSet(viewsets.ModelViewSet):
#     queryset = Alert.objects.all().order_by('-created_at')
#     serializer_class = AlertSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]


# --- Contact Info (singleton style, first row) ---
class ContactInfoViewSet(viewsets.ModelViewSet):
    queryset = ContactInfo.objects.all()
    serializer_class = ContactInfoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs[:1]


# --- Contact Messages ---
class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]  # Allow public contact form submissions

    def perform_create(self, serializer):
        instance = serializer.save()
        # Send notification email to default admin inbox
        from django.core.mail import send_mail
        subject = f"New contact message: {instance.subject}"
        body = f"From: {instance.name} <{instance.email}>\n\n{instance.message}"
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [getattr(settings, 'CONTACT_INBOX_EMAIL', settings.DEFAULT_FROM_EMAIL)],
            fail_silently=True,
        )


# --- Emergency Contacts ---
class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing emergency contacts
    
    Permissions:
    - GET (list, retrieve): All authenticated users can view active contacts
    - POST/PUT/PATCH/DELETE: Only admins can manage contacts
    """
    queryset = EmergencyContact.objects.all().order_by('order', 'name')
    serializer_class = EmergencyContactSerializer
    authentication_classes = [JWTAuthentication]
    
    def get_permissions(self):
        """Allow read access to all authenticated users, write access only to admins"""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        # For create, update, partial_update, destroy - require admin
        return [IsAdminUser()]
    
    def get_queryset(self):
        """Filter by active status if requested"""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            try:
                is_active_bool = is_active.lower() == 'true'
                queryset = queryset.filter(is_active=is_active_bool)
            except (AttributeError, ValueError):
                # If is_active param is invalid, ignore it
                pass
        return queryset

# --- ViewSets ---
@method_decorator(csrf_exempt, name='dispatch')
class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reviews
    
    Permissions:
    - GET (list, retrieve): Anyone can view reviews (guests, users, admins)
    - POST (create): Only authenticated users can create reviews
    - PUT/PATCH (update): Only the review owner or admin can update
    - DELETE: Only the review owner or admin can delete
    """
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        pin_id = self.request.query_params.get("pin_id")
        qs = Review.objects.all()
        
        if pin_id:
            qs = qs.filter(pin_id=pin_id)
        
        return qs.order_by("-created_at")

    def get_authenticators(self):
        """
        Override authentication to allow unauthenticated access for read operations.
        This allows guests to view reviews without authentication.
        """
        request = getattr(self, 'request', None)
        if request and request.method in ['GET', 'OPTIONS']:
            # No authentication required for viewing reviews
            return []
        # Require authentication for create, update, delete (POST, PUT, PATCH, DELETE)
        return [JWTAuthentication()]

    def perform_create(self, serializer):
        # Ensure user can only create one review per pin
        pin = serializer.validated_data['pin']
        user = self.request.user
        
        # Check if review already exists
        existing_review = Review.objects.filter(pin=pin, user=user).first()
        if existing_review:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You have already reviewed this location. You can update your existing review.")
        
        serializer.save(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class BlogCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Blog Comments
    
    Permissions:
    - GET (list, retrieve): Anyone can view comments (guests, users, admins)
    - POST (create): Only authenticated users (users and admins) can create comments
    - PUT/PATCH (update): Only the comment owner or admin can update
    - DELETE: Only the comment owner or admin can delete
    """
    serializer_class = BlogCommentSerializer
    authentication_classes = [JWTAuthentication]
    # Allow read access to everyone, but require authentication for write operations
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Filter comments by post_id if provided in query params
        Example: /api/blog-comments/?post_id=1
        """
        post_id = self.request.query_params.get("post_id")
        qs = BlogComment.objects.all()
        
        if post_id:
            qs = qs.filter(post_id=post_id)
        
        return qs.order_by("-created_at")  # Newest comments first

    def get_authenticators(self):
        """
        Override authentication to allow unauthenticated access for read operations.
        This allows guests to view comments without authentication.
        """
        # Check request method - GET requests don't need authentication
        # Use getattr to safely access request in case it's not initialized yet
        request = getattr(self, 'request', None)
        if request and request.method in ['GET', 'OPTIONS']:
            # No authentication required for viewing comments
            return []
        # Require authentication for create, update, delete (POST, PUT, PATCH, DELETE)
        return [JWTAuthentication()]

    def get_serializer_context(self):
        """Pass request context to serializer for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """
        Automatically set the user to the current authenticated user when creating a comment
        """
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Override create to provide better error messages
        """
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            # Return a more user-friendly error message
            return Response(
                {'detail': f'Error creating comment: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_permissions(self):
        """
        Override permissions for different actions:
        - list, retrieve: AllowAny (anyone can view)
        - create: IsAuthenticated (only authenticated users can comment)
        - update, destroy: IsAuthenticated + check if owner or admin
        """
        if self.action in ['list', 'retrieve']:
            # Anyone can view comments (guests, users, admins)
            permission_classes = [AllowAny]
        elif self.action == 'create':
            # Only authenticated users can create comments
            permission_classes = [IsAuthenticated]
        else:
            # For update/delete, use default IsAuthenticatedOrReadOnly
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        """
        Only allow the comment owner or admin to update
        """
        comment = self.get_object()
        
        # Check if user is the owner or admin
        if comment.user != request.user and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own comments.")
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Only allow the comment owner or admin to delete
        """
        comment = self.get_object()
        
        # Check if user is the owner or admin
        if comment.user != request.user and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own comments.")
        
        return super().destroy(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class BulletinCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Bulletin Comments
    
    Permissions:
    - GET (list, retrieve): Only authenticated users can view comments (for verified homeowners and admins)
    - POST (create): Only authenticated and verified users or admins can create comments
    - PUT/PATCH (update): Only the comment owner or admin can update
    - DELETE: Only the comment owner or admin can delete
    """
    serializer_class = BulletinCommentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter comments by bulletin_id if provided in query params
        Example: /api/bulletin-comments/?bulletin_id=1
        Only show comments from verified users to admins, or all comments if admin
        """
        bulletin_id = self.request.query_params.get("bulletin_id")
        qs = BulletinComment.objects.all()
        
        if bulletin_id:
            qs = qs.filter(bulletin_id=bulletin_id)
        
        # If user is admin, show all comments
        # Otherwise, only show comments from verified users
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(user__profile__is_verified=True)
        
        return qs.order_by("-created_at")  # Newest comments first

    def perform_create(self, serializer):
        """
        Automatically set the user to the current authenticated user when creating a comment
        Only verified users or admins can comment
        """
        user = self.request.user
        
        # Check if user is verified or admin
        is_verified = hasattr(user, 'profile') and user.profile.is_verified
        if not (is_verified or user.is_staff):
            raise PermissionDenied("Only verified homeowners and admins can comment on bulletins.")
        
        serializer.save(user=user)
    
    def create(self, request, *args, **kwargs):
        """
        Override create to provide better error messages
        """
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            # Return a more user-friendly error message
            return Response(
                {'detail': f'Error creating comment: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_permissions(self):
        """
        Override permissions for different actions:
        - list, retrieve: IsAuthenticated (only authenticated users can view)
        - create: IsAuthenticated + check if verified or admin
        - update, destroy: IsAuthenticated + check if owner or admin
        """
        if self.action in ['list', 'retrieve']:
            # Only authenticated users can view comments
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            # Only authenticated users can create comments (verified check in perform_create)
            permission_classes = [IsAuthenticated]
        else:
            # For update/delete, use IsAuthenticated
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def update(self, request, *args, **kwargs):
        """
        Override update to check if user is owner or admin
        """
        instance = self.get_object()
        
        # Allow update if user is admin or the comment owner
        if request.user.is_staff or instance.user == request.user:
            return super().update(request, *args, **kwargs)
        
        return Response(
            {'detail': 'You do not have permission to perform this action.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to check if user is owner or admin
        """
        instance = self.get_object()
        
        # Allow deletion if user is admin or the comment owner
        if request.user.is_staff or instance.user == request.user:
            return super().destroy(request, *args, **kwargs)
        
        return Response(
            {'detail': 'You do not have permission to perform this action.'},
            status=status.HTTP_403_FORBIDDEN
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CommunityMediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Community Media Gallery
    
    Permissions:
    - GET (list, retrieve): Anyone can view public media (guests, users, admins)
    - POST (create): Only authenticated users can create (admins auto-approved, users need approval)
    - PUT/PATCH (update): Only admin can update
    - DELETE: Only admin can delete
    """
    serializer_class = CommunityMediaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Filter media by category, featured status, or public visibility
        Query params:
        - category: Filter by category (events, facilities, properties, activities, announcements)
        - featured: Filter only featured items (true/false)
        - is_public: Filter public items (true/false, default: true for guests)
        """
        qs = CommunityMedia.objects.all()
        
        # If not authenticated or not admin, only show approved and public media
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(is_approved=True, is_public=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        
        # Filter by featured
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            qs = qs.filter(is_featured=True)
        
        # Filter by public (for admin)
        if self.request.user.is_authenticated and self.request.user.is_staff:
            is_public = self.request.query_params.get('is_public')
            if is_public:
                qs = qs.filter(is_public=(is_public.lower() == 'true'))
        
        return qs.order_by('-order', '-created_at')

    def get_authenticators(self):
        """Allow unauthenticated access for viewing media"""
        request = getattr(self, 'request', None)
        if request and request.method in ['GET', 'OPTIONS']:
            return []
        return [JWTAuthentication()]

    def get_serializer_context(self):
        """Pass request context to serializer for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        """Set uploaded_by to current user, auto-approve if admin"""
        user = self.request.user
        is_admin = user.is_staff
        
        serializer.save(
            uploaded_by=user,
            is_approved=is_admin,  # Auto-approve admin uploads
            approved_by=user if is_admin else None
        )

    def get_permissions(self):
        """Override permissions - allow anyone to view, require auth for write"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated]
        else:
            # Update/Delete only for admins
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        """Only admin can update media"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only administrators can update media.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If approving media, set approved_by
        instance = self.get_object()
        if 'is_approved' in request.data and request.data['is_approved']:
            request.data['approved_by'] = request.user.id
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Only admin can delete media"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only administrators can delete media.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increment view count (public action)"""
        media = self.get_object()
        media.views_count += 1
        media.save(update_fields=['views_count'])
        return Response({'views_count': media.views_count})


class PinViewSet(ModelViewSet):
    queryset = Pin.objects.all()
    serializer_class = PinSerializer
    # Temporarily allow open write access to unblock pinning; tighten later
    permission_classes = [AllowAny]
    authentication_classes = []

    def perform_create(self, serializer):
        # Ensure optional fields are saved from incoming payload
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


@method_decorator(csrf_exempt, name='dispatch')
class SubdivisionViewSet(ModelViewSet):
    queryset = Subdivision.objects.all()
    serializer_class = SubdivisionSerializer
    permission_classes = [AllowAny]
    authentication_classes = [BasicAuthentication]

    @action(detail=False, methods=['get'])
    def occupancy_stats(self, request):
        """Get real-time subdivision occupancy statistics based on pins"""
        # Get all pins
        all_pins = Pin.objects.all()
        total_pins = all_pins.count()
        
        # Count occupied pins (prefer status, fallback to legacy name marker)
        occupied_pins = all_pins.filter(
            Q(status__iexact='occupied') |
            Q(name__iregex=r'(^|\b)occupied($|\b)')
        ).count()
        available_pins = max(total_pins - occupied_pins, 0)
        
        # Use fixed capacity of 200 slots for subdivision capacity
        capacity = 200
        max_subdivisions = capacity
        total_subdivisions = capacity
        occupied_subdivisions = occupied_pins
        available_subdivisions = max(total_subdivisions - occupied_subdivisions, 0)
        
        return Response({
            'total': total_subdivisions,
            'occupied': occupied_subdivisions,
            'available': available_subdivisions,
            'occupancy_rate': (occupied_subdivisions / total_subdivisions * 100) if total_subdivisions > 0 else 0,
            'total_pins': total_pins,
            'occupied_pins': occupied_pins,
            'available_pins': available_pins
        })

    @action(detail=False, methods=['get'])
    def real_time_data(self, request):
        """Get real-time data for map including pins and occupancy"""
        # Get all pins
        pins = Pin.objects.all()
        pin_serializer = PinSerializer(pins, many=True)
        
        # Calculate occupancy stats based on pins
        total_pins = pins.count()
        occupied_pins = pins.filter(
            Q(status__iexact='occupied') |
            Q(name__iregex=r'(^|\b)occupied($|\b)')
        ).count()
        available_pins = max(total_pins - occupied_pins, 0)
        
        # Use fixed capacity of 200 slots for subdivision capacity
        capacity = 200
        max_subdivisions = capacity
        total_subdivisions = capacity
        occupied_subdivisions = occupied_pins
        available_subdivisions = max(total_subdivisions - occupied_subdivisions, 0)
        
        return Response({
            'pins': pin_serializer.data,
            'occupancy': {
                'total': total_subdivisions,
                'occupied': occupied_subdivisions,
                'available': available_subdivisions,
                'occupancy_rate': (occupied_subdivisions / total_subdivisions * 100) if total_subdivisions > 0 else 0,
                'total_pins': total_pins,
                'occupied_pins': occupied_pins,
                'available_pins': available_pins
            },
            'timestamp': timezone.now().isoformat()
        })


# --- reCAPTCHA ---
@csrf_exempt
def verify_recaptcha(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        recaptcha_token = data.get('recaptcha')

        if not recaptcha_token:
            return JsonResponse({'message': 'reCAPTCHA token missing'}, status=400)

        secret_key = settings.RECAPTCHA_SECRET_KEY
        payload = {'secret': secret_key, 'response': recaptcha_token}
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
        result = response.json()

        if not result.get('success'):
            return JsonResponse({'message': 'reCAPTCHA verification failed'}, status=400)

        # Example login check (replace with your own logic)
        username = data.get('username')
        password = data.get('password')
        if username == 'test' and password == 'password':
            return JsonResponse({'access': 'fake-jwt-token'}, status=200)

        return JsonResponse({'message': 'Invalid username or password'}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_verification_document(request):
    profile = request.user.profile
    file = request.FILES.get('document')
    if not file:
        return Response({"error": "No document uploaded"}, status=400)

    profile.document = file
    profile.is_verified = False  # Set to False initially; admin will verify later
    profile.save()
    return Response({"message": "Document uploaded successfully!"})

from .models import ResidentPin, Visitor
from .serializers import ResidentPinSerializer, VisitorSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.http import HttpResponse

# ✅ Resident PIN (GET/POST)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def my_resident_pin(request):
    user = request.user
    pin_obj, _ = ResidentPin.objects.get_or_create(user=user)

    if request.method == "POST":
        pin_obj.generate_pin()

    serializer = ResidentPinSerializer(pin_obj)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def visitor_checkin(request):
    serializer = VisitorSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def guest_visitor_checkin(request):
    name = request.data.get('name')
    gmail = request.data.get('gmail')
    contact_number = request.data.get('contact_number', None)
    pin = request.data.get('pin')
    reason = request.data.get('reason', '')

    # Validate required fields
    if not name or not gmail or not pin:
        return Response({"error": "Missing name, gmail, or resident PIN"}, status=400)

    try:
        resident = ResidentPin.objects.get(pin=pin)
    except ResidentPin.DoesNotExist:
        return Response({"error": "Invalid resident PIN"}, status=404)

    visitor = Visitor.objects.create(
        name=name,
        gmail=gmail,
        contact_number=contact_number,  # Optional
        reason=reason,
        resident=resident,
        status='pending'
    )

    # ✅ Send Gmail notification to resident
    if resident.user.email:
        send_mail(
            subject="🆕 New Visitor Check-In Pending Approval",
            message=(
                f"Hello {resident.user.username},\n\n"
                f"A new visitor has submitted a check-in request.\n"
                f"Details:\n"
                f"Name: {name}\n"
                f"Gmail: {gmail}\n"
                f"Contact: {contact_number or '-'}\n"
                # f"Reason: {reason or '-'}\n\n"
                f"Please approve or decline this visitor in the dashboard."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[resident.user.email],
            fail_silently=True,
        )

    serializer = VisitorSerializer(visitor)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def guest_visitor_checkin(request):
#     name = request.data.get('name')
#     gmail = request.data.get('gmail')
#     contact_number = request.data.get('contact_number', None)
#     pin = request.data.get('pin')
#     reason = request.data.get('reason', '')

#     if not name or not gmail or not pin:
#         return Response({"error": "Missing name, gmail, or resident PIN"}, status=400)

#     try:
#         resident = ResidentPin.objects.get(pin=pin)
#     except ResidentPin.DoesNotExist:
#         return Response({"error": "Invalid resident PIN"}, status=404)

#     visitor = Visitor.objects.create(
#         name=name,
#         gmail=gmail,
#         contact_number=contact_number,
#         reason=reason,
#         resident=resident,
#         status='pending'
#     )
#     serializer = VisitorSerializer(visitor)
#     return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def visitor_approval(request, visitor_id):
    approve = request.data.get("approve", False)

    try:
        visitor = Visitor.objects.get(id=visitor_id)
    except Visitor.DoesNotExist:
        return Response({"error": "Visitor not found"}, status=404)

    visitor.status = "approved" if approve else "declined"
    if approve:
        visitor.time_in = timezone.now()
    visitor.save()

    # ✅ Notify resident
    if visitor.resident.user.email:
        send_mail(
            subject="✅ Visitor Approved" if approve else "❌ Visitor Declined",
            message=(
                f"Visitor {visitor.name} has been {'approved' if approve else 'declined'} "
                f"by {visitor.resident.user.username}."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[visitor.resident.user.email],
            fail_silently=True,
        )

    # ✅ Notify visitor if approved
    if approve and visitor.gmail:
        send_mail(
            subject="✅ Your Visitor Check-In Has Been Approved",
            message=(
                f"Hello {visitor.name},\n\n"
                f"Your visitor check-in has been approved by {visitor.resident.user.username}.\n"
                f"Details:\n"
                f"Name: {visitor.name}\n"
                f"Gmail: {visitor.gmail}\n"
                f"Contact: {visitor.contact_number or '-'}\n"
                f"Reason: {visitor.reason or '-'}\n\n"
                f"Time In: {visitor.time_in}\n"
                f"Enjoy your visit!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[visitor.gmail],
            fail_silently=True,
        )

    serializer = VisitorSerializer(visitor)
    return Response(serializer.data)


# ✅ Visitor check-out
@api_view(['POST'])
@permission_classes([AllowAny])
def visitor_checkout(request, visitor_id):
    try:
        visitor = Visitor.objects.get(id=visitor_id)
    except Visitor.DoesNotExist:
        return Response({"error": "Visitor not found"}, status=404)

    if visitor.status != "approved":
        return Response({"error": "Cannot check out unapproved visitor"}, status=400)

    visitor.time_out = timezone.now()
    visitor.save()

    # Notify resident
    if visitor.resident and visitor.resident.user.email:
        send_mail(
            subject="🚪 Visitor Checked Out",
            message=f"Visitor {visitor.name} has checked out successfully.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[visitor.resident.user.email],
            fail_silently=True,
        )

    # Notify visitor
    if visitor.gmail:
        send_mail(
            subject="You Checked Out",
            message=f"Hello {visitor.name}, you have successfully checked out.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[visitor.gmail],
            fail_silently=True,
        )

    serializer = VisitorSerializer(visitor)
    return Response(serializer.data)
# ✅ Visitor approval (resident)
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def visitor_approval(request, visitor_id):
#     approve = request.data.get("approve", False)

#     try:
#         visitor = Visitor.objects.get(id=visitor_id)
#     except Visitor.DoesNotExist:
#         return Response({"error": "Visitor not found"}, status=404)

#     visitor.status = "approved" if approve else "declined"
#     if approve:
#         visitor.time_in = timezone.now()
#     visitor.save()

#     # ✅ Send Gmail notification to resident
#     if visitor.resident.user.email:
#         send_mail(
#             subject="✅ Visitor Approved" if approve else "❌ Visitor Declined",
#             message=(
#                 f"Visitor {visitor.name} has been {'approved' if approve else 'declined'} "
#                 f"by {visitor.resident.user.username}."
#             ),
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[visitor.resident.user.email],
#             fail_silently=True,
#         )

#     serializer = VisitorSerializer(visitor)
#     return Response(serializer.data)


# ✅ Visitor check-out
@api_view(['POST'])
@permission_classes([AllowAny])
def visitor_checkout(request, visitor_id):
    try:
        visitor = Visitor.objects.get(id=visitor_id)
    except Visitor.DoesNotExist:
        return Response({"error": "Visitor not found"}, status=404)

    if visitor.status != "approved":
        return Response({"error": "Cannot check out unapproved visitor"}, status=400)

    visitor.time_out = timezone.now()
    visitor.save()

    # ✅ Send Gmail notification to resident
    if visitor.resident.user.email:
        send_mail(
            subject="🚪 Visitor Checked Out",
            message=f"Visitor {visitor.name} has checked out successfully.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[visitor.resident.user.email],
            fail_silently=True,
        )

    serializer = VisitorSerializer(visitor)
    return Response(serializer.data)


# ✅ Active visitors
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_visitors(request):
    visitors = Visitor.objects.filter(
        resident__user=request.user,
        time_out__isnull=True,
        status="approved"
    )
    serializer = VisitorSerializer(visitors, many=True)
    return Response(serializer.data)


# ✅ Pending visitors
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_visitors(request):
    visitors = Visitor.objects.filter(
        resident__user=request.user,
        status="pending"
    )
    serializer = VisitorSerializer(visitors, many=True)
    return Response(serializer.data)


class VisitorViewSet(viewsets.ModelViewSet):
    serializer_class = VisitorSerializer

    def get_queryset(self):
        """
        Return visitors for the logged-in resident.
        Guests (anonymous) will use direct PK lookup in time_in/time_out.
        """
        user = self.request.user
        if user.is_authenticated:
            return Visitor.objects.filter(resident__user=user).order_by('-time_in')
        # For anonymous users, allow all visitors (used only in time_in/time_out)
        return Visitor.objects.all()

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        visitor = self.get_object()
        visitor.status = "approved"
        visitor.time_in = now()
        visitor.save()
        return Response({"message": "Visitor approved."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def decline(self, request, pk=None):
        visitor = self.get_object()
        visitor.status = "declined"
        visitor.time_out = now()
        visitor.save()
        return Response({"message": "Visitor declined."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], permission_classes=[AllowAny], url_path='time-in')
    def time_in(self, request, pk=None):
        """
        Update visitor time-in. Allows guests to check in using visitor ID.
        """
        visitor = Visitor.objects.get(pk=pk)  # Direct lookup, bypass user filter
        visitor.time_in = now()
        visitor.save()
        return Response({"time_in": visitor.time_in}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], permission_classes=[AllowAny], url_path='time-out')
    def time_out(self, request, pk=None):
        """
        Update visitor time-out. Allows guests to check out using visitor ID.
        """
        visitor = Visitor.objects.get(pk=pk)  # Direct lookup
        visitor.time_out = now()
        visitor.save()
        return Response({"time_out": visitor.time_out}, status=status.HTTP_200_OK)
# ✅ Optional ModelViewSets
# class VisitorViewSet(viewsets.ModelViewSet):
#     queryset = Visitor.objects.all().order_by('-time_in')
#     serializer_class = VisitorSerializer

#     def get_permissions(self):
#         if self.action in ['create', 'check_status']:
#             return [AllowAny()]
#         return [IsAuthenticated()]

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         gmail = self.request.query_params.get("gmail")
#         if gmail:
#             queryset = queryset.filter(gmail=gmail)
#         return queryset

#     def create(self, request):
#         """Visitor check-in (public)"""
#         name = request.data.get("name")
#         email = request.data.get("email")
#         pin_entered = request.data.get("pin")

#         try:
#             resident_pin = ResidentPin.objects.get(pin=pin_entered)
#         except ResidentPin.DoesNotExist:
#             return Response({"error": "Invalid PIN"}, status=400)

#         visitor = Visitor.objects.create(
#             name=name,
#             email=email,
#             resident=resident_pin.user,
#             pin=pin_entered,
#             status="PENDING"
#         )

#         serializer = VisitorSerializer(visitor)
#         return Response(serializer.data, status=201)

#     @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
#     def approve(self, request, pk=None):
#         """Resident approves visitor"""
#         visitor = self.get_object()
#         visitor.status = "APPROVED"
#         visitor.time_in = timezone.now()
#         visitor.save()
#         visitor.notify_status_change()  # ✅ send Gmail
#         return Response({"message": "Visitor approved and notified."})

#     @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
#     def decline(self, request, pk=None):
#         """Resident declines visitor"""
#         visitor = self.get_object()
#         visitor.status = "DECLINED"
#         visitor.save()
#         visitor.notify_status_change()  # ✅ send Gmail
#         return Response({"message": "Visitor declined and notified."})

#     @action(detail=False, methods=["post"], permission_classes=[AllowAny])
#     def check_status(self, request):
#         """Visitors can check their status using email + PIN"""
#         email = request.data.get("email")
#         pin = request.data.get("pin")

#         visitor = Visitor.objects.filter(email=email, pin=pin).order_by('-time_in').first()
#         if not visitor:
#             return Response({"status": "Not found"}, status=404)
#         return Response({"status": visitor.status})


class ResidentPinViewSet(viewsets.ModelViewSet):
    queryset = ResidentPin.objects.all()
    serializer_class = ResidentPinSerializer
    permission_classes = [IsAuthenticated]

class ResidentApprovalViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]

    def update(self, request, *args, **kwargs):
        """Allow admin to approve or decline a resident."""
        profile = self.get_object()
        is_verified = request.data.get('is_verified', None)

        if is_verified is not None:
            profile.is_verified = is_verified
            profile.save()
            return Response({
                "message": f"Resident {'approved ✅' if is_verified else 'declined ❌'} successfully."
            }, status=status.HTTP_200_OK)

        return Response({"error": "is_verified field required"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_visitors(request):
    visitors = Visitor.objects.filter(resident__user=request.user)
    serializer = VisitorSerializer(visitors, many=True)
    return Response(serializer.data)


class VisitorListView(generics.ListAPIView):
    serializer_class = VisitorSerializer

    def get_queryset(self):
        gmail = self.request.query_params.get("gmail")
        if gmail:
            return Visitor.objects.filter(gmail=gmail)
        return Visitor.objects.all()

def guest_visitors(request):
    email = request.query_params.get('email')
    visitors = Visitor.objects.filter(email=email)
    serializer = VisitorSerializer(visitors, many=True)
    return Response(serializer.data)

class VisitorCheckinView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VisitorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(status="pending")  # set status server-side
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def visitor_status(request):
    name = request.GET.get('name')
    gmail = request.GET.get('gmail')
    pin = request.GET.get('pin')

    if not all([name, gmail, pin]):
        return Response({"error": "Missing parameters"}, status=400)

    visitors = Visitor.objects.filter(
        name=name,
        gmail=gmail,
        resident__pin=pin
    )
    serializer = VisitorSerializer(visitors, many=True)
    return Response(serializer.data)


# Guest visitor status check
@api_view(['GET'])
@permission_classes([AllowAny])
def guest_visitor_status(request):
    name = request.GET.get('name')
    gmail = request.GET.get('gmail')
    pin = request.GET.get('pin')

    if not name or not gmail or not pin:
        return Response({"error": "Missing name, gmail, or resident PIN"}, status=400)

    try:
        resident = ResidentPin.objects.get(pin=pin)
    except ResidentPin.DoesNotExist:
        return Response({"error": "Invalid resident PIN"}, status=404)

    visitors = Visitor.objects.filter(resident=resident, name=name, gmail=gmail)
    serializer = VisitorSerializer(visitors, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resident_visitors(request):
    """
    Returns all visitor requests for the logged-in resident.
    """
    user = request.user
    # Assuming Resident PIN is linked to user
    visitor_requests = Visitor.objects.filter(resident__user=user)
    serializer = VisitorSerializer(visitor_requests, many=True)
    return Response(serializer.data)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def visitor_timeout(request, pk):
    try:
        visitor = Visitor.objects.get(id=pk)
        visitor.time_out = timezone.now()
        visitor.save()
        return Response({"detail": "Time out updated."})
    except Visitor.DoesNotExist:
        return Response({"detail": "Visitor not found."}, status=404)

from django.utils.timezone import now

class VisitorTrackingViewSet(viewsets.ModelViewSet):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Return all visitors, including those without time_in (approved but not checked in yet)
        Order by time_in (most recent first), then by id for those without time_in
        """
        return Visitor.objects.all().order_by('-time_in', '-id')

    def create(self, request, *args, **kwargs):
        """Override create to automatically set time_in when status is 'approved'"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # If status is approved, set time_in to current time
        if serializer.validated_data.get('status') == 'approved':
            serializer.validated_data['time_in'] = now()
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """Override update to automatically set time_in when status changes to 'approved'"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # If status is being changed to 'approved' and time_in is not already set
        new_status = serializer.validated_data.get('status')
        if new_status == 'approved' and not instance.time_in:
            serializer.validated_data['time_in'] = now()
        
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def approve(self, request, pk=None):
        visitor = self.get_object()
        visitor.status = "approved"
        visitor.time_in = now()
        visitor.save()
        return Response({"message": "Visitor approved."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    def decline(self, request, pk=None):
        visitor = self.get_object()
        visitor.status = "declined"
        visitor.time_out = now()
        visitor.save()
        return Response({"message": "Visitor declined."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    def timeout(self, request, pk=None):
        visitor = self.get_object()
        visitor.time_out = now()  # ✅ Make sure now() is imported
        visitor.save()
        return Response({"message": "Visitor time-out recorded."}, status=status.HTTP_200_OK)

from .models import House
from .serializers import HouseSerializer   
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

class HouseListCreateView(generics.ListCreateAPIView):
    queryset = House.objects.all().order_by("-created_at")
    serializer_class = HouseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    # CRITICAL: Add parser classes to handle multipart/form-data (file uploads)
    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _handle_images(self, house, request):
        """Handle multiple image uploads for a house - same as HouseViewSet"""
        from .models import HouseImage
        
        try:
            # Ensure house is saved before creating images
            if not house.pk:
                house.save()
                print(f"[HouseListCreateView] Saved house first to get PK: {house.pk}")
            
            # Get images from request.FILES (FormData sends files here)
            images = []
            if hasattr(request, 'FILES') and request.FILES:
                # Try to get images with key 'images'
                images = request.FILES.getlist('images')
                print(f"[HouseListCreateView] Received {len(images)} image(s) from request.FILES.getlist('images')")
                
                # If no images found, check all FILES keys for debugging
                if not images:
                    print(f"[HouseListCreateView] No images found with key 'images'. Available keys: {list(request.FILES.keys())}")
                    for key in request.FILES.keys():
                        files = request.FILES.getlist(key)
                        print(f"[HouseListCreateView] Key '{key}': {len(files)} file(s)")
                        if files:
                            print(f"[HouseListCreateView] Found {len(files)} file(s) with key '{key}'")
            else:
                print(f"[HouseListCreateView] ⚠️ WARNING: request.FILES is empty or doesn't exist!")
            
            if images:
                # Get current count for ordering
                current_count = house.images.count() if house.pk else 0
                print(f"[HouseListCreateView] Current image count: {current_count}, adding {len(images)} new image(s)")
                
                # Create HouseImage instances for each uploaded image
                created_images = []
                for index, image_file in enumerate(images):
                    try:
                        # Ensure house is saved before creating image
                        if not house.pk:
                            house.save()
                            print(f"[HouseListCreateView] Saved house to get PK: {house.pk}")
                        
                        house_image = HouseImage.objects.create(
                            house=house,
                            image=image_file,
                            order=current_count + index
                        )
                        created_images.append(house_image.id)
                        print(f"[HouseListCreateView] ✅ Created HouseImage {current_count + index} (ID: {house_image.id}) for house {house.id}")
                        
                        # Verify the image was saved
                        if house_image.image:
                            print(f"[HouseListCreateView] HouseImage {house_image.id} has image: {house_image.image.name}")
                        else:
                            print(f"[HouseListCreateView] ⚠️ WARNING: HouseImage {house_image.id} has no image file!")
                            
                    except Exception as e:
                        print(f"[HouseListCreateView] ❌ ERROR: Failed to create HouseImage {index}: {e}")
                        import traceback
                        print(traceback.format_exc())
                        # Continue with other images even if one fails
                
                print(f"[HouseListCreateView] ✅ Successfully created {len(created_images)}/{len(images)} images")
                return len(created_images)
            else:
                print(f"[HouseListCreateView] ⚠️ WARNING: No images to process for house {house.pk}")
                return 0
        except Exception as e:
            print(f"[HouseListCreateView] ❌ ERROR: Error in _handle_images: {e}")
            import traceback
            print(traceback.format_exc())
            # Don't raise - let the house creation succeed even if images fail
            return 0

    def perform_create(self, serializer):
        house = serializer.save(user=self.request.user)
        print(f"[HouseListCreateView] House saved with PK: {house.pk}")
        
        # Handle images
        images_created = self._handle_images(house, self.request)
        print(f"[HouseListCreateView] Created {images_created} image(s) for house {house.pk}")
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        """Override create to ensure images are included in response"""
        print(f"[HouseListCreateView] ========== CREATING HOUSE ==========")
        print(f"[HouseListCreateView] Request method: {request.method}")
        print(f"[HouseListCreateView] Request.FILES exists: {hasattr(request, 'FILES')}")
        print(f"[HouseListCreateView] Request.FILES keys: {list(request.FILES.keys()) if request.FILES else 'None'}")
        
        # Call parent create which will call perform_create (which handles images)
        response = super().create(request, *args, **kwargs)
        
        # Reload house with images for proper serialization
        house_id = response.data.get('id')
        if house_id:
            from django.db.models import Prefetch
            from .models import HouseImage
            house = House.objects.prefetch_related(
                Prefetch('images', queryset=HouseImage.objects.all().order_by('order', 'created_at'))
            ).select_related('user').get(pk=house_id)
            
            # Re-serialize with images
            serializer = self.get_serializer(house, context={'request': request})
            response.data.update(serializer.data)
            
            print(f"[HouseListCreateView] ✅ House {house_id} created with {house.images.count()} images")
        
        print(f"[HouseListCreateView] ====================================")
        return response


class HouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = House.objects.all()
    serializer_class = HouseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def _handle_images(self, house, request):
        """Handle multiple image uploads for a house"""
        from .models import HouseImage
        
        # Get images from request
        images = request.FILES.getlist('images')
        
        if images:
            # Create HouseImage instances for each uploaded image
            for index, image_file in enumerate(images):
                HouseImage.objects.create(
                    house=house,
                    image=image_file,
                    order=house.images.count() + index
                )

    def perform_update(self, serializer):
        # Prevent switching owners
        house = serializer.save(user=self.request.user)
        # Handle multiple images (new images will be added)
        self._handle_images(house, self.request)


class HouseViewSet(viewsets.ModelViewSet):
    serializer_class = HouseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    # CRITICAL: Add parser classes to handle multipart/form-data (file uploads)
    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        from django.db.models import Prefetch
        base_queryset = House.objects.prefetch_related(
            Prefetch('images', queryset=HouseImage.objects.all().order_by('order', 'created_at'))
        ).select_related('user')
        if user.is_staff:
            return base_queryset.all().order_by('-created_at')
        return base_queryset.filter(user=user).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        """Override list to ensure images are included"""
        response = super().list(request, *args, **kwargs)
        # Response data is already serialized with images due to prefetch_related
        return response

    def _handle_images(self, house, request):
        """Handle multiple image uploads for a house"""
        from .models import HouseImage
        
        try:
            # Ensure house is saved before creating images
            if not house.pk:
                house.save()
                print(f"[INFO] Saved house first to get PK: {house.pk}")
            
            # Get images from request.FILES (FormData sends files here)
            images = []
            if hasattr(request, 'FILES') and request.FILES:
                # Try to get images with key 'images'
                images = request.FILES.getlist('images')
                print(f"[INFO] Received {len(images)} image(s) from request.FILES.getlist('images')")
                
                # If no images found, check all FILES keys for debugging
                if not images:
                    print(f"[DEBUG] No images found with key 'images'. Available keys: {list(request.FILES.keys())}")
                    for key in request.FILES.keys():
                        files = request.FILES.getlist(key)
                        print(f"[DEBUG] Key '{key}': {len(files)} file(s)")
                        # If we find files with a different key, log it
                        if files:
                            print(f"[DEBUG] Found {len(files)} file(s) with key '{key}'")
            else:
                print(f"[WARNING] request.FILES is empty or doesn't exist")
            
            if images:
                # Get current count for ordering
                current_count = house.images.count() if house.pk else 0
                print(f"[INFO] Current image count: {current_count}, adding {len(images)} new image(s)")
                
                # Create HouseImage instances for each uploaded image
                created_images = []
                for index, image_file in enumerate(images):
                    try:
                        # Validate file is actually an image
                        if not hasattr(image_file, 'content_type'):
                            print(f"[WARNING] Image {index} has no content_type")
                        
                        # Ensure house is saved before creating image
                        if not house.pk:
                            house.save()
                            print(f"[INFO] Saved house to get PK: {house.pk}")
                        
                        house_image = HouseImage.objects.create(
                            house=house,
                            image=image_file,
                            order=current_count + index
                        )
                        created_images.append(house_image.id)
                        print(f"[SUCCESS] Created HouseImage {current_count + index} (ID: {house_image.id}) for house {house.id}")
                        
                        # Verify the image was saved
                        if house_image.image:
                            print(f"[INFO] HouseImage {house_image.id} has image: {house_image.image.name}")
                        else:
                            print(f"[WARNING] HouseImage {house_image.id} has no image file!")
                            
                    except Exception as e:
                        print(f"[ERROR] Failed to create HouseImage {index}: {e}")
                        import traceback
                        print(traceback.format_exc())
                        # Continue with other images even if one fails
                
                # Force database commit and verify
                if house.pk:
                    from django.db import transaction
                    from django.db import connection
                    
                    # Commit transaction to ensure images are saved
                    transaction.commit()
                    
                    # Clear any cached queries
                    connection.queries_log.clear()
                    
                    # Verify images are in database with a fresh query
                    db_count = HouseImage.objects.filter(house_id=house.pk).count()
                    print(f"[IMAGES] Verified: {db_count} images in database for house {house.pk}")
                    
                    # Verify each image file exists
                    for img_id in created_images:
                        try:
                            img = HouseImage.objects.get(id=img_id)
                            if img.image:
                                import os
                                from django.conf import settings
                                file_path = os.path.join(settings.MEDIA_ROOT, img.image.name)
                                if os.path.exists(file_path):
                                    print(f"[IMAGES] ✅ Image {img_id} file exists: {img.image.name}")
                                else:
                                    print(f"[IMAGES] ❌ Image {img_id} file NOT found: {file_path}")
                        except Exception as e:
                            print(f"[IMAGES] ❌ Error verifying image {img_id}: {e}")
                    
                    # Force reload relationship by clearing cache
                    if hasattr(house, '_prefetched_objects_cache'):
                        house._prefetched_objects_cache.clear()
                    
                    # Force reload
                    _ = list(house.images.all())
                    print(f"[IMAGES] Relationship loaded: {len(_)} images accessible")
                
                print(f"[IMAGES] ✅ Successfully created {len(created_images)}/{len(images)} images")
                return len(created_images)
            else:
                print(f"[WARNING] No images to process for house {house.pk}")
                return 0
        except Exception as e:
            print(f"[ERROR] Error in _handle_images: {e}")
            import traceback
            print(traceback.format_exc())
            # Don't raise - let the house creation succeed even if images fail
            return 0

    def create(self, request, *args, **kwargs):
        """Override create to ensure images are included in response"""
        print(f"[CREATE] ========== CREATING HOUSE ==========")
        print(f"[CREATE] Request method: {request.method}")
        print(f"[CREATE] Request content_type: {getattr(request, 'content_type', 'N/A')}")
        print(f"[CREATE] Request.META CONTENT_TYPE: {request.META.get('CONTENT_TYPE', 'N/A')}")
        print(f"[CREATE] request.FILES exists: {hasattr(request, 'FILES')}")
        print(f"[CREATE] request.FILES type: {type(request.FILES)}")
        print(f"[CREATE] request.FILES keys: {list(request.FILES.keys()) if request.FILES else 'None'}")
        print(f"[CREATE] request.FILES dict: {dict(request.FILES) if request.FILES else 'Empty'}")
        
        # Try to get images from request.FILES
        images_in_request = []
        if request.FILES:
            images_in_request = request.FILES.getlist('images')
            print(f"[CREATE] Images from getlist('images'): {len(images_in_request)}")
            
            # Also check all files in request.FILES
            all_files = []
            for key in request.FILES.keys():
                files = request.FILES.getlist(key)
                all_files.extend(files)
                print(f"[CREATE] Files with key '{key}': {len(files)}")
            print(f"[CREATE] Total files in request.FILES: {len(all_files)}")
        else:
            print(f"[CREATE] ⚠️ WARNING: request.FILES is empty or doesn't exist!")
        
        print(f"[CREATE] Images count in request: {len(images_in_request)}")
        
        # Create a copy of request.data without 'images' to avoid serializer validation issues
        # NOTE: 'images' in request.data might be a list of file names, but actual files are in request.FILES
        # IMPORTANT: Use dict() to create a mutable copy if request.data is a QueryDict
        if hasattr(request.data, 'copy'):
            data = request.data.copy()
        else:
            data = dict(request.data)
        
        # Remove 'images' from data dict if present (files are in request.FILES, not request.data)
        if 'images' in data:
            print(f"[CREATE] Found 'images' in request.data (removing from data dict): {data.get('images')}")
            if isinstance(data, dict):
                data.pop('images', None)
            else:
                # If it's a QueryDict, use the proper method
                data = dict(data)
                data.pop('images', None)
        
        print(f"[CREATE] Data dict keys (after removing images): {list(data.keys())}")
        print(f"[CREATE] Data dict: {data}")
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the house instance (should already have images loaded from perform_create)
        house = serializer.instance
        print(f"[CREATE] House ID: {house.pk}")
        
        # Force reload to ensure images are fresh - CRITICAL STEP
        from django.db.models import Prefetch
        house = House.objects.prefetch_related(
            Prefetch('images', queryset=HouseImage.objects.all().order_by('order', 'created_at'))
        ).select_related('user').get(pk=house.pk)
        
        # CRITICAL: Verify images exist in database
        image_count = house.images.count()
        print(f"[CREATE] ✅ House has {image_count} images in database")
        
        if image_count > 0:
            images_list = list(house.images.all())
            print(f"[CREATE] First image file: {images_list[0].image.name if images_list else 'None'}")
            # Test URL access
            try:
                test_url = images_list[0].image.url
                print(f"[CREATE] First image URL: {test_url}")
            except Exception as e:
                print(f"[CREATE] ❌ ERROR accessing image URL: {e}")
        else:
            print(f"[CREATE] ❌ WARNING: No images found in database!")
        
        # Serialize with request context for proper URL building
        response_serializer = self.get_serializer(house, context={'request': request})
        response_data = response_serializer.data
        
        # CRITICAL: Verify response has images
        image_urls = response_data.get('image_urls', [])
        images_array = response_data.get('images', [])
        print(f"[CREATE] Response check - image_urls: {len(image_urls)}, images array: {len(images_array)}")
        
        if len(image_urls) == 0 and len(images_array) == 0:
            print(f"[CREATE] ❌❌❌ CRITICAL ERROR: NO IMAGES IN RESPONSE!")
            print(f"[CREATE] House has {image_count} images in DB but serializer returned 0!")
            print(f"[CREATE] Attempting manual fix...")
            
            # MANUAL FIX: If serializer failed, manually add image URLs
            if image_count > 0:
                images_list = list(house.images.all())
                manual_urls = []
                for img in images_list:
                    if img.image:
                        try:
                            url = request.build_absolute_uri(img.image.url)
                            manual_urls.append(url)
                            print(f"[CREATE] Manually added image URL: {url}")
                        except Exception as e:
                            print(f"[CREATE] Error building URL: {e}")
                
                if manual_urls:
                    print(f"[CREATE] ✅ Manually added {len(manual_urls)} image URLs to response")
                    response_data['image_urls'] = manual_urls
        else:
            print(f"[CREATE] ✅✅✅ SUCCESS: Images included in response!")
            if len(image_urls) > 0:
                print(f"[CREATE] First image_url: {image_urls[0]}")
        
        print(f"[CREATE] ====================================")
        
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # Save house first to ensure it has a PK
        house = serializer.save(user=self.request.user)
        print(f"[INFO] House saved with PK: {house.pk}")
        
        # DEBUG: Check request.FILES before calling _handle_images
        print(f"[DEBUG] perform_create - request.FILES exists: {hasattr(self.request, 'FILES')}")
        print(f"[DEBUG] perform_create - request.FILES: {self.request.FILES if hasattr(self.request, 'FILES') else 'N/A'}")
        print(f"[DEBUG] perform_create - request.FILES keys: {list(self.request.FILES.keys()) if hasattr(self.request, 'FILES') and self.request.FILES else 'N/A'}")
        print(f"[DEBUG] perform_create - request.content_type: {getattr(self.request, 'content_type', 'N/A')}")
        
        # Handle multiple images (house must have PK for ForeignKey)
        images_created = self._handle_images(house, self.request)
        print(f"[INFO] Created {images_created} image(s) for house {house.pk}")
        
        # Update serializer.instance to the house with images loaded
        # This ensures the instance has the images relationship loaded
        house = House.objects.prefetch_related('images').select_related('user').get(pk=house.pk)
        serializer.instance = house

    def update(self, request, *args, **kwargs):
        """Override update to ensure images are included in response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Reload house with images for proper serialization
        house = serializer.instance
        house = House.objects.prefetch_related('images').get(pk=house.pk)
        
        # Create fresh serializer with reloaded house
        response_serializer = self.get_serializer(house)
        return Response(response_serializer.data)

    def perform_update(self, serializer):
        house = serializer.save(user=self.request.user)
        # Handle multiple images (new images will be added)
        self._handle_images(house, self.request)


# -----------------------------------------
# GUEST VIEWS (READ ONLY)
# -----------------------------------------

class GuestHouseListView(generics.ListAPIView):
    """Allows non-logged-in users to view all houses."""
    serializer_class = HouseSerializer
    permission_classes = [AllowAny]  # 👈 Guest access
    
    def get_queryset(self):
        """Prefetch images and user for efficient querying"""
        from django.db.models import Prefetch
        return House.objects.prefetch_related(
            Prefetch('images', queryset=HouseImage.objects.all().order_by('order', 'created_at'))
        ).select_related('user').all().order_by("-created_at")
    
    def get_serializer_context(self):
        """Ensure request context is passed to serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        """Override list to ensure images are included in response"""
        response = super().list(request, *args, **kwargs)
        
        # Verify images are included in response
        if hasattr(response, 'data') and isinstance(response.data, list):
            for house_data in response.data:
                house_id = house_data.get('id')
                image_urls = house_data.get('image_urls', [])
                images = house_data.get('images', [])
                
                # If no images found, try to manually add them
                if len(image_urls) == 0 and len(images) == 0 and house_id:
                    from .models import HouseImage
                    try:
                        house_images = HouseImage.objects.filter(house_id=house_id).order_by('order', 'created_at')
                        if house_images.exists():
                            manual_urls = []
                            for img in house_images:
                                if img.image:
                                    try:
                                        url = request.build_absolute_uri(img.image.url)
                                        manual_urls.append(url)
                                    except Exception as e:
                                        print(f"[GUEST_LIST] Error building URL for image {img.id}: {e}")
                            
                            if manual_urls:
                                house_data['image_urls'] = manual_urls
                                print(f"[GUEST_LIST] Manually added {len(manual_urls)} image URLs for house {house_id}")
                    except Exception as e:
                        print(f"[GUEST_LIST] Error fetching images for house {house_id}: {e}")
        
        return response


class GuestHouseDetailView(generics.RetrieveAPIView):
    """Allows non-logged-in users to view a single house."""
    serializer_class = HouseSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Prefetch images and user for efficient querying"""
        from django.db.models import Prefetch
        return House.objects.prefetch_related(
            Prefetch('images', queryset=HouseImage.objects.all().order_by('order', 'created_at'))
        ).select_related('user').all()
    
    def get_serializer_context(self):
        """Ensure request context is passed to serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to ensure images are included"""
        instance = self.get_object()
        
        # Force reload with images
        from django.db.models import Prefetch
        instance = House.objects.prefetch_related(
            Prefetch('images', queryset=HouseImage.objects.all().order_by('order', 'created_at'))
        ).select_related('user').get(pk=instance.pk)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

from .models import Billing
# views.py
# Upload Billing (User)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_billing(request):
    file = request.FILES.get('billing')
    if not file:
        return Response({'error': 'No file uploaded'}, status=400)

    billing = Billing.objects.create(user_profile=request.user.profile, file=file)
    serializer = BillingSerializer(billing, context={'request': request})
    return Response(serializer.data)

# Fetch all users with billing records
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_user_bills(request):
    users = User.objects.prefetch_related('billing_records').all()
    data = []
    for user in users:
        data.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "profile": {
                "billing_records": [b.file.url for b in user.billing_records.all()]
            }
        })
    return Response(data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_billing(request):
    user = request.user

    billing_id = request.data.get("id")
    if not billing_id:
        return Response({"error": "Billing ID is required"}, status=400)

    try:
        billing = Billing.objects.get(id=billing_id, user_profile=user.profile)
    except Billing.DoesNotExist:
        return Response({"error": "Billing not found"}, status=404)

    # Delete file from storage
    if billing.file and billing.file.name:
        billing.file.delete(save=False)

    billing.delete()
    return Response({"success": "Billing record deleted"})

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.filter(is_active=True).order_by('order', 'created_at')
    serializer_class = FAQSerializer

    def get_queryset(self):
        # Admins can see all FAQs (including inactive), regular users only see active ones
        if hasattr(self.request, 'user') and self.request.user.is_authenticated and self.request.user.is_staff:
            return FAQ.objects.all().order_by('order', 'created_at')
        return FAQ.objects.filter(is_active=True).order_by('order', 'created_at')

    def get_permissions(self):
        # Allow read access to everyone, but require admin for write operations
        if hasattr(self, 'action') and self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        # For list, retrieve, and any other read operations (including when action is None)
        return [AllowAny()]


class ServiceFeeViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceFeeSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        from django.utils import timezone
        
        # Admins can see all service fees
        if user.is_staff:
            queryset = ServiceFee.objects.all()
            
            # Filter by homeowner ID or name
            homeowner_id = self.request.query_params.get('homeowner_id')
            homeowner_name = self.request.query_params.get('homeowner_name')
            
            if homeowner_id:
                queryset = queryset.filter(homeowner_id=homeowner_id)
            if homeowner_name:
                queryset = queryset.filter(homeowner__username__icontains=homeowner_name)
            
            queryset = queryset.order_by('-created_at', '-due_date')
        else:
            # Homeowners can only see their own service fees (if verified)
            if hasattr(user, 'profile') and user.profile.is_verified:
                queryset = ServiceFee.objects.filter(homeowner=user).order_by('-created_at', '-due_date')
            else:
                # Unverified users see nothing
                return ServiceFee.objects.none()
        
        # Automatically mark bills as delayed if past due date
        today = timezone.now().date()
        delayed_fees = queryset.filter(
            status='unpaid',
            due_date__lt=today
        )
        
        # Update status to delayed in bulk
        if delayed_fees.exists():
            delayed_fees.update(status='delayed')
            # Refresh queryset to get updated status
            queryset = queryset.model.objects.filter(pk__in=queryset.values_list('pk', flat=True))
            if user.is_staff:
                queryset = queryset.order_by('-created_at', '-due_date')
            else:
                queryset = queryset.filter(homeowner=user).order_by('-created_at', '-due_date')
        
        return queryset

    def get_permissions(self):
        # Only authenticated users can access
        if hasattr(self, 'action'):
            # Homeowners can upload receipts via partial_update
            if self.action == 'partial_update':
                user = self.request.user
                # Check if user is the homeowner and verified
                if hasattr(user, 'profile') and user.profile.is_verified:
                    # Allow if they're updating their own service fee
                    return [IsAuthenticated()]
            # Only admins can create/update/delete
            if self.action in ['create', 'update', 'destroy']:
                return [IsAdminUser()]
        return [IsAuthenticated()]  # Authenticated users can view

    def get_object(self):
        """Override to check ownership for homeowners"""
        obj = super().get_object()
        user = self.request.user
        
        # If homeowner is trying to update, ensure they own this service fee
        if not user.is_staff and hasattr(user, 'profile') and user.profile.is_verified:
            if obj.homeowner != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(detail="You can only update your own service fees.")
        
        return obj

    def perform_create(self, serializer):
        """Create service fee + auto-generate payment link + send emails"""
        from .simple_paymongo import simple_paymongo
        from .models import PaymentLink
        
        try:
            service_fee = serializer.save()
        except Exception as e:
            print(f"Error saving service fee: {e}")
            raise
        
        # Auto-create payment link if amount exists
        if service_fee.amount:
            try:
                description = f"{service_fee.month or 'Monthly'} {service_fee.year or ''} Fee - {service_fee.homeowner.username}"
                
                # Generate payment link
                result = simple_paymongo.create_payment_link(
                    amount=service_fee.amount,
                    description=description
                )
                
                if result.get('success'):
                    # Save payment link
                    PaymentLink.objects.create(
                        service_fee=service_fee,
                        link_id=result['link_id'],
                        reference_number=result['reference_number'],
                        checkout_url=result['checkout_url'],
                        amount=service_fee.amount
                    )
                    
                    print(f"✅ Payment link created: {result['reference_number']}")
                    
                    # Send email to homeowner with payment link
                    if service_fee.homeowner.email:
                        simple_paymongo.send_payment_email(
                            to_email=service_fee.homeowner.email,
                            homeowner_name=service_fee.homeowner.username,
                            amount=service_fee.amount,
                            due_date=service_fee.due_date.strftime('%B %d, %Y') if service_fee.due_date else 'N/A',
                            reference=result['reference_number'],
                            checkout_url=result['checkout_url']
                        )
                else:
                    print(f"⚠️ Payment link creation failed: {result.get('error')}")
                    
            except Exception as e:
                print(f"⚠️ Error creating payment link: {e}")
                import traceback
                traceback.print_exc()

    def perform_update(self, serializer):
        """Update service fee and notify if status changes"""
        user = self.request.user
        old_status = self.get_object().status
        
        # If homeowner is updating, only allow receipt_image to be updated
        if not user.is_staff and hasattr(user, 'profile') and user.profile.is_verified:
            # Only allow receipt_image to be updated by homeowners
            allowed_fields = {'receipt_image'}
            data = serializer.validated_data
            restricted_fields = set(data.keys()) - allowed_fields
            if restricted_fields:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(f"Homeowners can only update receipt_image. Restricted fields: {', '.join(restricted_fields)}")
        
        service_fee = serializer.save()
        
        # Send email if status changed to paid (only if admin changed it)
        if user.is_staff and old_status != service_fee.status and service_fee.status == 'paid' and service_fee.homeowner.email:
            try:
                subject = f"Service Fee Payment Confirmed - {service_fee.month or 'Monthly'} {service_fee.year or ''}"
                message = f"""
Dear {service_fee.homeowner.username},

Your service fee payment for {service_fee.month or 'Monthly'} {service_fee.year or ''} has been confirmed.

Amount: ₱{service_fee.amount or 'N/A'}
Status: Paid

Thank you for your payment.

Happy Homes Administration
                """
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[service_fee.homeowner.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error sending payment confirmation email: {e}")
        
        # Notify admin when homeowner uploads receipt
        if not user.is_staff and hasattr(user, 'profile') and user.profile.is_verified:
            if 'receipt_image' in serializer.validated_data and service_fee.receipt_image:
                try:
                    # Get admin users to notify
                    from django.contrib.auth.models import User
                    admin_users = User.objects.filter(is_staff=True, is_active=True)
                    admin_emails = [admin.email for admin in admin_users if admin.email]
                    
                    if admin_emails:
                        subject = f"Receipt Uploaded - {service_fee.homeowner.username} - {service_fee.month or 'Monthly'} {service_fee.year or ''}"
                        message = f"""
A homeowner has uploaded a payment receipt.

Homeowner: {service_fee.homeowner.username} ({service_fee.homeowner.email})
Service Fee: {service_fee.month or 'Monthly'} {service_fee.year or ''}
Amount: ₱{service_fee.amount or 'N/A'}

Please review the receipt in the admin panel.

Happy Homes System
                        """
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=admin_emails,
                            fail_silently=True,
                        )
                except Exception as e:
                    print(f"Error sending receipt notification to admin: {e}")

# --- ViewSets ---
@method_decorator(csrf_exempt, name='dispatch')
class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reviews
    
    Permissions:
    - GET (list, retrieve): Anyone can view reviews (guests, users, admins)
    - POST (create): Only authenticated users can create reviews
    - PUT/PATCH (update): Only the review owner or admin can update
    - DELETE: Only the review owner or admin can delete
    """
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        pin_id = self.request.query_params.get("pin_id")
        qs = Review.objects.all()
        
        if pin_id:
            qs = qs.filter(pin_id=pin_id)
        
        return qs.order_by("-created_at")

    def get_authenticators(self):
        """
        Override authentication to allow unauthenticated access for read operations.
        This allows guests to view reviews without authentication.
        """
        request = getattr(self, 'request', None)
        if request and request.method in ['GET', 'OPTIONS']:
            # No authentication required for viewing reviews
            return []
        # Require authentication for create, update, delete (POST, PUT, PATCH, DELETE)
        return [JWTAuthentication()]

    def perform_create(self, serializer):
        # Ensure user can only create one review per pin
        pin = serializer.validated_data['pin']
        user = self.request.user
        
        # Check if review already exists
        existing_review = Review.objects.filter(pin=pin, user=user).first()
        if existing_review:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You have already reviewed this location. You can update your existing review.")
        
        serializer.save(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

from django.contrib.auth.hashers import make_password   
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_update_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=404)

    data = request.data
    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.email = data.get("email", user.email)
    user.save()

    # Update profile if exists
    profile_data = data.get("profile", {})
    profile = getattr(user, "profile", None)
    if profile:
        profile.contact_number = profile_data.get("contact_number", profile.contact_number)
        profile.save()

    return Response({"detail": "User updated successfully"}, status=200)


# -------------------------
# Admin: Change User Password
# -------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_change_user_password(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=404)

    new_password = request.data.get("new_password")
    if not new_password:
        return Response({"detail": "New password is required"}, status=400)

    user.password = make_password(new_password)
    user.save()

    return Response({"detail": "Password updated successfully"}, status=200)
# --- Simple user info (legacy) ---
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_user_profile(request):
#     user = request.user
    
#     return Response({
#         'username': user.username,
#         'email': user.email,
#         'first_name': user.first_name,
#         'last_name': user.last_name,
#         'is_staff': user.is_staff,
#     })

# import json
# import requests
# from core import settings  # Correct the import
# from rest_framework import status, viewsets
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.response import Response
# from django.contrib.auth.models import User
# from rest_framework_simplejwt.tokens import RefreshToken
# from .models import Post, Message, Subdivision, Pin
# from .serializers import PostSerializer, MessageSerializer, SubdivisionSerializer, PinSerializer, UserSerializer
# from rest_framework.authentication import SessionAuthentication, BasicAuthentication
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework.viewsets import ModelViewSet
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from django.http import JsonResponse




# @api_view(['POST'])
# def register(request):
#     data = request.data
#     if User.objects.filter(username=data.get('username')).exists():
#         return Response({'detail': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

#     user = User.objects.create_user(
#         username=data.get('username'),
#         password=data.get('password'),
#         first_name=data.get('first_name', ''),
#         last_name=data.get('last_name', ''),
#         email=data.get('email', '')
        
#     )

#     serializer = UserSerializer(user)
#     refresh = RefreshToken.for_user(user)

#     return Response({
#         'user': serializer.data,
#         'access': str(refresh.access_token),
#         'refresh': str(refresh),
#     })

# @api_view(['GET'])
# def get_posts(request):
#     posts = Post.objects.all()
#     serializer = PostSerializer(posts, many=True)
#     return Response(serializer.data)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_user_posts(request):
#     posts = Post.objects.filter(user=request.user)
#     serializer = PostSerializer(posts, many=True)
#     return Response(serializer.data)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_user_profile(request):
#     user = request.user
#     return Response({
#         'username': user.username,
#         'email': user.email,
#         'first_name': user.first_name,
#         'last_name': user.last_name,
#         'is_staff': user.is_staff,
#     })

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def profile(request):
#     user = request.user
#     serializer = UserSerializer(user)
#     return Response(serializer.data)

# @api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# def update_user_profile(request):
#     user = request.user
#     data = request.data

#     # Update fields if provided
#     user.first_name = data.get('first_name', user.first_name)
#     user.last_name = data.get('last_name', user.last_name)
#     user.email = data.get('email', user.email)
#     user.username = data.get('username', user.username)
    
#     user.save()

#     return Response({
#         'username': user.username,
#         'email': user.email,
#         'first_name': user.first_name,
#         'last_name': user.last_name,
#         'is_staff': user.is_staff,
#     })

# #messenger naten temporary lang
# @api_view(['GET', 'POST'])
# def message_list_create(request):
#     if request.method == 'GET':
#         messages = Message.objects.all().order_by('timestamp')
#         serializer = MessageSerializer(messages, many=True)
#         return Response(serializer.data)

#     if request.method == 'POST':
#         serializer = MessageSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=201)
#         return Response(serializer.errors, status=400)
    
# @api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
# def subdivision_list_create(request):
#     if request.method == 'GET':
#         subdivisions = Subdivision.objects.all()
#         serializer = SubdivisionSerializer(subdivisions, many=True)
#         return Response(serializer.data)

#     elif request.method == 'POST':
#         serializer = SubdivisionSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET', 'PUT', 'DELETE'])
# @permission_classes([IsAuthenticated])
# def subdivision_detail(request, pk):
#     try:
#         subdivision = Subdivision.objects.get(pk=pk)
#     except Subdivision.DoesNotExist:
#         return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'GET':
#         serializer = SubdivisionSerializer(subdivision)
#         return Response(serializer.data)

#     elif request.method == 'PUT':
#         serializer = SubdivisionSerializer(subdivision, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     elif request.method == 'DELETE':
#         subdivision.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
    
# @method_decorator(csrf_exempt, name='dispatch')
# class PinViewSet(ModelViewSet):
#     queryset = Pin.objects.all()
#     serializer_class = PinSerializer
#     permission_classes = [AllowAny]  # For testing
#     authentication_classes = [BasicAuthentication]  # or []

# @method_decorator(csrf_exempt, name='dispatch')
# class SubdivisionViewSet(ModelViewSet):
#     queryset = Subdivision.objects.all()
#     serializer_class = SubdivisionSerializer
#     permission_classes = [AllowAny]
#     authentication_classes = [BasicAuthentication]

# @csrf_exempt  # To allow POST requests without CSRF token (for simplicity)
# def verify_recaptcha(request):
#     if request.method == 'POST':
#         # Get the data from the frontend
#         data = json.loads(request.body)
#         recaptcha_token = data.get('recaptcha')

#         if not recaptcha_token:
#             return JsonResponse({'message': 'reCAPTCHA token missing'}, status=400)

#         # Google reCAPTCHA secret key (use your actual secret key here)
#         secret_key = settings.RECAPTCHA_SECRET_KEY

#         # Make a POST request to Google's reCAPTCHA verification API
#         payload = {
#             'secret': secret_key,
#             'response': recaptcha_token
#         }
#         response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
#         result = response.json()

#         if not result.get('success'):
#             return JsonResponse({'message': 'reCAPTCHA verification failed'}, status=400)

#         # If the reCAPTCHA was successful, you can proceed with the login
#         # Example (replace with actual login logic)
#         username = data.get('username')
#         password = data.get('password')

#         # Your actual authentication logic goes here
#         if username == 'test' and password == 'password':
#             return JsonResponse({'access': 'fake-jwt-token'}, status=200)

#         return JsonResponse({'message': 'Invalid username or password'}, status=400)

#     return JsonResponse({'message': 'Invalid request method'}, status=405)

# class BookingViewSet(viewsets.ModelViewSet):
#     queryset = Booking.objects.all()
#     serializer_class = BookingSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         facility_id = self.request.query_params.get('facility_id')
#         qs = Booking.objects.filter(user=self.request.user)
#         if facility_id:
#             qs = qs.filter(facility_id=facility_id)
#         return qs

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)  # user comes from JWT

    # def get_queryset(self):
    #     facility_id = self.request.query_params.get('facility_id')
    #     qs = Booking.objects.filter(user=self.request.user)
    #     if facility_id:
    #         qs = qs.filter(facility_id=facility_id)
    #     return qs

    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)
    
# @api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# def update_user_profile(request):
#     user = request.user

#     # Ensure profile exists
#     profile, created = UserProfile.objects.get_or_create(user=user)

#     user.first_name = request.data.get("first_name", user.first_name)
#     user.last_name = request.data.get("last_name", user.last_name)
#     user.email = request.data.get("email", user.email)
#     user.username = request.data.get("username", user.username)
#     user.save()

#     if "profile_image" in request.FILES:
#         profile.profile_image = request.FILES["profile_image"]
#         profile.save()

#     return Response({
#         "username": user.username,
#         "first_name": user.first_name,
#         "last_name": user.last_name,
#         "email": user.email,
#         "profile_image": profile.profile_image.url if profile.profile_image else None
#     })    

# @api_view(['PUT'])
# def verify_user(request, user_id):
#     user = get_object_or_404(User, id=user_id)
#     profile = user.profile
#     profile.is_verified = True
#     profile.save()
#     return Response({"detail": "User verified successfully"})
    
# # Reject user
# @api_view(['PUT'])
# @permission_classes([IsAdminUser])
# def reject_user(request, user_id):
#     try:
#         profile = UserProfile.objects.get(user__id=user_id)
#         profile.is_verified = False
#         profile.document.delete(save=True)  # Optional: delete uploaded doc
#         return Response({'message': 'User rejected successfully'})
#     except UserProfile.DoesNotExist:
#         return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)   
    
# @api_view(['GET'])
# @permission_classes([IsAdminUser])
# def pending_verifications(request):
#     pending_profiles = UserProfile.objects.filter(is_verified=False, document__isnull=False)
#     data = []
#     for profile in pending_profiles:
#         data.append({
#             'id': profile.user.id,
#             'username': profile.user.username,
#             'email': profile.user.email,
#             'document': profile.document.url if profile.document else None,
#             'is_verified': profile.is_verified,  # <-- add this
#         })
#     return Response(data) 


# ============================================================================
# VISITOR REQUEST VIEWSET (One-Time PIN System)
# ============================================================================

from .visitor_request_utils import generate_visitor_request_pdf, send_visitor_request_approval_email
from .maintenance_request_utils import (
    send_maintenance_request_created_emails,
    send_maintenance_request_approval_email,
    send_maintenance_request_decline_email
)


class VisitorRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing visitor requests with one-time PIN generation
    
    Permissions:
    - GET (list, retrieve): Residents see their own, admins see all
    - POST (create): Only authenticated residents can create requests
    - PUT/PATCH (update): Only admins can update (for approval)
    - DELETE: Only admins can delete
    """
    serializer_class = VisitorRequestSerializer
    authentication_classes = [JWTAuthentication]  # Default, overridden in get_authenticators for verify_pin
    permission_classes = [IsAuthenticated]
    
    # Explicitly allow POST for custom actions
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
    
    def get_queryset(self):
        """
        Filter requests based on user role:
        - Residents see only their own requests
        - Admins see all requests
        """
        user = self.request.user
        
        # Handle unauthenticated users (shouldn't happen for list, but safety check)
        if not user or not user.is_authenticated:
            return VisitorRequest.objects.none()
        
        # Use select_related to optimize queries and prevent serialization issues
        # Note: visitor_record is nullable, so we handle it separately if needed
        base_queryset = VisitorRequest.objects.select_related(
            'resident', 
            'approved_by'
        )
        
        if user.is_staff:
            # Admin can see all requests
            queryset = base_queryset.all()
        else:
            # Residents see only their own requests
            queryset = base_queryset.filter(resident=user)
        
        # Filter by status if provided
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_context(self):
        """Pass request context to serializer for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_authenticators(self):
        """Override to allow unauthenticated access for verify_pin action"""
        # Check action first (set after dispatch)
        action = getattr(self, 'action', None)
        if action == 'verify_pin':
            return []  # No authentication required for PIN verification
        
        # Fallback: check request path from META (available during initialization)
        try:
            request = getattr(self, 'request', None)
            if request:
                # Try to get path from request object or META
                path = getattr(request, 'path', None) or getattr(request, 'META', {}).get('PATH_INFO', '')
                if path and 'verify_pin' in path:
                    return []  # No authentication required for PIN verification
        except (AttributeError, TypeError, KeyError):
            pass
        
        return [JWTAuthentication()]
    
    def get_permissions(self):
        """Override to allow unauthenticated access for verify_pin action"""
        # Check action first (set after dispatch)
        action = getattr(self, 'action', None)
        if action == 'verify_pin':
            return [AllowAny()]  # No permission required for PIN verification
        
        # Fallback: check request path from META
        try:
            request = getattr(self, 'request', None)
            if request:
                # Try to get path from request object or META
                path = getattr(request, 'path', None) or getattr(request, 'META', {}).get('PATH_INFO', '')
                if path and 'verify_pin' in path:
                    return [AllowAny()]  # No permission required for PIN verification
        except (AttributeError, TypeError, KeyError):
            pass
        
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Set resident to current user when creating request"""
        serializer.save(resident=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """Override list to add error handling and safe serialization"""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                # Paginated response
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            # Non-paginated response - serialize with error handling per object
            serializer = self.get_serializer(queryset, many=True)
            
            # Filter out any objects that failed to serialize
            safe_data = []
            for i, obj in enumerate(queryset):
                try:
                    obj_serializer = self.get_serializer(obj)
                    safe_data.append(obj_serializer.data)
                except Exception as obj_error:
                    import traceback
                    print(f"[WARNING] Failed to serialize VisitorRequest {obj.id}: {str(obj_error)}")
                    # Try to get at least basic data
                    try:
                        safe_data.append({
                            'id': obj.id,
                            'visitor_name': obj.visitor_name,
                            'status': obj.status,
                            'visit_date': str(obj.visit_date) if obj.visit_date else None,
                            'error': 'Partial serialization'
                        })
                    except:
                        # Skip this object if even basic serialization fails
                        pass
            
            return Response(safe_data)
            
        except Exception as e:
            import traceback
            from django.conf import settings
            
            error_traceback = traceback.format_exc()
            print(f"ERROR in VisitorRequestViewSet.list: {str(e)}")
            print(f"Traceback: {error_traceback}")
            
            return Response(
                {
                    'error': f'Error fetching visitor requests: {str(e)}',
                    'detail': str(e),
                    'traceback': error_traceback if settings.DEBUG else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """
        Admin action to approve a visitor request
        - Generates one-time PIN
        - Creates PDF
        - Sends email to homeowner with PDF
        """
        visitor_request = self.get_object()
        
        if visitor_request.status != 'pending_admin':
            return Response(
                {'error': f'Request is already {visitor_request.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate one-time PIN
            visitor_request.generate_one_time_pin()
            
            # Update status and approval info
            visitor_request.status = 'approved'
            visitor_request.approved_by = request.user
            visitor_request.approved_at = timezone.now()
            visitor_request.save()
            
            # Create Visitor record so it appears in visitors list
            # Find or create ResidentPin for the homeowner
            from .models import ResidentPin, Visitor
            resident_pin, _ = ResidentPin.objects.get_or_create(user=visitor_request.resident)
            
            # Create Visitor record (but don't set time_in yet - that happens when guard checks in)
            visitor = Visitor.objects.create(
                name=visitor_request.visitor_name,
                gmail=visitor_request.visitor_email,
                contact_number=visitor_request.visitor_contact_number or '',
                reason=visitor_request.reason or '',
                pin_entered=visitor_request.one_time_pin,
                resident=resident_pin,
                status='approved',  # Already approved via request
                # Don't set time_in yet - guard will set it when checking in
            )
            
            # Link visitor record to request
            visitor_request.visitor_record = visitor
            visitor_request.save()
            
            # Generate PDF
            pdf_path = generate_visitor_request_pdf(visitor_request)
            if pdf_path:
                visitor_request.pdf_file_path = pdf_path
                visitor_request.pdf_generated = True
                visitor_request.save()
            
            # Send email with PDF attachment
            email_sent = send_visitor_request_approval_email(visitor_request)
            if email_sent:
                visitor_request.email_sent = True
                visitor_request.email_sent_at = timezone.now()
                visitor_request.save()
            
            serializer = self.get_serializer(visitor_request)
            return Response({
                'message': 'Visitor request approved successfully',
                'visitor_request': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to approve request: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def decline(self, request, pk=None):
        """
        Admin action to decline a visitor request
        """
        visitor_request = self.get_object()
        declined_reason = request.data.get('declined_reason', '')
        
        if visitor_request.status != 'pending_admin':
            return Response(
                {'error': f'Request is already {visitor_request.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        visitor_request.status = 'declined'
        visitor_request.declined_reason = declined_reason
        visitor_request.approved_by = request.user
        visitor_request.approved_at = timezone.now()
        visitor_request.save()
        
        # TODO: Send decline email to homeowner (optional)
        
        serializer = self.get_serializer(visitor_request)
        return Response({
            'message': 'Visitor request declined',
            'visitor_request': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def pdf(self, request, pk=None):
        """
        Download PDF for a visitor request
        Allows admins to download any PDF, residents to download their own
        """
        visitor_request = self.get_object()
        
        # Check permissions: admin can access any, residents can only access their own
        if not request.user.is_staff and visitor_request.resident != request.user:
            return Response(
                {'error': 'You do not have permission to access this PDF'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not visitor_request.pdf_file_path:
            # Generate PDF if it doesn't exist
            pdf_path = generate_visitor_request_pdf(visitor_request)
            if pdf_path:
                visitor_request.pdf_file_path = pdf_path
                visitor_request.pdf_generated = True
                visitor_request.save()
            else:
                return Response(
                    {'error': 'Failed to generate PDF'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        try:
            file_path = visitor_request.pdf_file_path.path
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    pdf_content = f.read()
                    # Verify it's actually a PDF by checking the PDF header
                    if pdf_content[:4] != b'%PDF':
                        return Response(
                            {'error': 'File is not a valid PDF'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                    
                    response = HttpResponse(pdf_content, content_type='application/pdf')
                    # Use 'inline' instead of 'attachment' to open in browser
                    # Properly encode filename for international characters
                    filename = f"visitor_request_{visitor_request.id}.pdf"
                    response['Content-Disposition'] = f'inline; filename="{filename}"'
                    response['Content-Length'] = len(pdf_content)
                    # Additional headers to ensure proper PDF handling
                    response['X-Content-Type-Options'] = 'nosniff'
                    return response
            else:
                return Response(
                    {'error': 'PDF file not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def checkin_one_time(self, request):
        """
        Check-in using one-time PIN (public endpoint)
        Validates PIN and creates Visitor record
        """
        pin = request.data.get('pin')
        name = request.data.get('name')
        gmail = request.data.get('gmail')
        contact_number = request.data.get('contact_number', '')
        reason = request.data.get('reason', '')
        
        if not pin or not name or not gmail:
            return Response(
                {'error': 'PIN, name, and email are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            visitor_request = VisitorRequest.objects.get(one_time_pin=pin, status='approved')
        except VisitorRequest.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired PIN'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate PIN is still valid (check date/time)
        if not visitor_request.is_valid():
            visitor_request.status = 'expired'
            visitor_request.save()
            return Response(
                {'error': 'PIN has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if PIN was already used (has time_in set)
        if visitor_request.visitor_record:
            if visitor_request.visitor_record.time_in:
                visitor_request.status = 'used'
                visitor_request.save()
                return Response(
                    {'error': 'PIN has already been used'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Visitor record exists but not checked in yet - update it
                visitor = visitor_request.visitor_record
                visitor.time_in = timezone.now()
                visitor.save()
                visitor_request.status = 'used'
                visitor_request.save()
                serializer = VisitorSerializer(visitor)
                return Response({
                    'message': 'Check-in successful',
                    'visitor': serializer.data
                }, status=status.HTTP_200_OK)
        
        # If no visitor record exists, create one (shouldn't happen if approve creates it, but safety check)
        from .models import ResidentPin
        resident_pin, _ = ResidentPin.objects.get_or_create(user=visitor_request.resident)
        
        # Create Visitor record
        visitor = Visitor.objects.create(
            name=name,
            gmail=gmail,
            contact_number=contact_number,
            reason=reason or visitor_request.reason,
            pin_entered=pin,
            resident=resident_pin,
            status='approved',  # Already approved via request
            time_in=timezone.now()
        )
        
        # Link visitor record to request
        visitor_request.visitor_record = visitor
        visitor_request.status = 'used'
        visitor_request.save()
        
        serializer = VisitorSerializer(visitor)
        return Response({
            'message': 'Check-in successful',
            'visitor': serializer.data
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        Delete visitor request with proper validation
        - Admins can delete any request (with warning if used)
        - Homeowners can only delete their own pending/declined requests
        """
        visitor_request = self.get_object()
        
        # Admins can delete any request
        if request.user.is_staff:
            visitor_request.delete()
            return Response(
                {'message': 'Visitor request deleted successfully'},
                status=status.HTTP_200_OK
            )
        
        # Homeowners can only delete their own requests
        if visitor_request.resident != request.user:
            return Response(
                {'error': 'You can only delete your own visitor requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Homeowners can delete any of their own requests (pending, declined, approved, or used)
        # Frontend will show appropriate warnings for approved/used requests
        visitor_request.delete()
        return Response(
            {'message': 'Visitor request deleted successfully'},
            status=status.HTTP_200_OK
        )


# ============================================================================
# MAINTENANCE REQUEST VIEWSET
# ============================================================================

class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing maintenance requests
    
    Permissions:
    - GET (list, retrieve): Residents see their own, admins see all
    - POST (create): Only authenticated residents can create requests
    - PUT/PATCH (update): Only admins can update (for approval)
    - DELETE: Only admins can delete
    """
    serializer_class = MaintenanceRequestSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter requests based on user role:
        - Residents see only their own requests
        - Admins see all requests
        """
        user = self.request.user
        
        if user.is_staff:
            # Admin can see all requests
            queryset = MaintenanceRequest.objects.all()
        else:
            # Residents see only their own requests
            queryset = MaintenanceRequest.objects.filter(homeowner=user)
        
        # Filter by status if provided
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_context(self):
        """Pass request context to serializer for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Set homeowner and send email notifications"""
        maintenance_request = serializer.save(homeowner=self.request.user)
        
        # Send email notifications (non-blocking)
        try:
            send_maintenance_request_created_emails(maintenance_request)
        except Exception as email_error:
            print(f"[WARNING] Email notification failed (request still created): {email_error}")
            import traceback
            traceback.print_exc()
    
    def update(self, request, *args, **kwargs):
        """
        Allow homeowners to update their own pending requests
        Admins can update any request
        """
        maintenance_request = self.get_object()
        user = request.user
        
        # Check permissions
        if not user.is_staff:
            # Homeowners can only update their own requests
            if maintenance_request.homeowner != user:
                return Response(
                    {'error': 'You can only update your own maintenance requests'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Homeowners can only update pending requests
            if maintenance_request.status != 'pending':
                return Response(
                    {'error': 'You can only update pending requests. This request is already processed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Proceed with update
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(maintenance_request, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        """Save the updated request"""
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete maintenance request with proper validation
        - Admins can delete any request
        - Homeowners can only delete their own pending/declined requests
        """
        maintenance_request = self.get_object()
        user = request.user
        
        # Admins can delete any request
        if user.is_staff:
            maintenance_request.delete()
            return Response(
                {'message': 'Maintenance request deleted successfully'},
                status=status.HTTP_200_OK
            )
        
        # Homeowners can only delete their own requests
        if maintenance_request.homeowner != user:
            return Response(
                {'error': 'You can only delete your own maintenance requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Homeowners can delete any of their own requests (pending, declined, approved, etc.)
        # This allows them to clean up their request list
        maintenance_request.delete()
        return Response(
            {'message': 'Maintenance request deleted successfully'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """
        Admin action to approve a maintenance request
        - Updates status
        - Sends email to homeowner
        """
        maintenance_request = self.get_object()
        
        if maintenance_request.status != 'pending':
            return Response(
                {'error': f'Request is already {maintenance_request.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update status and approval info
            maintenance_request.status = 'approved'
            maintenance_request.approved_by = request.user
            maintenance_request.approved_at = timezone.now()
            maintenance_request.save()
            
            # Send approval email
            try:
                send_maintenance_request_approval_email(maintenance_request)
            except Exception as email_error:
                print(f"[WARNING] Failed to send approval email: {email_error}")
            
            serializer = self.get_serializer(maintenance_request)
            return Response({
                'message': 'Maintenance request approved successfully',
                'maintenance_request': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to approve request: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def decline(self, request, pk=None):
        """
        Admin action to decline a maintenance request
        - Updates status with decline reason
        - Sends email to homeowner
        """
        maintenance_request = self.get_object()
        declined_reason = request.data.get('declined_reason', '')
        
        if maintenance_request.status != 'pending':
            return Response(
                {'error': f'Request is already {maintenance_request.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            maintenance_request.status = 'declined'
            maintenance_request.declined_reason = declined_reason
            maintenance_request.approved_by = request.user
            maintenance_request.approved_at = timezone.now()
            maintenance_request.save()
            
            # Send decline email
            try:
                send_maintenance_request_decline_email(maintenance_request)
            except Exception as email_error:
                print(f"[WARNING] Failed to send decline email: {email_error}")
            
            serializer = self.get_serializer(maintenance_request)
            return Response({
                'message': 'Maintenance request declined',
                'maintenance_request': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to decline request: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post', 'patch'], permission_classes=[IsAdminUser])
    def add_feedback(self, request, pk=None):
        """
        Admin action to add or update feedback on a maintenance request
        Can be used at any stage (pending, approved, in_progress, completed)
        """
        maintenance_request = self.get_object()
        admin_feedback = request.data.get('admin_feedback', '')
        
        try:
            maintenance_request.admin_feedback = admin_feedback
            maintenance_request.save()
            
            serializer = self.get_serializer(maintenance_request)
            return Response({
                'message': 'Admin feedback updated successfully',
                'maintenance_request': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to update feedback: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_status_message(self, visitor_request, is_valid, is_used, is_expired, is_approved, 
                           is_pending, is_declined, is_not_yet_valid, is_past_valid, is_within_window,
                           visit_datetime_start, visit_datetime_end):
        """Helper method to generate detailed status message based on time/date intervals"""
        from django.utils import timezone
        from django.utils.formats import date_format, time_format
        
        # Wrong PIN case is handled before this method is called
        
        if is_declined:
            return 'This PIN has been declined by admin'
        
        if is_pending:
            return 'This PIN is pending admin approval'
        
        if is_used:
            return 'This PIN has already been used'
        
        if is_expired:
            return 'This PIN has expired'
        
        if is_approved:
            # Check time/date scenarios - order matters!
            # First check if it's past the valid time window
            if is_past_valid and visit_datetime_end:
                # Format the end datetime for display
                end_str = visit_datetime_end.strftime('%Y-%m-%d %I:%M %p')
                return f'PIN is approved, but has passed the valid time/date. Valid until: {end_str}'
            
            # Then check if it's not yet valid (before the time window)
            if is_not_yet_valid and visit_datetime_start:
                # Format the start datetime for display
                start_str = visit_datetime_start.strftime('%Y-%m-%d %I:%M %p')
                return f'PIN is approved, but the visit time/date is not yet valid. Valid from: {start_str}'
            
            # If within window, it's valid
            if is_within_window:
                return 'PIN is valid and ready for use'
            
            # Fallback if date/time info is missing
            return 'PIN is approved'
        
        # Fallback for any other status
        if is_expired or not is_valid:
            return 'This PIN has expired or is outside valid time window'
        
        return 'Unknown status'


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_pin_view(request):
    """
    Standalone view for PIN verification (bypasses ViewSet routing issues)
    Guard/Entrance endpoint to verify one-time PIN
    Returns visitor request details without creating Visitor record
    Public endpoint - no authentication required
    """
    from .models import VisitorRequest
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.conf import settings
    from rest_framework import status
    import traceback
    
    # Safely get PIN from request
    try:
        if hasattr(request, 'data'):
            pin = request.data.get('pin')
        else:
            import json
            body = request.body.decode('utf-8')
            data = json.loads(body) if body else {}
            pin = data.get('pin')
    except (AttributeError, json.JSONDecodeError, UnicodeDecodeError) as e:
        return Response(
            {'error': f'Invalid request format: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not pin:
        return Response(
            {'error': 'PIN is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        visitor_request = VisitorRequest.objects.select_related('resident', 'visitor_record').get(one_time_pin=pin)
    except VisitorRequest.DoesNotExist:
        return Response(
            {
                'valid': False,
                'error': 'Invalid PIN - PIN not found'
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {
                'valid': False,
                'error': f'Error looking up PIN: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    try:
        # Check basic PIN status - handle visitor_record safely
        is_used = False
        visitor_record = None
        is_checked_out = False
        try:
            if visitor_request.visitor_record:
                visitor_record = visitor_request.visitor_record
                if hasattr(visitor_record, 'time_in'):
                    is_used = visitor_record.time_in is not None
                if hasattr(visitor_record, 'time_out'):
                    is_checked_out = visitor_record.time_out is not None
        except (AttributeError, Exception):
            is_used = False
            is_checked_out = False
        
        # AUTO CHECKOUT LOGIC: If visitor is checked in but not checked out, perform checkout
        if visitor_record and is_used and not is_checked_out:
            visitor_record.time_out = timezone.now()
            visitor_record.save(update_fields=['time_out'])
            is_checked_out = True
            
            # Optional: Send notification
            try:
                if visitor_record.resident and visitor_record.resident.user.email:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    send_mail(
                        subject="🚪 Visitor Checked Out",
                        message=f"Visitor {visitor_record.name} has checked out successfully at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[visitor_record.resident.user.email],
                        fail_silently=True,
                    )
            except Exception:
                pass  # Don't fail if email fails
        
        is_expired_status = visitor_request.status == 'expired'
        is_approved = visitor_request.status == 'approved'
        is_pending = visitor_request.status == 'pending_admin'
        is_declined = visitor_request.status == 'declined'
        
        visit_datetime_start = None
        visit_datetime_end = None
        now = timezone.now()
        
        # Check time/date validity
        is_not_yet_valid = False
        is_past_valid = False
        is_within_window = False
        
        if visitor_request.visit_date and visitor_request.visit_start_time:
            visit_datetime_start_naive = datetime.combine(visitor_request.visit_date, visitor_request.visit_start_time)
            visit_datetime_start = timezone.make_aware(visit_datetime_start_naive)
            
        end_date = visitor_request.visit_end_date if visitor_request.visit_end_date else visitor_request.visit_date
        if end_date and visitor_request.visit_end_time:
            visit_datetime_end_naive = datetime.combine(end_date, visitor_request.visit_end_time)
            visit_datetime_end = timezone.make_aware(visit_datetime_end_naive)
            
            if visit_datetime_end and visit_datetime_start and visit_datetime_end < visit_datetime_start and visitor_request.visit_date == end_date:
                visit_datetime_end += timedelta(days=1)
        
        # Check time/date intervals
        if visit_datetime_start and visit_datetime_end:
            if now < visit_datetime_start:
                is_not_yet_valid = True
            elif now > visit_datetime_end:
                is_past_valid = True
            else:
                is_within_window = True
        
        # Record PIN entry time when PIN is entered at guard station
        if not visitor_request.pin_entered_at:
            visitor_request.pin_entered_at = timezone.now()
            visitor_request.save(update_fields=['pin_entered_at'])
        
        # Determine overall validity (for check-in only, checkout is handled above)
        is_valid = is_approved and not is_used and is_within_window and not is_expired_status and not is_past_valid
        
        # Get status message
        if is_checked_out:
            checkout_time = visitor_record.time_out.strftime('%Y-%m-%d %I:%M %p') if visitor_record and visitor_record.time_out else 'now'
            status_message = f'✅ Visitor {visitor_request.visitor_name} has been checked out successfully at {checkout_time}'
        elif is_declined:
            status_message = 'This PIN has been declined by admin'
        elif is_pending:
            status_message = 'This PIN is pending admin approval'
        elif is_used:
            status_message = 'This PIN has already been used (visitor already checked in)'
        elif is_expired_status:
            status_message = 'This PIN has expired'
        elif is_approved:
            if is_past_valid and visit_datetime_end:
                end_str = visit_datetime_end.strftime('%Y-%m-%d %I:%M %p')
                status_message = f'PIN is approved, but has passed the valid time/date. Valid until: {end_str}'
            elif is_not_yet_valid and visit_datetime_start:
                start_str = visit_datetime_start.strftime('%Y-%m-%d %I:%M %p')
                status_message = f'PIN is approved, but the visit time/date is not yet valid. Valid from: {start_str}'
            elif is_within_window:
                status_message = 'PIN is valid and ready for use'
            else:
                status_message = 'PIN is approved'
        else:
            status_message = 'Unknown status'
        
        return Response({
            'valid': is_valid or is_checked_out,  # Valid if can check-in OR just checked out
            'pin': pin,
            'checked_out': is_checked_out,  # New field to indicate checkout happened
            'visitor_request': {
                'id': visitor_request.id,
                'visitor_name': visitor_request.visitor_name,
                'visitor_email': visitor_request.visitor_email,
                'visitor_contact_number': visitor_request.visitor_contact_number or '',
                'vehicle_plate_number': visitor_request.vehicle_plate_number or '',
                'reason': visitor_request.reason or '',
                'visit_date': visitor_request.visit_date.strftime('%Y-%m-%d') if visitor_request.visit_date else '',
                'visit_end_date': visitor_request.visit_end_date.strftime('%Y-%m-%d') if visitor_request.visit_end_date else None,
                'visit_start_time': visitor_request.visit_start_time.strftime('%H:%M') if visitor_request.visit_start_time else '',
                'visit_end_time': visitor_request.visit_end_time.strftime('%H:%M') if visitor_request.visit_end_time else '',
                'status': visitor_request.status,
                'resident_name': visitor_request.resident.username if visitor_request.resident else 'Unknown',
                'resident_email': visitor_request.resident.email if visitor_request.resident else '',
                'visit_datetime_start': visit_datetime_start.isoformat() if visit_datetime_start else None,
                'visit_datetime_end': visit_datetime_end.isoformat() if visit_datetime_end else None,
            },
            'details': {
                'is_approved': is_approved,
                'is_used': is_used,
                'is_checked_out': is_checked_out,  # New field
                'is_expired': is_expired_status,
                'is_valid': is_valid,
                'is_pending': is_pending,
                'is_declined': is_declined,
                'is_not_yet_valid': is_not_yet_valid,
                'is_past_valid': is_past_valid,
                'is_within_window': is_within_window,
                'status_message': status_message
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        traceback.print_exc()
        return Response(
            {
                'valid': False,
                'error': f'Error processing PIN verification: {str(e)}',
                'traceback': traceback.format_exc() if settings.DEBUG else None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class MaintenanceProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing maintenance providers
    
    Permissions:
    - GET (list, retrieve): All authenticated users can view approved providers
    - POST/PUT/PATCH/DELETE: Only admins can manage providers
    """
    serializer_class = MaintenanceProviderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter providers based on user role:
        - All users see approved and active providers
        - Admins see all providers (including unapproved/inactive)
        - Filter by maintenance_type if provided
        """
        user = self.request.user
        maintenance_type = self.request.query_params.get('maintenance_type', None)
        
        if user.is_staff:
            # Admin can see all providers
            queryset = MaintenanceProvider.objects.all()
        else:
            # Regular users see only approved and active providers
            queryset = MaintenanceProvider.objects.filter(is_approved=True, is_active=True)
        
        # Filter by maintenance type if provided
        if maintenance_type:
            # Search in services field (comma-separated)
            queryset = queryset.filter(services__icontains=maintenance_type)
        
        return queryset.order_by('-is_approved', '-is_active', 'name')
    
    def get_permissions(self):
        """
        Allow all authenticated users to view (GET, LIST),
        but only admins can create, update, or delete.
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]
    
    def perform_create(self, serializer):
        """Set created_by when creating a provider"""
        serializer.save(created_by=self.request.user)


# ==================== GUARD ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def guard_login(request):
    """Guard login endpoint - returns token"""
    from django.contrib.auth import authenticate
    from rest_framework.authtoken.models import Token
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user and (user.is_staff or user.groups.filter(name='Guard').exists()):
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'is_guard': True
            }
        })
    
    return Response({'error': 'Invalid credentials or not authorized as guard'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guard_walk_in(request):
    """Register walk-in visitor"""
    from .models import Visitor
    from .serializers import VisitorSerializer
    
    try:
        visitor = Visitor.objects.create(
            name=request.data.get('name'),
            gmail=request.data.get('gmail', ''),
            contact_number=request.data.get('contact_number'),
            address=request.data.get('address'),
            homeowner_name=request.data.get('homeowner_name'),
            reason=request.data.get('reason'),
            status='approved',
            time_in=timezone.now()
        )
        return Response(VisitorSerializer(visitor).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def guard_active_visitors(request):
    """Get all currently active visitors"""
    from .models import Visitor, VisitorRequest
    from .serializers import VisitorSerializer, VisitorRequestSerializer
    
    # Walk-in visitors (no checkout time)
    walk_ins = Visitor.objects.filter(time_out__isnull=True, time_in__isnull=False)
    
    # Scheduled visitors (PIN verified, not checked out)
    scheduled = VisitorRequest.objects.filter(
        pin_entered_at__isnull=False,
        status='approved'
    ).exclude(
        visitor_record__time_out__isnull=False
    )
    
    return Response({
        'walk_ins': VisitorSerializer(walk_ins, many=True).data,
        'scheduled': VisitorRequestSerializer(scheduled, many=True, context={'request': request}).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guard_checkin_pin(request, request_id):
    """Check in visitor with verified PIN"""
    from .models import Visitor, VisitorRequest
    
    try:
        visitor_request = VisitorRequest.objects.get(id=request_id)
        visitor_request.pin_entered_at = timezone.now()
        visitor_request.save()
        
        # Create or update visitor record
        if not visitor_request.visitor_record:
            visitor = Visitor.objects.create(
                name=visitor_request.visitor_name,
                gmail=visitor_request.visitor_email,
                contact_number=visitor_request.visitor_contact_number,
                reason=visitor_request.reason or 'Scheduled visit',
                status='approved',
                time_in=timezone.now()
            )
            visitor_request.visitor_record = visitor
            visitor_request.save()
        
        return Response({'message': 'Visitor checked in successfully'})
    except VisitorRequest.DoesNotExist:
        return Response({'error': 'Visitor request not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guard_checkout(request, visitor_id):
    """Checkout visitor"""
    from .models import Visitor, VisitorRequest
    
    visitor_type = request.query_params.get('type', 'walkin')
    
    try:
        if visitor_type == 'walkin':
            visitor = Visitor.objects.get(id=visitor_id)
            visitor.time_out = timezone.now()
            visitor.save()
        else:  # scheduled
            visitor_request = VisitorRequest.objects.get(id=visitor_id)
            if visitor_request.visitor_record:
                visitor_request.visitor_record.time_out = timezone.now()
                visitor_request.visitor_record.save()
        
        return Response({'message': 'Visitor checked out successfully'})
    except (Visitor.DoesNotExist, VisitorRequest.DoesNotExist):
        return Response({'error': 'Visitor not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

