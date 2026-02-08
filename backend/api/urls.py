from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    BookingViewSet, FacilityViewSet, HouseDetailView, VisitorViewSet, admin_user_bills, delete_billing, password_reset_confirm, pending_visitors, register, get_posts, get_user_posts, get_user_profile, admin_change_user_password, admin_update_user, 
    message_list_create, send_email, subdivision_list_create, subdivision_detail, PinViewSet,
    SubdivisionViewSet, update_user_profile, ChangePasswordView,
    admin_user_list, admin_user_delete, admin_user_update, admin_user_detail,
    admin_dashboard_stats, admin_pin_stats,
    NewsViewSet, AlertViewSet, ContactInfoViewSet, ContactMessageViewSet, password_reset_request, visitor_approval,
    AvailableSlotViewSet, MaintenanceViewSet, ReviewViewSet, admin_create_user, BulletinViewSet
)
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserHistoryListView, my_resident_pin, visitor_checkin, visitor_checkout, ResidentPinViewSet, ResidentApprovalViewSet, visitor_timeout, VisitorTrackingViewSet, HouseListCreateView, HouseViewSet, GuestHouseListView, GuestHouseDetailView, ReviewViewSet, FAQViewSet, ServiceFeeViewSet, BlogCommentViewSet, BulletinCommentViewSet, CommunityMediaViewSet, VisitorRequestViewSet, MaintenanceRequestViewSet, MaintenanceProviderViewSet, EmergencyContactViewSet, verify_pin_view, guard_login, guard_walk_in, guard_active_visitors, guard_checkin_pin, guard_checkout
from .paymongo_views import (
    create_payment,
    check_transaction_status,
    paymongo_webhook,
    get_user_transactions
)
from . import simple_webhook


router = DefaultRouter()
router.register(r'pins', PinViewSet, basename='pin')
router.register(r'url', PinViewSet, basename='pins-legacy')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'subdivisions', SubdivisionViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'available-slots', AvailableSlotViewSet, basename='available-slot')
router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')
router.register(r'news', NewsViewSet, basename='news')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'contact-info', ContactInfoViewSet, basename='contact-info')
router.register(r'contact-messages', ContactMessageViewSet, basename='contact-message')
router.register(r'emergency-contacts', EmergencyContactViewSet, basename='emergency-contact')
router.register(r'visitor', VisitorViewSet, basename='visitor')
router.register(r'resident-pin', ResidentPinViewSet, basename='resident-pin')
router.register(r'residents', ResidentApprovalViewSet, basename='residents')
router.register(r'admin/visitors', VisitorTrackingViewSet, basename='admin-visitors')
router.register(r'houses', HouseViewSet, basename='houses')
router.register(r'faq', FAQViewSet, basename='faq')
router.register(r'service-fees', ServiceFeeViewSet, basename='service-fees')
router.register(r'blog-comments', BlogCommentViewSet, basename='blog-comment')
router.register(r'bulletin-comments', BulletinCommentViewSet, basename='bulletin-comment')
router.register(r'bulletins', BulletinViewSet, basename='bulletin')
router.register(r'community-media', CommunityMediaViewSet, basename='community-media')
router.register(r'visitor-requests', VisitorRequestViewSet, basename='visitor-request')
router.register(r'maintenance-requests', MaintenanceRequestViewSet, basename='maintenance-request')
router.register(r'maintenance-providers', MaintenanceProviderViewSet, basename='maintenance-provider')

urlpatterns = [
    path('register/', register),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('visitor-requests/verify_pin/', views.verify_pin_view, name='verify-pin'),
    path('posts/', get_posts),
    path('posts/<int:pk>/', views.post_detail, name='post-detail'),
    path('myposts/', get_user_posts),
    path('profile/', get_user_profile),
    path('profile/update/', update_user_profile),
    path("resident-pin/my/", my_resident_pin, name="my_resident_pin"),
    path("visitor/checkin/", visitor_checkin, name="visitor_checkin"),
    path("visitor/checkout/<int:visitor_id>/", visitor_checkout, name="visitor_checkout"),
    path("visitor/pending/", pending_visitors, name="pending_visitors"),
    path("visitor/approval/<int:visitor_id>/", visitor_approval, name="visitor_approval"),
    path('visitor/checkin/', views.visitor_checkin, name='visitor-checkin'),
    path('visitor/checkout/<int:visitor_id>/', views.visitor_checkout),
    path('visitor/approval/<int:visitor_id>/', views.visitor_approval),
    path('visitors/', views.all_visitors, name='visitors-all'), 
    path('visitor/status/', views.visitor_status),
    path('visitor/guest-status/', views.guest_visitor_status, name='guest-visitor-status'),
    path('visitor/guest-checkin/', views.guest_visitor_checkin, name='guest-visitor-checkin'),
    path('resident/visitors/', views.resident_visitors, name='resident-visitors'),
    path("visitor/timeout/<int:pk>/", visitor_timeout, name="visitor-timeout"),
    path("houses/", HouseListCreateView.as_view(), name="house-list-create"),
    path("house/<int:pk>/", HouseDetailView.as_view()),
    path("guest/houses/", GuestHouseListView.as_view()),
    path("guest/houses/<int:pk>/", GuestHouseDetailView.as_view()),
    path('profile/upload-billing/', views.upload_billing, name='upload-billing'),
    path('admin/user-bills/', views.admin_user_bills, name='admin-user-bills'),
    path("api/admin/users/<int:user_id>/delete-billing/", delete_billing),
    path('api/admin/users/', admin_user_bills, name='admin-user-bills'),  # GET list users with bills
    path('api/admin/users/<int:user_id>/delete-billing/', delete_billing, name='delete-billing'),
    path('profile/delete-billing/', delete_billing, name='delete-billing'),
    path('admin/users/<int:user_id>/update/', admin_update_user, name='admin-update-user'),
    path('admin/users/<int:user_id>/change-password/', admin_change_user_password, name='admin-change-password'),

    
 
    # ✅ Admin user management
    path('admin/users/', admin_user_list, name='admin_user_list'),
    path('admin/users/create/', admin_create_user, name='admin_create_user'),
    path('admin/users/<int:user_id>/delete/', admin_user_delete, name='admin_user_delete'),
    path('admin/users/<int:user_id>/update/', admin_user_update, name='admin_user_update'),
    path('admin/users/<int:pk>/', admin_user_detail, name='admin_user_detail'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('notifications/send-email/', send_email, name='send_email'),
    # ✅ Dashboard & pins stats
    path('admin/dashboard-stats/', admin_dashboard_stats, name='admin_dashboard_stats'),
    path('admin/pin-stats/', admin_pin_stats, name='admin_pin_stats'),
        
    # ✅ Password reset
    path('password-reset/', password_reset_request, name='password_reset'),
    path('password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),
    path('user-history/', UserHistoryListView.as_view(), name='user-history'),
    path('profile/upload-document/', views.upload_document, name='upload_document'),
    path('admin/pending-verifications/', views.pending_verifications),
    path('admin/verify-user/<int:user_id>/', views.verify_user),
    path('admin/reject-user/<int:user_id>/', views.reject_user),

    path('send_verification_email/', views.send_verification_email, name='send_verification_email'),
    path('verify_email_code/', views.verify_email_code, name='verify_email_code'),
    
    # PayMongo Payment Integration (QRPh/GCash/E-Wallet)
    path('service-fees/<int:service_fee_id>/paymongo-payment/', create_payment, name='create-payment'),
    path('paymongo/transaction/<int:transaction_id>/status/', check_transaction_status, name='check-transaction-status'),
    path('paymongo/webhook/', paymongo_webhook, name='paymongo-webhook'),
    path('paymongo/transactions/', get_user_transactions, name='get-user-transactions'),
    
    # Simple Payment Link Webhook
    path('webhook/payment/', simple_webhook.payment_webhook, name='payment-webhook'),
    
    # Guard Endpoints
    path('guard-login/', guard_login, name='guard-login'),
    path('guard/walk-in/', guard_walk_in, name='guard-walk-in'),
    path('guard/active-visitors/', guard_active_visitors, name='guard-active-visitors'),
    path('guard/checkin-pin/<int:request_id>/', guard_checkin_pin, name='guard-checkin-pin'),
    path('guard/checkout/<int:visitor_id>/', guard_checkout, name='guard-checkout'),
    
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# from django.urls import path, include
# from flask import views
# from rest_framework.routers import DefaultRouter
# from .views import (
#     BookingViewSet, FacilityViewSet, password_reset_confirm, register, get_posts, get_user_posts, get_user_profile,
#     message_list_create, subdivision_list_create, subdivision_detail, PinViewSet,
#     SubdivisionViewSet, update_user_profile, ChangePasswordView,
#     admin_user_list, admin_user_delete, admin_user_update, admin_user_detail,
#     admin_dashboard_stats, admin_pin_stats,
#     NewsViewSet, AlertViewSet, ContactInfoViewSet, ContactMessageViewSet, password_reset_request, password_reset_confirm
# )
# from django.conf import settings
# from django.conf.urls.static import static
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



# router = DefaultRouter()
# router.register(r'pins', PinViewSet, basename='pin')
# # Legacy route kept for backward compatibility with existing frontend calls
# router.register(r'url', PinViewSet, basename='pins-legacy')
# router.register(r'subdivisions', SubdivisionViewSet)
# router.register(r'bookings', BookingViewSet, basename='booking')
# router.register(r'facilities', FacilityViewSet, basename='facility')
# router.register(r'news', NewsViewSet, basename='news')
# router.register(r'alerts', AlertViewSet, basename='alert')
# router.register(r'contact-info', ContactInfoViewSet, basename='contact-info')
# router.register(r'contact-messages', ContactMessageViewSet, basename='contact-message')

# urlpatterns = [
#     path('register/', register),
#     path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('posts/', get_posts),
#     path('myposts/', get_user_posts),
#     path('profile/', get_user_profile),
#     path('profile/update/', update_user_profile),
#     path('messages/', message_list_create),
#     path('subdivisions/', subdivision_list_create),
#     path('subdivisions/<int:pk>/', subdivision_detail),
#     path('user/', get_user_profile, name='get_user_profile'),
#     path('user/update/', update_user_profile, name='update_user_profile'),

#     # ✅ Admin user management endpoints
#     path('admin/users/', admin_user_list, name='admin_user_list'),
#     path('admin/users/<int:user_id>/delete/', admin_user_delete, name='admin_user_delete'),
#     path('admin/users/<int:user_id>/update/', admin_user_update, name='admin_user_update'),
#     path('admin/users/<int:pk>/', admin_user_detail, name='admin_user_detail'),

#     # ✅ New change password endpoint
#     path('change-password/', ChangePasswordView.as_view(), name='change-password'),

#     # ✅ Dashboard statistics endpoint
#     path('admin/dashboard-stats/', admin_dashboard_stats, name='admin_dashboard_stats'),
#     # ✅ Pin statistics endpoint
#     path('admin/pin-stats/', admin_pin_stats, name='admin_pin_stats'),
#     path('password-reset/', password_reset_request, name='password_reset'),
#     path('password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),
#     path('admin/users/<int:id>/update/', views.update_user, name='update_user'),
#     path('admin/users/<int:id>/delete/', views.delete_user, name='delete_user'),
#     path('', include(router.urls)),
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
