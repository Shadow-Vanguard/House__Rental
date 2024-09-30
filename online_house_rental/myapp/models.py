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
    status = models.BooleanField(default=True)  # Boolean field, defaulting to True (e.g., for active users)



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

