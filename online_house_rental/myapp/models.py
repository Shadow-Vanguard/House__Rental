from django.db import models
from django.utils import timezone


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


        