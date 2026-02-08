from django.db import models
from django.contrib.auth.models import User
from rest_framework import serializers
from simple_history.models import HistoricalRecords
import random
from django.core.mail import send_mail

def user_profile_path(instance, filename):
    return f'profile_images/user_{instance.user.id}/{filename}'

def billing_path(instance, filename):
    return f'billing/user_{instance.user.id}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_image = models.ImageField(upload_to=user_profile_path, blank=True, null=True)
    contact_number = models.CharField(max_length=14, blank=True, null=True)  # +63XXXXXXXXX
    is_verified = models.BooleanField(default=False)  # ✅ New field
    document = models.FileField(upload_to='documents/', blank=True, null=True)
    billing = models.FileField(upload_to='billing/', blank=True, null=True)  # ✅ Uploaded document
    history = HistoricalRecords()

    def __str__(self):
        return self.user.username


# --- signals ---
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Post(models.Model):
    title = models.CharField(max_length=100)
    body = models.TextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.title


class Bulletin(models.Model):
    """Bulletin Board model for community announcements"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bulletins')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bulletin"
        verbose_name_plural = "Bulletins"

    def __str__(self):
        return self.title


class BulletinComment(models.Model):
    """Comment model for bulletin posts"""
    bulletin = models.ForeignKey(Bulletin, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulletin_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']  # Newest comments first
        verbose_name = "Bulletin Comment"
        verbose_name_plural = "Bulletin Comments"

    def __str__(self):
        return f"{self.user.username} commented on '{self.bulletin.title[:30]}'"


class BlogComment(models.Model):
    """Comment model for blog posts (Post model)"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']  # Newest comments first
        verbose_name = "Blog Comment"
        verbose_name_plural = "Blog Comments"

    def __str__(self):
        return f"{self.user.username} commented on '{self.post.title[:30]}'"


class CommunityMedia(models.Model):
    """Model for community gallery media (pictures & videos)"""
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    CATEGORIES = [
        ('events', 'Community Events'),
        ('facilities', 'Facilities & Amenities'),
        ('properties', 'Properties'),
        ('activities', 'Community Activities'),
        ('announcements', 'Announcements'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    media_file = models.FileField(upload_to='community_media/%Y/%m/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='image')
    category = models.CharField(max_length=20, choices=CATEGORIES, default='activities')
    
    # Relationships
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_media')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_media')
    
    # Status
    is_approved = models.BooleanField(default=True)  # Admin uploads auto-approved, user submissions need approval
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    # Metadata
    views_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    order = models.IntegerField(default=0)  # For manual sorting
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-order', '-created_at']  # Featured/ordered items first, then by date
        verbose_name = "Community Media"
        verbose_name_plural = "Community Media"
    
    def __str__(self):
        return f"{self.title} ({self.get_media_type_display()})"


class Message(models.Model):
    text = models.TextField()
    sender = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.sender}: {self.text[:30]}"


class Subdivision(models.Model):
    lot_number = models.CharField(max_length=50, unique=True)
    is_occupied = models.BooleanField(default=False)
    owner_name = models.CharField(max_length=100, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.lot_number} - {'Occupied' if self.is_occupied else 'Not Occupied'}"


class Pin(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    occupant = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)  # Available | Occupied | Reserved
    price = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    square_meter = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='pin_images/', blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def get_average_rating(self):
        """Calculate average rating for this pin"""
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0.0

    def get_review_count(self):
        """Get total number of reviews"""
        return self.reviews.count()


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    pin = models.ForeignKey(Pin, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ['pin', 'user']  # One review per user per pin
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.pin.name} ({self.rating} stars)"

# --- Facility ---
class Facility(models.Model):
    FACILITY_CHOICES = [
        ("Court", "Basketball Court"),
        ("Pool", "Swimming Pool"),
        ("Clubhouse", "Clubhouse"),
    ]
    name = models.CharField(max_length=100, choices=FACILITY_CHOICES)
    history = HistoricalRecords()

    def __str__(self):
        return self.get_name_display()

# --- Booking ---
class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="bookings")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.username} booked {self.facility.get_name_display()} on {self.date} ({self.status})"    

# --- Available Slot (Admin sets available booking times) ---
class AvailableSlot(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="available_slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ['facility', 'date', 'start_time', 'end_time']
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.facility.get_name_display()} - {self.date} ({self.start_time} to {self.end_time})"

# --- Maintenance (Admin blocks dates/times for facility maintenance) ---
class Maintenance(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="maintenance_periods")
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)  # Optional: specific time
    end_time = models.TimeField(null=True, blank=True)  # Optional: specific time
    reason = models.TextField(blank=True, help_text="Reason for maintenance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['start_date', 'start_time']
        verbose_name_plural = "Maintenance Periods"

    def __str__(self):
        time_str = f" {self.start_time} - {self.end_time}" if self.start_time and self.end_time else ""
        return f"{self.facility.get_name_display()} - {self.start_date} to {self.end_date}{time_str}"


class MaintenanceRequest(models.Model):
    """
    Homeowner maintenance request system
    Homeowner creates request -> Admin approves/declines -> Email notifications sent
    """
    MAINTENANCE_TYPE_CHOICES = [
        ('carpenter', 'Carpenter'),
        ('aircon', 'Air Conditioning Repair'),
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('roofing', 'Roofing'),
        ('renovation', 'House Renovation'),
        ('painting', 'Painting'),
        ('flooring', 'Flooring'),
        ('appliance', 'Appliance Repair'),
        ('structural_repairs', 'Structural Repairs'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    # Homeowner who created the request
    homeowner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='maintenance_requests'
    )
    
    # Maintenance details
    maintenance_type = models.CharField(max_length=50, choices=MAINTENANCE_TYPE_CHOICES)
    description = models.TextField(help_text="Detailed description of the maintenance needed")
    
    # Preferred schedule
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    
    # Urgency
    is_urgent = models.BooleanField(default=False)
    
    # External contractor option
    use_external_contractor = models.BooleanField(
        default=False,
        help_text="If homeowner wants to call someone outside the subdivision"
    )
    external_contractor_name = models.CharField(max_length=255, blank=True, null=True)
    external_contractor_contact = models.CharField(max_length=50, blank=True, null=True)
    external_contractor_company = models.CharField(max_length=255, blank=True, null=True)
    
    # Status and approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_maintenance_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    declined_reason = models.TextField(blank=True, null=True)
    admin_feedback = models.TextField(blank=True, null=True, help_text="Admin notes or feedback on the maintenance request")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Maintenance Requests"
    
    def __str__(self):
        return f"{self.get_maintenance_type_display()} - {self.homeowner.username} ({self.status})"


class MaintenanceProvider(models.Model):
    """
    Approved maintenance providers that admin can list for homeowners
    """
    name = models.CharField(max_length=255, help_text="Provider/Company name")
    contact_person = models.CharField(max_length=255, blank=True, null=True, help_text="Contact person name")
    phone = models.CharField(max_length=50, help_text="Contact phone number")
    email = models.EmailField(blank=True, null=True, help_text="Contact email")
    address = models.TextField(blank=True, null=True, help_text="Provider address")
    
    # Services offered
    services = models.TextField(help_text="Comma-separated list of services offered (e.g., plumbing, electrical, roofing)")
    
    # Location info
    is_nearby = models.BooleanField(default=True, help_text="Is this provider nearby the subdivision?")
    distance = models.CharField(max_length=50, blank=True, null=True, help_text="Distance from subdivision (e.g., '2 km', '5 minutes')")
    
    # Status
    is_approved = models.BooleanField(default=True, help_text="Is this provider approved by admin?")
    is_active = models.BooleanField(default=True, help_text="Is this provider currently active?")
    
    # Additional info
    rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, help_text="Provider rating (0-5)")
    notes = models.TextField(blank=True, null=True, help_text="Admin notes about this provider")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_providers')
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-is_approved', '-is_active', 'name']
        verbose_name = "Maintenance Provider"
        verbose_name_plural = "Maintenance Providers"
    
    def __str__(self):
        return f"{self.name} ({'Approved' if self.is_approved else 'Pending'})"
    
    def get_services_list(self):
        """Return services as a list"""
        if self.services:
            return [s.strip() for s in self.services.split(',')]
        return []
    
    
class News(models.Model):
    title = models.CharField(max_length=150)
    content = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.title


class Alert(models.Model):
    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]
    title = models.CharField(max_length=150)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="info")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"[{self.severity}] {self.title}"


class ContactInfo(models.Model):
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.address or self.email or "Contact Info"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.subject} from {self.name}"


class EmergencyContact(models.Model):
    """Emergency contact information for residents"""
    name = models.CharField(max_length=255, help_text="Name of the emergency contact (e.g., Police, Fire Department, Hospital)")
    phone = models.CharField(max_length=20, help_text="Contact phone number")
    description = models.TextField(blank=True, null=True, help_text="Description or additional information")
    category = models.CharField(
        max_length=50,
        default='general',
        help_text="Category of emergency contact (police, fire, medical, security, etc.)"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this contact is currently active")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"

    def __str__(self):
        return f"{self.name} - {self.phone}"
 
class ResidentPin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="resident_pin")
    pin = models.CharField(max_length=6, blank=True, null=True)
    history = HistoricalRecords()

    def generate_pin(self):
        self.pin = f"{random.randint(100000, 999999)}"
        self.save()
        return self.pin

    def __str__(self):
        return f"{self.user.username} - {self.pin}"   
    
class Visitor(models.Model):
    name = models.CharField(max_length=255)
    gmail = models.EmailField(blank=True, null=True)  # Gmail field
    contact_number = models.CharField(max_length=20, blank=True, null=True)  # Optional contact number
    address = models.CharField(max_length=500, blank=True, null=True)  # Address of visit
    homeowner_name = models.CharField(max_length=255, blank=True, null=True)  # Homeowner to visit
    pin_entered = models.CharField(max_length=6, blank=True, null=True)
    history = HistoricalRecords()  # Entered resident PIN
    resident = models.ForeignKey(
        "ResidentPin",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("declined", "Declined")
        ],
        default="pending"
    )
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.gmail or 'No Email'})"   


class VisitorRequest(models.Model):
    """
    Time-limited visitor request system with one-time PIN generation
    Homeowner creates request -> Admin approves -> System generates PIN -> Email sent with PDF
    """
    STATUS_CHOICES = [
        ('pending_admin', 'Pending Admin Approval'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('used', 'Used'),
    ]
    
    # Resident/Homeowner who created the request
    resident = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='visitor_requests'
    )
    
    # Visitor Information
    visitor_name = models.CharField(max_length=255)
    visitor_email = models.EmailField()
    visitor_contact_number = models.CharField(max_length=20)
    vehicle_plate_number = models.CharField(max_length=20, blank=True, null=True, help_text="Vehicle plate number (if applicable)")
    reason = models.TextField(blank=True, null=True, help_text="Reason for visit")
    
    # One-time PIN
    one_time_pin = models.CharField(max_length=6, unique=True, null=True, blank=True, db_index=True)
    
    # Time validity - when the PIN can be used
    visit_date = models.DateField()
    visit_end_date = models.DateField(null=True, blank=True, help_text="End date for multi-day visits (optional - if not set, uses visit_date)")
    visit_start_time = models.TimeField()
    visit_end_time = models.TimeField()
    
    # Status and tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending_admin'
    )
    
    # Admin approval tracking
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_visitor_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    declined_reason = models.TextField(blank=True, null=True, help_text="Reason for decline (if applicable)")
    
    # PDF and email tracking
    pdf_generated = models.BooleanField(default=False)
    pdf_file_path = models.FileField(upload_to='visitor_request_pdfs/', null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Link to actual Visitor record if PIN was used
    visitor_record = models.ForeignKey(
        Visitor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitor_request'
    )
    
    # PIN entry tracking - when guard enters the PIN at guard station
    pin_entered_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when PIN was entered at guard station")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Visitor Request"
        verbose_name_plural = "Visitor Requests"
    
    def is_valid(self):
        """Check if PIN is still valid based on date and time with proper timezone handling"""
        from django.utils import timezone
        from django.conf import settings
        from datetime import datetime, timedelta
        
        if self.status != 'approved' or not self.one_time_pin:
            return False
            
        # Check if PIN has been used
        if self.status == 'used':
            return False
        
        # Check if required date/time fields are present
        if not self.visit_date or not self.visit_start_time or not self.visit_end_time:
            return False
        
        # Get current time (already timezone-aware)
        now = timezone.now()
        
        # Determine end date (use visit_end_date if set, otherwise use visit_date)
        end_date = self.visit_end_date if self.visit_end_date else self.visit_date
        
        # Combine date and time to create naive datetime objects
        visit_datetime_start_naive = datetime.combine(self.visit_date, self.visit_start_time)
        visit_datetime_end_naive = datetime.combine(end_date, self.visit_end_time)
        
        # Make aware using Django's timezone utilities (uses settings.TIME_ZONE)
        # timezone.make_aware uses the default timezone from settings
        visit_datetime_start = timezone.make_aware(visit_datetime_start_naive)
        visit_datetime_end = timezone.make_aware(visit_datetime_end_naive)
        
        # If end time is before start time on same day, assume it spans to next day
        if visit_datetime_end < visit_datetime_start and self.visit_date == end_date:
            visit_datetime_end += timedelta(days=1)
        
        # Ensure both datetimes are in the same timezone as 'now' for comparison
        # This handles any timezone differences
        if visit_datetime_start.tzinfo != now.tzinfo:
            visit_datetime_start = visit_datetime_start.astimezone(now.tzinfo)
        if visit_datetime_end.tzinfo != now.tzinfo:
            visit_datetime_end = visit_datetime_end.astimezone(now.tzinfo)
        
        # PIN is valid ONLY if current time is within the visit window (between start and end)
        # This ensures PIN is only valid during the scheduled visit time
        is_within_window = visit_datetime_start <= now <= visit_datetime_end
        
        return is_within_window
    
    def generate_one_time_pin(self):
        """Generate a unique 6-digit PIN"""
        max_attempts = 100
        for _ in range(max_attempts):
            pin = f"{random.randint(100000, 999999)}"
            if not VisitorRequest.objects.filter(one_time_pin=pin).exists():
                self.one_time_pin = pin
                self.save()
                return pin
        raise ValueError("Could not generate unique PIN after multiple attempts")
    
    def __str__(self):
        return f"Request for {self.visitor_name} by {self.resident.username} - {self.status}"


class House(models.Model):
    LISTING_TYPE_CHOICES = [
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condo'),
        ('townhouse', 'Townhouse'),
        ('villa', 'Villa'),
        ('duplex', 'Duplex'),
        ('studio', 'Studio'),
    ]
    
    FURNISHING_CHOICES = [
        ('fully_furnished', 'Fully Furnished'),
        ('semi_furnished', 'Semi Furnished'),
        ('unfurnished', 'Unfurnished'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="houses")
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='house-images/', blank=True, null=True)  # Keep for backward compatibility
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES, default='sale')
    
    # Basic Property Information
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, blank=True, null=True)
    beds = models.IntegerField(default=0, help_text="Number of bedrooms")
    baths = models.IntegerField(default=0, help_text="Number of bathrooms")
    floor_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Floor area in square meters")
    lot_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Lot size in square meters")
    year_built = models.IntegerField(blank=True, null=True, help_text="Year the property was built")
    floors = models.IntegerField(default=1, help_text="Number of floors/stories")
    
    # Property Features
    furnishing = models.CharField(max_length=20, choices=FURNISHING_CHOICES, blank=True, null=True)
    parking_spaces = models.IntegerField(default=0, help_text="Number of parking spaces")
    has_balcony = models.BooleanField(default=False)
    has_garden = models.BooleanField(default=False)
    has_pool = models.BooleanField(default=False)
    has_elevator = models.BooleanField(default=False)
    has_security = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=False)
    has_heating = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_cable_tv = models.BooleanField(default=False)
    has_dishwasher = models.BooleanField(default=False)
    has_washing_machine = models.BooleanField(default=False)
    has_dryer = models.BooleanField(default=False)
    has_microwave = models.BooleanField(default=False)
    has_refrigerator = models.BooleanField(default=False)
    has_gym = models.BooleanField(default=False)
    has_playground = models.BooleanField(default=False)
    has_clubhouse = models.BooleanField(default=False)
    has_laundry_room = models.BooleanField(default=False)
    has_storage = models.BooleanField(default=False)
    has_fireplace = models.BooleanField(default=False)
    has_garage = models.BooleanField(default=False)
    has_cctv = models.BooleanField(default=False)
    has_intercom = models.BooleanField(default=False)
    has_generator = models.BooleanField(default=False)
    has_water_heater = models.BooleanField(default=False)
    has_solar_panels = models.BooleanField(default=False)
    
    # Financial Information
    association_dues = models.CharField(max_length=255, blank=True, null=True, help_text="Association dues information")
    utilities_included = models.BooleanField(default=False, help_text="Are utilities included in the price?")
    
    # Rental Specific Fields
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Security deposit amount")
    advance_payment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Advance payment amount")
    lease_term = models.CharField(max_length=100, blank=True, null=True, help_text="Lease term (e.g., '1 year', '6 months')")
    pet_friendly = models.BooleanField(default=False)
    
    # Sale Specific Fields
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Required down payment")
    payment_terms = models.TextField(blank=True, null=True, help_text="Payment terms and conditions")
    
    # Additional Information
    amenities = models.TextField(blank=True, null=True, help_text="Comma-separated list of amenities")
    nearby_facilities = models.TextField(blank=True, null=True, help_text="Nearby schools, malls, hospitals, etc.")
    days_on_market = models.CharField(max_length=100, blank=True, null=True, help_text="Days on the market (e.g., '1 month', '2 weeks')")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Contact phone number")
    contact_email = models.EmailField(blank=True, null=True, help_text="Contact email address")
    property_status = models.CharField(max_length=20, default='available', help_text="Property status: available, pending, sold, rented")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class HouseImage(models.Model):
    """Model for storing multiple images per house"""
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='house-images/')
    order = models.IntegerField(default=0, help_text="Order for displaying images")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.house.title} - Image {self.order}"
    
class Billing(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='billing_records')
    file = models.FileField(upload_to='billing/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.file.name}"
    
class BillingRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_records')
    file = models.FileField(upload_to=billing_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.username} - {self.file.name.split('/')[-1]}"    
    
class FAQ(models.Model):
    question = models.CharField(max_length=500)
    answer = models.TextField()
    order = models.IntegerField(default=0, help_text="Order for display (lower numbers appear first)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question[:50] + "..." if len(self.question) > 50 else self.question


def service_fee_bill_path(instance, filename):
    """Generate upload path for service fee bills"""
    return f'service_fees/user_{instance.homeowner.id}/bills/{filename}'


def service_fee_receipt_path(instance, filename):
    """Generate upload path for service fee receipts"""
    return f'service_fees/user_{instance.homeowner.id}/receipts/{filename}'


def service_fee_policy_path(instance, filename):
    """Generate upload path for service fee policy documents"""
    return f'service_fees/user_{instance.homeowner.id}/policies/{filename}'


class ServiceFee(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('delayed', 'Delayed'),
    ]
    
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_fees', limit_choices_to={'is_staff': False})
    bill_image = models.ImageField(upload_to=service_fee_bill_path, blank=True, null=True, help_text="Bill image uploaded by admin")
    receipt_image = models.ImageField(upload_to=service_fee_receipt_path, blank=True, null=True, help_text="Receipt image uploaded by homeowner")
    policy_image = models.ImageField(upload_to=service_fee_policy_path, blank=True, null=True, help_text="Policy document/image uploaded by admin")
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Service fee amount")
    due_date = models.DateField(blank=True, null=True, help_text="Due date for payment")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    month = models.CharField(max_length=20, blank=True, null=True, help_text="Billing month (e.g., January 2024)")
    year = models.IntegerField(blank=True, null=True, help_text="Billing year")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at', '-due_date']
        verbose_name = "Service Fee"
        verbose_name_plural = "Service Fees"

    def __str__(self):
        return f"{self.homeowner.username} - {self.month or 'N/A'} {self.year or ''} - {self.get_status_display()}"
    
    def check_if_overdue(self):
        """Auto-check if payment is overdue"""
        from django.utils import timezone
        if self.status == 'unpaid' and self.due_date:
            if timezone.now().date() > self.due_date:
                self.status = 'delayed'
                self.save()
                return True
        return False
    
    def get_status_display_with_icon(self):
        """Get status with icon"""
        icons = {
            'unpaid': '🔵 UNPAID',
            'paid': '✅ PAID',
            'delayed': '🔴 OVERDUE'
        }
        return icons.get(self.status, self.status.upper())


class PaymentLink(models.Model):
    """Simple payment link tracker"""
    service_fee = models.OneToOneField(
        ServiceFee,
        on_delete=models.CASCADE,
        related_name='payment_link'
    )
    link_id = models.CharField(max_length=100, unique=True)
    reference_number = models.CharField(max_length=100, unique=True)
    checkout_url = models.URLField(max_length=500)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    history = HistoricalRecords()
    
    class Meta:
        db_table = 'payment_link'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference_number} - {'PAID' if self.paid else 'UNPAID'}"


class PayMongoTransaction(models.Model):
    """Track PayMongo payments (QRPh/GCash/E-Wallet)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('chargeable', 'Chargeable'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    service_fee = models.ForeignKey(
        ServiceFee,
        on_delete=models.CASCADE,
        related_name='paymongo_transactions'
    )
    
    # PayMongo IDs
    source_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # Transaction Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='PHP')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # URLs
    checkout_url = models.URLField(max_length=500)
    
    # Billing Info
    billing_name = models.CharField(max_length=255)
    billing_email = models.EmailField()
    billing_phone = models.CharField(max_length=20)
    
    # Timestamps
    paid_at = models.DateTimeField(blank=True, null=True)
    
    # Fees
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    test_mode = models.BooleanField(default=True)
    raw_data = models.JSONField(blank=True, null=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "PayMongo Transaction"
        verbose_name_plural = "PayMongo Transactions"
    
    def __str__(self):
        return f"{self.service_fee.homeowner.username} - ₱{self.amount} - {self.status}"
    
    
# Store the PIN for each resident/admin
# class ResidentPin(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="resident_pin")
#     pin = models.CharField(max_length=6, blank=True, null=True)
#     history = HistoricalRecords()

#     def generate_pin(self):
#         # Generate a 6-digit numeric PIN
#         self.pin = f"{random.randint(100000, 999999)}"
#         self.save()
#         return self.pin

#     def __str__(self):
#         return f"{self.user.username} - {self.pin}"


# Track visitor check-ins
# class Visitor(models.Model):
#     name = models.CharField(max_length=255)
#     gmail = models.EmailField(blank=True, null=True)  # <-- use gmail
#     pin_entered = models.CharField(max_length=6, blank=True, null=True)
#     resident = models.ForeignKey("ResidentPin", on_delete=models.SET_NULL, null=True, blank=True)
#     reason = models.TextField(blank=True, null=True)    
#     status = models.CharField(
#         max_length=10,
#         choices=[("pending","Pending"),("approved","Approved"),("declined","Declined")],
#         default="pending"
#     )
#     time_in = models.DateTimeField(null=True, blank=True)
#     time_out = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.name} ({self.gmail})"

# class Facility(models.Model):
#     FACILITY_CHOICES = [
#         ("Court", "Basketball Court"),
#         ("Pool", "Swimming Pool"),
#     ]
#     name = models.CharField(max_length=100, choices=FACILITY_CHOICES)

#     def __str__(self):
#         return self.get_name_display()


# class Booking(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
#     facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="bookings")
#     date = models.DateField()
#     start_time = models.TimeField()
#     end_time = models.TimeField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user.username} booked {self.facility.get_name_display()} on {self.date}"


# # from django.db import models

# # class Post(models.Model):
# #     title = models.CharField(max_length=100)
# #     body = models.TextField()
# #     lat = models.FloatField(null=True, blank=True)
# #     lng = models.FloatField(null=True, blank=True)

# # class Message(models.Model):
# #     text = models.TextField()
# #     sender = models.CharField(max_length=10)
# #     timestamp = models.DateTimeField(auto_now_add=True)

# #     def __str__(self):
# #         return f"{self.sender}: {self.text[:30]}"    

# # models.py
# from django.db import models
# from django.db import models
# from django.contrib.auth.models import User

# def user_profile_path(instance, filename):
#     return f'profile_images/user_{instance.user.id}/{filename}'

# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
#     profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

#     def __str__(self):
#         return self.user.username


# # --- signals ---
# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)

# class Post(models.Model):
#     title = models.CharField(max_length=100)
#     body = models.TextField()
#     lat = models.FloatField(null=True, blank=True)
#     lng = models.FloatField(null=True, blank=True)

# class Message(models.Model):
#     text = models.TextField()
#     sender = models.CharField(max_length=10)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.sender}: {self.text[:30]}"

# class Subdivision(models.Model):
#     lot_number = models.CharField(max_length=50, unique=True)
#     is_occupied = models.BooleanField(default=False)
#     owner_name = models.CharField(max_length=100, blank=True, null=True)

#     def __str__(self):
#         return f"{self.lot_number} - {'Occupied' if self.is_occupied else 'Not Occupied'}"
    
# class Pin(models.Model):
#     name = models.CharField(max_length=255)
#     latitude = models.FloatField()
#     longitude = models.FloatField()

#     def __str__(self):
#         return self.name