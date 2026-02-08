from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Billing, Post, Message, Subdivision, Pin, UserProfile, Booking, Facility, AvailableSlot, Maintenance, MaintenanceRequest, MaintenanceProvider, News, Alert, ContactInfo, ContactMessage, EmergencyContact, Review, House, HouseImage, FAQ, ServiceFee, BlogComment, Bulletin, BulletinComment, CommunityMedia, VisitorRequest
from simple_history.models import HistoricalRecords


class PostSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = '__all__'
        extra_kwargs = {
            'image': {'required': False, 'allow_null': True}
        }
    
    def get_image_url(self, obj):
        """Return full URL for the image if it exists"""
        try:
            if obj.image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return obj.image.url
        except (AttributeError, ValueError):
            pass
        return None


class BlogCommentSerializer(serializers.ModelSerializer):
    """Serializer for blog comments"""
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_admin = serializers.SerializerMethodField()
    post_title = serializers.CharField(source='post.title', read_only=True)
    user_profile_image = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogComment
        fields = [
            'id', 'post', 'post_title', 'user', 'user_id', 'username', 
            'is_admin', 'user_profile_image', 'content', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_is_admin(self, obj):
        """Check if the commenter is an admin/staff"""
        return obj.user.is_staff
    
    def get_user_profile_image(self, obj):
        """Get the profile image URL for the commenter"""
        if hasattr(obj.user, 'profile') and obj.user.profile.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile.profile_image.url)
            return obj.user.profile.profile_image.url
        return None


class CommunityMediaSerializer(serializers.ModelSerializer):
    """Serializer for Community Media (Gallery)"""
    media_url = serializers.SerializerMethodField()
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    uploaded_by_id = serializers.IntegerField(source='uploaded_by.id', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = CommunityMedia
        fields = [
            'id', 'title', 'description', 'media_file', 'media_url', 'media_type', 'category',
            'uploaded_by', 'uploaded_by_id', 'uploaded_by_username',
            'approved_by', 'approved_by_username',
            'is_approved', 'is_featured', 'is_public',
            'views_count', 'likes_count', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['uploaded_by', 'approved_by', 'views_count', 'likes_count', 'created_at', 'updated_at']
    
    def get_media_url(self, obj):
        """Get the full URL for the media file"""
        if obj.media_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.media_file.url)
            return obj.media_file.url
        return None


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class SubdivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subdivision
        fields = ['id', 'lot_number', 'is_occupied', 'owner_name']


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_profile_image = serializers.SerializerMethodField()
    pin_name = serializers.CharField(source='pin.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'pin', 'pin_name', 'user', 'user_name', 'user_profile_image',
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_user_profile_image(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile.profile_image.url)
            return obj.user.profile.profile_image.url
        return None


class PinSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Pin
        fields = [
            'id',
            'name',
            'latitude',
            'longitude',
            'occupant',
            'status',
            'price',
            'description',
            'square_meter',
            'image',
            'average_rating',
            'review_count',
        ]

    def get_average_rating(self, obj):
        return obj.get_average_rating()

    def get_review_count(self, obj):
        return obj.get_review_count()

class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    billing_records = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['profile_image', 'contact_number', 'is_verified', 'document', 'billing_records']

    def get_profile_image(self, obj):
        try:
            request = self.context.get('request')
            if obj and obj.profile_image:
                return request.build_absolute_uri(obj.profile_image.url) if request else obj.profile_image.url
        except Exception:
            pass
        return None

    def get_document(self, obj):
        try:
            request = self.context.get('request')
            if obj and obj.document:
                return request.build_absolute_uri(obj.document.url) if request else obj.document.url
        except Exception:
            pass
        return None

    def get_billing_records(self, obj):
        try:
            request = self.context.get('request')
            if obj:
                return [request.build_absolute_uri(b.file.url) if request else b.file.url for b in obj.billing_records.all()]
        except Exception:
            pass
        return []


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'profile']
    
    def get_profile(self, obj):
        """Safely get user profile, create if doesn't exist"""
        try:
            if hasattr(obj, 'profile'):
                return UserProfileSerializer(obj.profile, context=self.context).data
            else:
                # Create profile if it doesn't exist
                profile = UserProfile.objects.create(user=obj)
                return UserProfileSerializer(profile, context=self.context).data
        except Exception as e:
            # Return default profile data if error
            return {
                'profile_image': None,
                'contact_number': '',
                'is_verified': False,
                'document': None,
                'billing_records': []
            }

class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ['id', 'name']

class BookingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    facility_name = serializers.SerializerMethodField(read_only=True)
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source='facility',
        write_only=True
    )
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H:%M:%S'])
    end_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H:%M:%S'])
    status = serializers.CharField(required=False)  # Make status writable

    class Meta:
        model = Booking
        fields = [
            'id', 'user_name', 'facility_name', 'facility_id',
            'date', 'start_time', 'end_time', 'status'
        ]
        read_only_fields = ['id', 'facility_name']
    
    def validate_status(self, value):
        """Validate status value - only allow admins to change it"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Only admins can set status
            if not request.user.is_staff:
                # For non-admins, status should remain as is (read-only)
                return None  # Return None to keep existing value
            # Validate status value for admins
            valid_statuses = ['pending', 'approved', 'rejected']
            if value and value not in valid_statuses:
                raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
    
    def update(self, instance, validated_data):
        """Override update to handle status updates for admins"""
        request = self.context.get('request')
        # Only allow admins to update status
        if request and hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
            status_value = validated_data.pop('status', None)
            if status_value:
                instance.status = status_value
        # Update other fields
        return super().update(instance, validated_data)
    
    def validate_start_time(self, value):
        """Ensure start_time is a valid time"""
        if value is None:
            raise serializers.ValidationError("Start time is required.")
        return value
    
    def validate_end_time(self, value):
        """Ensure end_time is a valid time"""
        if value is None:
            raise serializers.ValidationError("End time is required.")
        return value
    
    def get_facility_name(self, obj):
        """Safely get facility display name"""
        if not obj:
            return "Unknown Facility"
        
        try:
            # Get facility_id first
            facility_id = None
            if hasattr(obj, 'facility_id'):
                facility_id = obj.facility_id
            elif hasattr(obj, 'facility') and obj.facility:
                facility_id = obj.facility.id if hasattr(obj.facility, 'id') else None
            
            if not facility_id:
                return "Unknown Facility"
            
            # Try to get facility from loaded relationship first
            if hasattr(obj, 'facility') and obj.facility is not None:
                try:
                    if hasattr(obj.facility, 'get_name_display'):
                        return obj.facility.get_name_display()
                    elif hasattr(obj.facility, 'name'):
                        return obj.facility.name
                except (AttributeError, TypeError, ValueError) as e:
                    pass
            
            # If not loaded, fetch from database
            try:
                facility = Facility.objects.get(id=facility_id)
                if hasattr(facility, 'get_name_display'):
                    return facility.get_name_display()
                elif hasattr(facility, 'name'):
                    return facility.name
            except (Facility.DoesNotExist, ValueError, TypeError):
                return "Unknown Facility"
        except Exception as e:
            # Silently fail and return default
            import traceback
            print(f"Error in get_facility_name: {e}")
            print(traceback.format_exc())
        
        return "Unknown Facility"
    
    def to_representation(self, instance):
        """Override to ensure facility is loaded before serialization"""
        if instance and hasattr(instance, 'facility_id') and instance.facility_id:
            if not hasattr(instance, '_facility_loaded'):
                try:
                    # Try to get facility from the instance first
                    if not hasattr(instance, 'facility') or instance.facility is None:
                        instance.facility = Facility.objects.get(id=instance.facility_id)
                    instance._facility_loaded = True
                except (Facility.DoesNotExist, AttributeError, ValueError, TypeError):
                    pass
        try:
            return super().to_representation(instance)
        except Exception as e:
            import traceback
            print(f"[ERROR] Error in to_representation: {e}")
            print(traceback.format_exc())
            # Return minimal representation
            return {
                'id': getattr(instance, 'id', None),
                'facility_id': getattr(instance, 'facility_id', None),
                'facility_name': 'Unknown Facility',
                'date': str(getattr(instance, 'date', '')),
                'start_time': str(getattr(instance, 'start_time', '')),
                'end_time': str(getattr(instance, 'end_time', '')),
                'status': getattr(instance, 'status', 'pending'),
                'user_name': getattr(instance.user, 'username', 'Unknown') if hasattr(instance, 'user') else 'Unknown',
            }

class AvailableSlotSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source='facility.get_name_display', read_only=True)
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source='facility',
        write_only=True
    )

    class Meta:
        model = AvailableSlot
        fields = [
            'id', 'facility_id', 'facility_name',
            'date', 'start_time', 'end_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class MaintenanceSerializer(serializers.ModelSerializer):
    facility_name = serializers.SerializerMethodField(read_only=True)
    facility_id = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(),
        source='facility',
        write_only=True
    )

    def get_facility_name(self, obj):
        if obj.facility:
            return obj.facility.get_name_display()
        return None

    class Meta:
        model = Maintenance
        fields = [
            'id', 'facility_id', 'facility_name',
            'start_date', 'end_date', 'start_time', 'end_time', 
            'reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class MaintenanceRequestSerializer(serializers.ModelSerializer):
    homeowner_name = serializers.SerializerMethodField()
    homeowner_email = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    def get_homeowner_name(self, obj):
        if obj.homeowner.first_name and obj.homeowner.last_name:
            return f"{obj.homeowner.first_name} {obj.homeowner.last_name}"
        return obj.homeowner.username
    
    def get_homeowner_email(self, obj):
        return obj.homeowner.email
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            if obj.approved_by.first_name and obj.approved_by.last_name:
                return f"{obj.approved_by.first_name} {obj.approved_by.last_name}"
            return obj.approved_by.username
        return None
    
    class Meta:
        model = MaintenanceRequest
        fields = [
            'id', 'homeowner', 'homeowner_name', 'homeowner_email',
            'maintenance_type', 'maintenance_type_display',
            'description', 'preferred_date', 'preferred_time',
            'is_urgent', 'use_external_contractor',
            'external_contractor_name', 'external_contractor_contact', 'external_contractor_company',
            'status', 'status_display',
            'approved_by', 'approved_by_name', 'approved_at', 'declined_reason', 'admin_feedback',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['homeowner', 'approved_by', 'approved_at', 'created_at', 'updated_at']


class MaintenanceProviderSerializer(serializers.ModelSerializer):
    """Serializer for Maintenance Provider"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    services_list = serializers.SerializerMethodField()
    
    def get_services_list(self, obj):
        """Return services as a list"""
        return obj.get_services_list()
    
    class Meta:
        model = MaintenanceProvider
        fields = [
            'id', 'name', 'contact_person', 'phone', 'email', 'address',
            'services', 'services_list', 'is_nearby', 'distance',
            'is_approved', 'is_active', 'rating', 'notes',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'is_published', 'created_at']


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ['id', 'title', 'message', 'severity', 'is_active', 'created_at']


class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['id', 'address', 'phone', 'email']


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'is_resolved', 'created_at']


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'name', 'phone', 'description', 'category', 'is_active', 'order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

 



class HistoricalRecordSerializer(serializers.ModelSerializer):
    history_user = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile.history.model
        fields = ['id', 'history_date', 'history_type', 'history_user', 'model_name']

    def get_history_user(self, obj):
        """Safely get the username of the user who made the change"""
        try:
            if obj.history_user:
                return obj.history_user.username
            return 'System'
        except (AttributeError, TypeError):
            return 'System'

    def get_model_name(self, obj):
        """Safely get the model name"""
        try:
            if obj.instance:
                return obj.instance.__class__.__name__
            # Fallback: try to get from the history model
            return obj.__class__.__name__.replace('Historical', '').replace('History', '')
        except (AttributeError, TypeError):
            return 'Unknown'


class VisitorRequestSerializer(serializers.ModelSerializer):
    """Serializer for Visitor Request with one-time PIN"""
    resident_username = serializers.SerializerMethodField()
    resident_email = serializers.SerializerMethodField()
    resident_name = serializers.SerializerMethodField()
    approved_by_username = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VisitorRequest
        fields = [
            'id', 'resident', 'resident_username', 'resident_email', 'resident_name',
            'visitor_name', 'visitor_email', 'visitor_contact_number', 'vehicle_plate_number', 'reason',
            'one_time_pin', 'visit_date', 'visit_end_date', 'visit_start_time', 'visit_end_time',
            'status', 'approved_by', 'approved_by_username', 'approved_at',
            'declined_reason', 'pdf_generated', 'pdf_file_path', 'pdf_url',
            'email_sent', 'email_sent_at', 'visitor_record', 'pin_entered_at', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'resident', 'one_time_pin', 'approved_by', 'approved_at',
            'pdf_generated', 'pdf_file_path', 'email_sent', 'email_sent_at',
            'visitor_record', 'pin_entered_at', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'visitor_record': {'allow_null': True, 'required': False}
        }
    
    def to_representation(self, instance):
        """Override to safely handle visitor_record and other fields"""
        try:
            data = super().to_representation(instance)
            # Ensure visitor_record is safely serialized (can be None)
            # visitor_record is a ForeignKey, so it will be serialized as an ID (integer) or None
            # No need to modify it, just ensure it's handled
            return data
        except Exception as e:
            # If serialization fails, log and return minimal safe data
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            error_msg = f"Serialization error for VisitorRequest {getattr(instance, 'id', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            
            # Return minimal safe representation
            try:
                return {
                    'id': getattr(instance, 'id', None),
                    'visitor_name': getattr(instance, 'visitor_name', ''),
                    'visitor_email': getattr(instance, 'visitor_email', ''),
                    'status': getattr(instance, 'status', ''),
                    'visit_date': str(getattr(instance, 'visit_date', '')) if hasattr(instance, 'visit_date') and instance.visit_date else None,
                    'visit_start_time': str(getattr(instance, 'visit_start_time', '')) if hasattr(instance, 'visit_start_time') and instance.visit_start_time else None,
                    'visit_end_time': str(getattr(instance, 'visit_end_time', '')) if hasattr(instance, 'visit_end_time') and instance.visit_end_time else None,
                    'resident': getattr(instance, 'resident_id', None),
                    'visitor_record': getattr(instance, 'visitor_record_id', None),
                    'one_time_pin': getattr(instance, 'one_time_pin', None),
                    'created_at': str(getattr(instance, 'created_at', '')) if hasattr(instance, 'created_at') and instance.created_at else None,
                    'error': 'Partial data due to serialization error'
                }
            except Exception as fallback_error:
                logger.error(f"Fallback serialization also failed: {fallback_error}")
                return {
                    'id': getattr(instance, 'id', None),
                    'error': 'Serialization failed'
                }
    
    def get_resident_username(self, obj):
        """Get resident username"""
        try:
            return obj.resident.username if obj.resident else None
        except Exception:
            return None
    
    def get_resident_email(self, obj):
        """Get resident email"""
        try:
            return obj.resident.email if obj.resident else None
        except Exception:
            return None
    
    def get_resident_name(self, obj):
        """Get full name of resident"""
        try:
            if not obj.resident:
                return 'Unknown'
            if obj.resident.first_name and obj.resident.last_name:
                return f"{obj.resident.first_name} {obj.resident.last_name}"
            return obj.resident.username or 'Unknown'
        except Exception:
            return 'Unknown'
    
    def get_approved_by_username(self, obj):
        """Get approved by username"""
        try:
            return obj.approved_by.username if obj.approved_by else None
        except Exception:
            return None
    
    def get_is_valid(self, obj):
        """Check if PIN is currently valid"""
        try:
            return obj.is_valid()
        except Exception:
            # Return False if validation fails (e.g., missing date/time fields)
            return False
    
    def get_pdf_url(self, obj):
        """Get URL to PDF file via action endpoint (ensures proper PDF headers)"""
        try:
            if not obj:
                return None
                
            if obj.pdf_file_path or obj.pdf_generated:
                request = self.context.get('request') if self.context else None
                if request and hasattr(request, 'build_absolute_uri'):
                    try:
                        # Use the action endpoint instead of direct file URL
                        # This ensures proper Content-Type headers are set
                        return request.build_absolute_uri(f'/api/visitor-requests/{obj.id}/pdf/')
                    except Exception:
                        pass
                
                # Fallback to direct URL if no request context
                if obj.pdf_file_path:
                    try:
                        if hasattr(obj.pdf_file_path, 'url'):
                            return obj.pdf_file_path.url
                    except (AttributeError, ValueError, TypeError):
                        pass
            return None
        except Exception as e:
            # Silently fail - PDF URL is optional
            return None
    

class UserProfileAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['contact_number', 'is_verified', 'document', 'profile_image']

class UserAdminSerializer(serializers.ModelSerializer):
    profile = UserProfileAdminSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']

from .models import ResidentPin, Visitor

class ResidentPinSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)  # add username

    class Meta:
        model = ResidentPin
        fields = ["id", "pin", "username"]  # include username

class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = [
            'id', 'name', 'gmail', 'contact_number', 'reason', 'pin_entered', 'resident', 'status', 'time_in', 'time_out'
        ]

class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name']


class HouseImageSerializer(serializers.ModelSerializer):
    """Serializer for house images"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = HouseImage
        fields = ['id', 'image', 'image_url', 'order', 'created_at']
        read_only_fields = ['created_at']
    
    def get_image_url(self, obj):
        """Get the full URL for the image"""
        if obj.image:
            request = self.context.get('request')
            try:
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return obj.image.url
            except Exception as e:
                print(f"[WARNING] Failed to build image URL: {e}")
                return obj.image.url if obj.image else None
        return None


class HouseSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)
    image = serializers.ImageField(use_url=True, required=False, allow_null=True)  # Keep for backward compatibility
    images = serializers.SerializerMethodField()  # Use SerializerMethodField to handle missing relation (read-only)
    image_urls = serializers.SerializerMethodField()  # Convenience field for frontend

    class Meta:
        model = House
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'images']  # images is read-only, handled separately in views
    
    def get_images(self, obj):
        """Safely get images relation - ALWAYS query database to ensure we get images"""
        try:
            if not hasattr(obj, 'images'):
                print(f"[SERIALIZER] House {obj.pk} has no 'images' attribute")
                return []
            
            # ALWAYS query directly from database to ensure we get the latest images
            # Don't rely on prefetch cache which might be stale
            from .models import HouseImage
            try:
                images_list = list(HouseImage.objects.filter(house_id=obj.pk).order_by('order', 'created_at'))
                print(f"[SERIALIZER] House {obj.pk} - Queried {len(images_list)} images from database")
                
                if images_list:
                    serialized = HouseImageSerializer(images_list, many=True, context=self.context).data
                    print(f"[SERIALIZER] House {obj.pk} - Serialized {len(serialized)} images")
                    return serialized
                else:
                    print(f"[SERIALIZER] House {obj.pk} - No images found in database")
            except Exception as e:
                print(f"[ERROR] Error querying images for house {obj.pk}: {e}")
                import traceback
                print(traceback.format_exc())
        except Exception as e:
            print(f"[ERROR] Error in get_images for house {obj.pk if hasattr(obj, 'pk') else 'unknown'}: {e}")
        return []
    
    def get_image_urls(self, obj):
        """Get list of image URLs for easy frontend access - ALWAYS query database"""
        request = self.context.get('request')
        image_urls = []
        
        # ALWAYS query directly from database to ensure we get the latest images
        try:
            from .models import HouseImage
            # Query directly using house_id to avoid any relationship cache issues
            images_list = list(HouseImage.objects.filter(house_id=obj.pk).order_by('order', 'created_at'))
            print(f"[SERIALIZER] get_image_urls - House {obj.pk}: Found {len(images_list)} images in database")
            
            for house_image in images_list:
                if house_image and house_image.image:
                    try:
                        image_url = house_image.image.url
                        if request:
                            full_url = request.build_absolute_uri(image_url)
                            image_urls.append(full_url)
                            print(f"[SERIALIZER] Added image URL: {full_url}")
                        else:
                            image_urls.append(image_url)
                    except Exception as e:
                        print(f"[ERROR] Failed to get image URL for HouseImage {house_image.id}: {e}")
        except Exception as e:
            print(f"[ERROR] Error in get_image_urls for house {obj.pk}: {e}")
            import traceback
            print(traceback.format_exc())
        
        # Include the main image if it exists (for backward compatibility) - only if no images found
        if len(image_urls) == 0 and hasattr(obj, 'image') and obj.image:
            try:
                if request:
                    image_urls.append(request.build_absolute_uri(obj.image.url))
                else:
                    image_urls.append(obj.image.url)
            except Exception:
                pass
        
        print(f"[SERIALIZER] get_image_urls - House {obj.pk}: Returning {len(image_urls)} image URLs")
        return image_urls

# serializers.py
class BillingUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['billing']


class BillingSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = Billing
        fields = ['id', 'file', 'uploaded_at']

    def get_file(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        elif obj.file:
            return obj.file.url
        return None
class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ServiceFeeSerializer(serializers.ModelSerializer):
    bill_image_url = serializers.SerializerMethodField()
    receipt_image_url = serializers.SerializerMethodField()
    policy_image_url = serializers.SerializerMethodField()
    homeowner_name = serializers.CharField(source='homeowner.username', read_only=True)
    homeowner_email = serializers.CharField(source='homeowner.email', read_only=True)
    homeowner_id = serializers.IntegerField(source='homeowner.id', read_only=True)
    has_paymongo_transaction = serializers.SerializerMethodField()
    latest_transaction = serializers.SerializerMethodField()

    class Meta:
        model = ServiceFee
        fields = [
            'id', 'homeowner', 'homeowner_id', 'homeowner_name', 'homeowner_email',
            'bill_image', 'receipt_image', 'policy_image',
            'bill_image_url', 'receipt_image_url', 'policy_image_url',
            'amount', 'due_date', 'status', 'month', 'year', 
            'notes', 'has_paymongo_transaction', 'latest_transaction',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'homeowner_id', 'homeowner_name', 'homeowner_email']

    def get_bill_image_url(self, obj):
        request = self.context.get('request')
        if obj.bill_image:
            return request.build_absolute_uri(obj.bill_image.url) if request else obj.bill_image.url
        return None

    def get_receipt_image_url(self, obj):
        request = self.context.get('request')
        if obj.receipt_image:
            return request.build_absolute_uri(obj.receipt_image.url) if request else obj.receipt_image.url
        return None

    def get_policy_image_url(self, obj):
        request = self.context.get('request')
        if obj.policy_image:
            return request.build_absolute_uri(obj.policy_image.url) if request else obj.policy_image.url
        return None
    
    def get_has_paymongo_transaction(self, obj):
        """Check if this service fee has any PayMongo transactions"""
        try:
            return obj.paymongo_transactions.exists()
        except:
            return False
    
    def get_latest_transaction(self, obj):
        """Get payment link info with auto-overdue check"""
        try:
            # Auto-check if overdue
            obj.check_if_overdue()
            
            if hasattr(obj, 'payment_link'):
                link = obj.payment_link
                return {
                    'reference_number': link.reference_number,
                    'checkout_url': link.checkout_url,
                    'amount': float(link.amount),
                    'paid': link.paid,
                    'paid_at': link.paid_at,
                    'status_icon': obj.get_status_display_with_icon(),
                    'created_at': link.created_at
                }
        except Exception as e:
            print(f"Error getting transaction: {e}")
            pass
        return None

    def to_representation(self, instance):
        """Override to return full URLs in bill_image, receipt_image, policy_image fields"""
        representation = super().to_representation(instance)
        # Replace the file field values with full URLs
        bill_url = representation.get('bill_image_url')
        receipt_url = representation.get('receipt_image_url')
        policy_url = representation.get('policy_image_url')
        
        if bill_url:
            representation['bill_image'] = bill_url
        elif not representation.get('bill_image'):
            representation['bill_image'] = None
            
        if receipt_url:
            representation['receipt_image'] = receipt_url
        elif not representation.get('receipt_image'):
            representation['receipt_image'] = None
            
        if policy_url:
            representation['policy_image'] = policy_url
        elif not representation.get('policy_image'):
            representation['policy_image'] = None
        
        # Remove the _url fields from the response
        representation.pop('bill_image_url', None)
        representation.pop('receipt_image_url', None)
        representation.pop('policy_image_url', None)
        return representation


class BulletinCommentSerializer(serializers.ModelSerializer):
    """Serializer for bulletin comments"""
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_admin = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    bulletin_title = serializers.CharField(source='bulletin.title', read_only=True)
    
    class Meta:
        model = BulletinComment
        fields = [
            'id', 'bulletin', 'bulletin_title', 'user', 'user_id', 'username', 
            'is_admin', 'is_verified', 'content', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_is_admin(self, obj):
        """Check if the commenter is an admin/staff"""
        return obj.user.is_staff
    
    def get_is_verified(self, obj):
        """Check if the commenter is verified"""
        if hasattr(obj.user, 'profile'):
            return obj.user.profile.is_verified
        return False


class BulletinSerializer(serializers.ModelSerializer):
    created_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Bulletin
        fields = ['id', 'title', 'content', 'is_published', 'created_by', 'created_by_username', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_created_by_username(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return None        
                

     
# class VisitorSerializer(serializers.ModelSerializer):
#     resident = ResidentPinSerializer(read_only=True)  # nested serializer

#     class Meta:
#         model = Visitor
#         fields = ["id", "name", "pin_entered", "resident", "time_in", "time_out", "status"]
#         read_only_fields = ["time_in", "time_out", "resident", "status"]

# class FacilitySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Facility
#         fields = ['id', 'name']

# class BookingSerializer(serializers.ModelSerializer):
#     facility_name = serializers.CharField(source='facility.name', read_only=True)
#     facility_id = serializers.PrimaryKeyRelatedField(
#         queryset=Facility.objects.all(),
#         source='facility',
#         write_only=True
#     )

#     class Meta:
#         model = Booking
#         fields = ['id', 'user', 'facility', 'facility_id', 'facility_name', 'date', 'start_time', 'end_time', 'created_at']
#         read_only_fields = ['user', 'facility', 'facility_name', 'created_at']


