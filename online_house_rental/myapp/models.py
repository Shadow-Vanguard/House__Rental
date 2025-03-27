from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class User(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Property Owner'),
        ('user', 'User'),
    ]
    name = models.CharField(max_length=150, unique=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True)
    phone = models.CharField(max_length=10, blank=True, null=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    reset_token = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(default=True)





class Property(models.Model):
    PROPERTY_TYPES = [
        ('Apartment', 'Apartment'),
        ('House', 'House'),
    ]
    LISTING_TYPES = [
        ('Rent', 'Rent'),
        ('Sale', 'Sale'),
        ('Both', 'Rent and Sale'),
    ]
    property_name = models.CharField(max_length=255, null=False)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES, null=False)
    listing_type = models.CharField(max_length=50, choices=LISTING_TYPES, null=False)  # Rent, Sale, or Both
    description = models.TextField(null=False)
    address = models.CharField(max_length=255, null=False)
    city = models.CharField(max_length=100, null=False)
    state = models.CharField(max_length=100, null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    beds = models.IntegerField(default=0, null=False, )
    baths = models.IntegerField(default=1, null=False, )
    area = models.IntegerField(default=500, null=False, )
    posted_date = models.DateTimeField(default=timezone.now, null=False)
    status = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    monthly_rent = models.IntegerField(null=True, blank=True)
    terms_and_conditions = models.CharField(max_length=3000, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_rented = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)

    def __str__(self):
        return self.property_name



class PropertyImage(models.Model):
    property = models.ForeignKey(Property, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='property_images/', null=False)

    def str(self):
        return f"Image for {self.property.property_name}"

class Adminm(models.Model):
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

class RentalAgreement(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    renter = models.ForeignKey(User, on_delete=models.CASCADE)  # The user signing the agreement
    start_date = models.DateField()
    end_date = models.DateField()
    terms = models.BooleanField()  # To confirm they agreed to terms
    digital_signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    owner_digital_signature = models.ImageField(upload_to='signatures/', blank=True, null=True)  # Owner's signature
    status = models.BooleanField(null=True, default=None)
    notification_date = models.DateTimeField(blank=True, null=True)  # Field to track notification timestamp



    def __str__(self):
        return f'Rental Agreement for {self.property.property_name}'



class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    property = models.ForeignKey(Property, on_delete=models.CASCADE)  # Link to the property
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_date = models.DateTimeField(blank=True, null=True)  # Added for tracking notification time
    token_advance = models.BooleanField(default=False)
    token_status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'),('rejected', 'Rejected')], null=True, blank=True)
    token_price = models.IntegerField(blank=True, null=True)

class Feedback(models.Model):
    property = models.ForeignKey(Property, related_name="feedback", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # Store a rating from 1 to 5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    rental_agreement = models.ForeignKey(RentalAgreement, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True, null=True)
    
class TokenPayment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Foreign Keys
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_payments')  # Tenant making the payment
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_token_payments')  # Property owner
    property = models.ForeignKey(Property, on_delete=models.CASCADE)  # Associated property
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)  # Associated token request message

    # Fields
    billing_address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pin_code = models.CharField(max_length=10, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Token amount
    payment_date = models.DateTimeField(default=timezone.now)  # When the payment was made
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')  # Payment status
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # Unique transaction ID


class PropertyRental(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey('Property', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    rental_start_date = models.DateField(auto_now_add=True)



class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('declined', 'Declined')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency')
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='maintenance_images/', blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='low')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    reported_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    owner_notes = models.TextField(blank=True, null=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    notification_date = models.DateTimeField(blank=True, null=True)



class HouseholdItem(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('used', 'Used')
    ]
    
    CATEGORY_CHOICES = [
        ('furniture', 'Furniture'),
        ('appliances', 'Appliances'),
        ('electronics', 'Electronics'),
        ('kitchenware', 'Kitchenware'),
        ('decor', 'Home Decor'),
        ('other', 'Other')
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='household_items')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    posted_date = models.DateTimeField(default=timezone.now)
    status = models.BooleanField(default=True)  # For soft delete

    # Optional fields
    brand = models.CharField(max_length=100, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)  # Age in months
    warranty_info = models.TextField(blank=True, null=True)
    warranty_document = models.FileField(upload_to='warranty_documents/', blank=True, null=True)

    def __str__(self):
        return self.name

class HouseholdItemImage(models.Model):
    item = models.ForeignKey(HouseholdItem, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='household_items/')

    def __str__(self):
        return f"Image for {self.item.name}"

class HouseholdItemWishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='household_wishlists')
    item = models.ForeignKey(HouseholdItem, on_delete=models.CASCADE, related_name='wishlist_entries')
    added_date = models.DateTimeField(auto_now_add=True)


class HouseholdItemPayment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='household_payments')
    item = models.ForeignKey(HouseholdItem, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True)

class VirtualMeeting(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meetings_requested")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meetings_received")
    property_name = models.CharField(max_length=255)
    scheduled_time = models.DateTimeField()
    meeting_link = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    

class ForumPost(models.Model):
    """Forum post model for community discussions"""
    CATEGORY_CHOICES = [
        ('general', 'General Discussion'),
        ('renting', 'Renting Tips'),
        ('maintenance', 'Maintenance'),
        ('neighborhood', 'Neighborhood Info'),
        ('other', 'Other')
    ]
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='forum_attachments/', null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

class ForumInteraction(models.Model):
    """Combined model for comments and likes"""
    INTERACTION_TYPES = [
        ('comment', 'Comment'),
        ('like', 'Like')
    ]
    
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='interactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    comment_content = models.TextField(null=True, blank=True)  # Only used for comments
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Ensure a user can only like a post once
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'],
                condition=models.Q(interaction_type='like'),
                name='unique_post_like'
            )
        ]
    
    def __str__(self):
        if self.interaction_type == 'comment':
            return f"Comment by {self.user.name} on {self.post.title}"
        return f"Like by {self.user.name} on {self.post.title}"


class PropertyView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    view_count = models.IntegerField(default=1)
    last_viewed = models.DateTimeField(auto_now=True)

        
