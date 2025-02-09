from django.shortcuts import render,redirect,get_object_or_404
from .models import User,Property,PropertyImage,Adminm,Wishlist,RentalAgreement,Message,Feedback,Payment,TokenPayment, PropertyRental, MaintenanceRequest, HouseholdItem, HouseholdItemImage, HouseholdItemWishlist
from django.contrib import messages
import logging
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.http import HttpResponse,HttpResponseRedirect
from django.core.files.storage import FileSystemStorage 
import random
import time
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
import json
from datetime import datetime


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):
    request.session.flush()  # This clears the session data
    return redirect('login')


def index(request):
    return render(request, 'index.html')

from django.core.mail import send_mail


otp_storage = {}

def send_otp_email(user_email):
    otp = random.randint(1000, 9999) 
    otp_storage[user_email] = otp 

    subject = 'Your OTP for Email Verification'
    message = f'Your OTP is {otp}. Please use this to verify your email.'
    from_email = 'haripriyaka2025@mca.ajce.in' 
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list)

def enter_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.GET.get('role')  # Get role from the query parameters
        if User.objects.filter(email=email).exists():
            messages.info(request, "Email is already registered. Please log in.")
            return redirect('login')
        send_otp_email(email)
        request.session['email'] = email
        request.session['role'] = role  # Store role in session
        return redirect('verify_otp')
    return render(request, 'enter_email.html')


def verify_otp(request):
    email = request.session.get('email')
    role = request.session.get('role')  # Get role from session
    if not email:
        messages.error(request, "Session expired. Please enter your email again.")
        return redirect('enter_email')
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        if otp_storage.get(email) and otp_storage[email] == int(otp_input):
            del otp_storage[email]
            request.session['email'] = email
            return redirect(f"{reverse('register')}?role={role}")  # Correctly construct the URL
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    return render(request, 'verify_otp.html')


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        password = request.POST.get('password')
        admin = Adminm.objects.filter(email=email).first()
        if admin:
            if admin.password == password:  # Check password
                request.session['admin_email'] = admin.email
                return redirect('admin')
            else:
                return render(request, 'login.html', {'error': 'Incorrect password for admin'})
        user = User.objects.filter(email=email).first()
        if user:
            if user.password == password:  # Check password
                request.session['user_id'] = user.id
                request.session['name'] = user.name
                request.session['role'] = user.role
                if user.role == 'owner':
                    return redirect('owner')
                elif user.role == 'user':
                    return redirect('userpage')
            else:
                return render(request, 'login.html', {'error': 'Incorrect password'})
        return render(request, 'login.html', {'error': 'Email does not exist'})
    return render(request, 'login.html')

def register(request):
    role = request.GET.get('role', 'user')
    email = request.session.get('email', '')
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        email = request.POST.get('email')
        phone = request.POST.get('contact')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        role = request.POST.get('role', role)  # Use role from POST if it exists
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'email_error': 'An account with this email already exists.', 'name': name, 'address': address, 'contact': phone, 'role': role})
        if password != confirm_password:
            return render(request, 'register.html', {'error': 'Passwords do not match.', 'name': name, 'address': address, 'contact': phone, 'email': email, 'role': role})
        user = User(name=name, address=address, email=email, phone=phone, password=password, role=role)
        user.save()
        send_mail('Registration Successful', f'Hello {name},\n\nThank you for registering!\n\nBest regards,\nYour Team', settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        return redirect('login')
    return render(request, 'register.html', {'role': role, 'email': email})



def about(request):
    return render(request, 'about.html')
def contact(request):
    return render(request, 'contact.html')
def forgotpass(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            token = get_random_string(20)
            reset_link = request.build_absolute_uri(reverse('reset_password', args=[token]))
            try:
                send_mail(
                    'Password Reset Request',
                    f'Click the link below to reset your password:\n\n{reset_link}',
                    'your-email@example.com',  # Use the actual email configured in settings
                    [email],
                    fail_silently=False,
                )
                user.reset_token = token
                user.save()
                messages.success(request, 'Password reset link has been sent to your email.')
            except Exception as e:
                messages.error(request, f"Error sending email: {str(e)}")
        else:
            messages.error(request, 'No account found with that email.')
    return render(request, 'forgotpass.html')  # This should be inside the POST block


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def userpage(request):
    if request.session.get('user_id'):
        user_id = request.session.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect('login')

        # Get rented properties for this user
        rented_properties = Property.objects.filter(
            propertyrental__user=user,
            propertyrental__is_active=True
        ).distinct()

        # Get all verified properties that are NOT rented by anyone
        properties = Property.objects.filter(
            is_verified=True,
            is_rented=False  # Only show properties that aren't rented
        ).exclude(
            id__in=rented_properties.values_list('id', flat=True)  # Exclude user's rented properties
        )

        # Apply search filters
        location = request.GET.get('location', '')
        category = request.GET.get('category', '')
        price = request.GET.get('price', '')
        bhk = request.GET.get('bhk', '')

        if location:
            properties = properties.filter(city__icontains=location) | properties.filter(state__icontains=location)
        
        if category:
            properties = properties.filter(property_type__iexact=category)
        
        if price:
            try:
                max_price = float(price)
                properties = properties.filter(price__lte=max_price)
            except ValueError:
                pass
        
        if bhk:
            try:
                bhk_value = int(bhk)
                properties = properties.filter(beds=bhk_value)
            except ValueError:
                pass

        context = {
            'user': user,
            'properties': properties,
            'rented_properties': rented_properties,
            'request': request
        }
        
        return render(request, 'userpage.html', context)
    else:
        return redirect('login')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def owner(request):
    if request.session.get('user_id'):
        user_id = request.session.get('user_id')  # Get user_id from session
        user = get_object_or_404(User, id=user_id)  # Fetch the user details

        owner_name = request.session.get('name')  # Get owner's name from session

        return render(request, 'owner.html', {
            'owner_name': owner_name,
            'user': user,  # Pass the user object to the template
        })
    else:
        return redirect('login')


def admin(request):
    return render(request, 'admin.html')
def reset_password(request, token):
    user = User.objects.filter(reset_token=token).first()
    if user:
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password == confirm_password:
                user.password = new_password
                user.reset_token = None
                user.save()
                messages.success(request, 'Password reset successful. You can now log in.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
        return render(request, 'reset_password.html', {'token': token})
    else:
        messages.error(request, 'Invalid or expired reset token.')
        return redirect('forgotpass')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)        
def propertyview(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)
    user_id = request.session.get('user_id')
    
    # Check if user has rented this property
    has_rented = False
    if user_id:
        # Check if there's an accepted rental agreement
        has_active_agreement = RentalAgreement.objects.filter(
            property=property_instance,
            status=True  # Accepted agreement
        ).exists()
        
        # Check if the current user has rented this property
        has_rented = RentalAgreement.objects.filter(
            property=property_instance,
            renter_id=user_id,
            status=True  # Accepted agreement
        ).exists()
        
        # Update property's rented status based on active agreements
        if property_instance.is_rented != has_active_agreement:
            property_instance.is_rented = has_active_agreement
            property_instance.save()
    
    if request.method == 'POST':
        if 'add_to_wishlist' in request.POST:
            if user_id:
                user = User.objects.get(id=user_id)
                wishlist_item, created = Wishlist.objects.get_or_create(user=user, property=property_instance)
                if created:
                    messages.success(request, 'Property added to wishlist!')
                else:
                    messages.info(request, 'Property is already in your wishlist.')
            else:
                messages.error(request, 'You need to log in to add to your wishlist.')

    context = {
        'property': property_instance,
        'has_rented': has_rented,
        'debug': True,
        'user_id': user_id
    }
    return render(request, 'propertyview.html', context)

def propertypage(request):
    properties = Property.objects.all()  # Fetch all properties
    return render(request, 'propertypage.html', {'properties': properties})

def updateprofile(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        new_name = request.POST.get('name')
        new_address = request.POST.get('address')
        new_phone = request.POST.get('phone')
        user.name = new_name
        user.address = new_address
        user.phone = new_phone
        user.save()
        return redirect('userpage')
    else:
        return render(request, 'updateprofile.html', {'user': user})
        
def ownerupdate(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        new_name = request.POST.get('name')
        new_address = request.POST.get('address')
        new_phone = request.POST.get('phone')
        user.name = new_name
        user.address = new_address
        user.phone = new_phone
        user.save()
        return redirect('owner')
    else:
        return render(request, 'ownerupdate.html', {'user': user})

def propertyadd(request):
    if request.method == 'POST':
        property_name = request.POST.get('property_name')
        description = request.POST.get('description')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        price = request.POST.get('price')
        property_type = request.POST.get('property_type')
        listing_type = request.POST.get('listing_type')
        beds = request.POST.get('beds')
        baths = request.POST.get('baths')
        area = request.POST.get('area')
        owner_id = request.session.get('user_id')
        owner = User.objects.get(id=owner_id)
        if Property.objects.filter(property_name=property_name).exists():
            messages.error(request, "Property name already exists. Please choose another name.")
            return render(request, 'propertyadd.html')
        property_instance = Property.objects.create(
            property_name=property_name,description=description,address=address,city=city,state=state,price=price,
            property_type=property_type,listing_type=listing_type,beds=beds,baths=baths,area=area,owner=owner
        )
        property_photos = request.FILES.getlist('image')
        for photo in property_photos:
            PropertyImage.objects.create(property=property_instance, image=photo)
        messages.success(request, 'Property added successfully!')
        return redirect('owner')
    return render(request, 'propertyadd.html')
    
def updateproperty(request):
    property_instance = None
    search_property_name = request.GET.get('search_property_name')
    if search_property_name:
        property_instance = Property.objects.filter(property_name=search_property_name).first()
    if request.method == 'POST' and property_instance:
        property_instance.property_name = request.POST.get('property_name')
        property_instance.description = request.POST.get('description')
        property_instance.address = request.POST.get('address')
        property_instance.city = request.POST.get('city')
        property_instance.state = request.POST.get('state')
        property_instance.price = request.POST.get('price')
        property_instance.property_type = request.POST.get('property_type')
        property_instance.listing_type = request.POST.get('listing_type')
        property_instance.save()
        delete_image_id = request.POST.get('delete_image')
        if delete_image_id:
            image_to_delete = PropertyImage.objects.filter(id=delete_image_id, property=property_instance).first()
            if image_to_delete:
                image_to_delete.delete()
        new_images = request.FILES.getlist('new_images')
        for image in new_images:
            PropertyImage.objects.create(property=property_instance, image=image)
        return redirect(f"{reverse('owner')}?search_property_name={property_instance.property_name}")
    return render(request, 'updateproperty.html', {'property': property_instance})

def ownerproperty(request):
    properties = Property.objects.all()
    if request.method == 'POST':
        delete_image_id = request.POST.get('delete_image')
        property_id = request.POST.get('property_id')
        deactivate_property_id = request.POST.get('deactivate_property')
        activate_property_id = request.POST.get('activate_property')
        # Handle image deletion
        if delete_image_id:
            property_instance = get_object_or_404(Property, id=property_id)
            image_to_delete = PropertyImage.objects.filter(id=delete_image_id, property=property_instance).first()
            if image_to_delete:
                image_to_delete.delete()
                return JsonResponse({'status': 'success'})
        # Handle property deactivation
        if deactivate_property_id:
            property_instance = get_object_or_404(Property, id=deactivate_property_id)
            property_instance.status = False  # Deactivate the property
            property_instance.save()
            return redirect('ownerproperty')
        # Handle property activation
        if activate_property_id:
            property_instance = get_object_or_404(Property, id=activate_property_id)
            property_instance.status = True  # Activate the property
            property_instance.save()
            return redirect('ownerproperty')
        # Handle property update
        property_instance = get_object_or_404(Property, id=property_id)
        property_instance.property_name = request.POST.get('property_name')
        property_instance.description = request.POST.get('description')
        property_instance.address = request.POST.get('address')
        property_instance.city = request.POST.get('city')
        property_instance.state = request.POST.get('state')
        property_instance.beds = request.POST.get('beds')
        property_instance.price = request.POST.get('price')
        property_instance.property_type = request.POST.get('property_type')
        property_instance.listing_type = request.POST.get('listing_type')
        monthly_rent = request.POST.get('monthly_rent')
        if monthly_rent:
            property_instance.monthly_rent = int(monthly_rent)
        property_instance.save()
        # Handle adding new images
        new_images = request.FILES.getlist('new_images')
        for image in new_images:
            PropertyImage.objects.create(property=property_instance, image=image)
        return redirect('ownerproperty')
    return render(request, 'ownerproperty.html', {'properties': properties})


def manageproperty(request):
    properties = Property.objects.all()  # Fetch all properties
    return render(request, 'manageproperty.html', {'properties': properties})

def manage_users(request, role):
    users = User.objects.filter(role=role)
    context = {'users': users, 'role': role}
    return render(request, 'manage_users.html', context)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('manage_users', user.role)

def view_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'view_profile.html', {'user': user})

def view_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'view_profile.html', {'user': user})

def deactivate_user(request, id):
    user = get_object_or_404(User, id=id)
    
    # If the request method is POST, capture the reason for deactivation
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        # Set the user's status to inactive
        user.status = False
        user.save()

        # Send an email notification with the reason for deactivation
        send_mail(
            'Account Deactivation',
            f'Hello {user.name},\n\nYour account has been deactivated. If you have any questions, please contact support.\n\nReason for deactivation: {reason}',
            'your_email@example.com',  # Replace with your email or from_email
            [user.email],  # The recipient's email
            fail_silently=False,
        )

        # Display a success message
        messages.success(request, 'User has been deactivated and notified via email.')

        # Redirect to manage_users with the role parameter
        return redirect('manage_users', role=user.role)
    else:
        # Handle the GET request to show the confirmation page with the deactivation form
        return render(request, 'deactivate_user.html', {'user': user})

def activate_user(request, id):
    user = get_object_or_404(User, id=id)
    user.status = True  # Set the status to active
    user.save()

    # Send an email notification
    send_mail(
        'Account Activation',
        f'Hello {user.name},\n\nYour account has been activated. You can now log in and use our services.',
        'your_email@example.com',  # Replace with your email or from_email
        [user.email],
        fail_silently=False,
    )

    messages.success(request, 'User has been activated and notified via email.')

    # Redirect to manage_users with the role parameter
    return redirect('manage_users', role=user.role)  # Adjust user.role based on how you retrieve it

def request(request):
    properties = Property.objects.all()  # Retrieve all properties
    return render(request, 'request.html', {'properties': properties})

def verify_property(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    property.is_verified = True  # Set is_verified to 1
    property.save()

    # Send verification email
    send_mail(
        'Property Verified',
        f'Congratulations! Your property "{property.property_name}" has been verified by our team.',
        'your_email@example.com',  # Replace with your email
        [property.owner.email],  # Owner's email
        fail_silently=False,
    )

    messages.success(request, f'Property "{property.property_name}" has been verified.')
    return redirect('request')  # Redirect back to the request page


def reject_property(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    property.is_verified = False  # Set is_verified to 0
    property.save()

    # Send rejection email
    send_mail(
        'Property Rejected',
        f'We regret to inform you that your property "{property.property_name}" has been rejected by our team.',
        'your_email@example.com',  # Replace with your email
        [property.owner.email],  # Owner's email
        fail_silently=False,
    )

    messages.success(request, f'Property "{property.property_name}" has been rejected.')
    return redirect('request')


def bookproperty(request):
    return render(request, 'bookproperty.html')
def bookconf(request):
    return render(request, 'bookconf.html')

def contactowner(request, property_id):
    if not request.session.get('user_id'):
        return redirect('login')  # Redirect to login if no session exists

    # Retrieve property and owner information
    property = get_object_or_404(Property, id=property_id)
    owner = property.owner
    current_user_id = request.session.get('user_id')  # Retrieve current user from session
    current_user = get_object_or_404(User, id=current_user_id)  # Get current user object

    # Fetch messages related to the property between the current user and the owner
    messages = Message.objects.filter(property=property, sender=current_user, receiver=owner) | \
               Message.objects.filter(property=property, sender=owner, receiver=current_user)
    messages = messages.order_by('timestamp')  # Order messages by timestamp

    if request.method == 'POST':
        message_text = request.POST.get('message')
        
        # Create a new message with the current user as sender
        Message.objects.create(
            sender=current_user,
            receiver=owner,
            property=property,
            message=message_text,
            timestamp=timezone.now(),
        )

    return render(request, 'contactowner.html', {
        'owner': owner,
        'messages': messages,
        'property': property,
    })

def owner_details(request, property_id):
    # Get the property object based on the provided property_id
    property = get_object_or_404(Property, id=property_id)
    
    # Render the owner details template with the property data
    return render(request, 'owner_details.html', {'property': property})


def wishlist(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = get_object_or_404(User, id=user_id)
        if request.method == 'POST':
            property_id = request.POST.get('remove_property_id')
            if property_id:
                try:
                    wishlist_item = Wishlist.objects.get(user=user, property_id=property_id)
                    wishlist_item.delete()  # Remove the property from the wishlist
                    messages.success(request, 'Property removed from your wishlist.')
                except Wishlist.DoesNotExist:
                    messages.error(request, 'This property is not in your wishlist.')
        wishlist_items = Wishlist.objects.filter(user=user)
        context = {
            'wishlist': [item.property for item in wishlist_items],
            'error': None
        }
    else:
        messages.error(request, "You need to log in to view your wishlist.")
        context = {
            'wishlist': [],
            'error': "You need to log in to view your wishlist."
        }
    return render(request, 'wishlist.html', context)



# def rental_agreement(request, property_id):
#     property = get_object_or_404(Property, id=property_id)
#     user_id = request.session.get('user_id')
#     print("User id:",user_id)
#     if not user_id:
#         return redirect('login')
#     user = get_object_or_404(User, id=user_id)
#     # Check if property is already rented
#     if property.is_rented:
#         messages.error(request, 'This property is no longer available for rent.')
#         return redirect('propertyview', property_id=property_id)

#      # Check if an agreement already exists for this user and property
#     existing_agreement = RentalAgreement.objects.filter(property=property, renter=user).exists()
#     if existing_agreement:
#         # Show a message if the agreement has already been submitted
#         return HttpResponse('You have already submitted a rental agreement for this property.')
#     if request.method == 'POST':
#         start_date = request.POST.get('start_date')
#         end_date = request.POST.get('end_date')
#         terms = request.POST.get('terms') == 'on'
#         digital_signature = request.FILES.get('digital_signature')
#         if not terms:
#             return HttpResponse('You must agree to the terms and conditions.')
#         rental_agreement = RentalAgreement(
#             property=property,
#             renter=user,
#             start_date=start_date,
#             end_date=end_date,
#             terms=terms,
#             digital_signature=digital_signature 
#         )
#         rental_agreement.save()
#         return redirect('thank')
#         # return HttpResponse('submitted succesfully')
#     return render(request, 'rental_agreement.html', {
#         'property': property
#         })

import base64
from django.core.files.base import ContentFile

def rental_agreement(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    user_id = request.session.get('user_id')
    print("User id:",user_id)
    if not user_id:
        return redirect('login')
    user = get_object_or_404(User, id=user_id)

     # Check if an agreement already exists for this user and property
    existing_agreement = RentalAgreement.objects.filter(property=property, renter=user).exists()
    if existing_agreement:
        # Show a message if the agreement has already been submitted
        return HttpResponse('You have already submitted a rental agreement for this property.')
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        terms = request.POST.get('terms') == 'on'
        digital_signature = request.FILES.get('digital_signature')
        if not terms:
            return HttpResponse('You must agree to the terms and conditions.')
        rental_agreement = RentalAgreement(
            property=property,
            renter=user,
            start_date=start_date,
            end_date=end_date,
            terms=terms,
            digital_signature=digital_signature 
        )
        rental_agreement.save()
        return redirect('thank')
        # return HttpResponse('submitted succesfully')
    return render(request, 'rental_agreement.html', {
        'property': property
        })

def adminproview(request):
    properties = Property.objects.all()  # Fetch all properties
    return render(request, 'adminproview.html', {'properties': properties})

def propertywelcom(request):
    return render(request,'propertywelcom.html')


def termsandconditions(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id)
    if request.method == 'POST':
        terms_and_conditions = request.POST.get('terms_and_conditions')
        if len(terms_and_conditions) > 255:
            pass
        else:
            property_instance.terms_and_conditions = terms_and_conditions
            property_instance.save()
            return redirect('termsandconditions', property_id=property_id)
    return render(request, 'termsandconditions.html', {'property': property_instance})

def ownerview(request):
    if request.session.get('user_id'):
        owner_name = request.session.get('name')
        print("Owner Name:",owner_name)
        owner=User.objects.get(name=owner_name)
        owner_properties = Property.objects.filter(owner=owner)
        print("Property:",owner_properties)
        rental_agreements = RentalAgreement.objects.filter(property__in=owner_properties)
        return render(request, 'ownerview.html', {
            'owner_name': owner_name,
            'rental_agreements': rental_agreements,
        })
    else:
        return redirect('login')


def accept_decline_agreement(request, agreement_id):
    if request.session.get('user_id'):
        rental_agreement = get_object_or_404(RentalAgreement, id=agreement_id)
        if request.method == "POST":
            action = request.POST.get('action')
            
            if action == "accept":
                try:
                    # Create PropertyRental entry
                    PropertyRental.objects.create(
                        user=rental_agreement.renter,
                        property=rental_agreement.property,
                        is_active=True,
                        rental_start_date=timezone.now()
                    )
                    
                    # Update property status
                    property = rental_agreement.property
                    property.is_rented = True
                    property.save()
                    
                    # Update rental agreement
                    rental_agreement.status = 1
                    if 'owner_digital_signature' in request.FILES:
                        rental_agreement.owner_digital_signature = request.FILES['owner_digital_signature']
                    rental_agreement.save()
                    
                    messages.success(request, 'Rental agreement accepted and property marked as rented successfully!')
                    
                except Exception as e:
                    messages.error(request, f'Error occurred while processing: {str(e)}')
                
            elif action == "decline":
                rental_agreement.status = 0
                rental_agreement.save()
                messages.success(request, 'Agreement declined successfully!')
            
            return redirect('ownerview')
    return redirect('login')

def rented_properties_view(request):
    rented_properties = RentalAgreement.objects.select_related('property', 'renter').all()
    return render(request, 'rented_properties.html', {'rented_properties': rented_properties})

def rented_properties_view(request):
    rented_properties = RentalAgreement.objects.select_related('property', 'renter').all()
    return render(request, 'rented_properties.html', {'rented_properties': rented_properties})


def buy_property(request, property_id):
    # Get the property object based on the ID from the URL
    property = get_object_or_404(Property, id=property_id)

    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        purchase_date = request.POST.get('purchase_date')
        payment_method = request.POST.get('payment_method')

        # Simulate processing the purchase (e.g., store transaction in the database)
        # Here, you can add logic to create a Purchase object or store the transaction

        # Send a confirmation email (optional)
        send_mail(
            'Property Purchase Confirmation',
            f'Dear {name},\n\nThank you for purchasing the property: {property.property_name}.',
            'from@example.com',  # Replace with your email
            [email],
            fail_silently=False,
        )

        # Add a success message and redirect to another page, e.g., a success page or property list
        messages.success(request, 'Property purchased successfully!')
        return redirect('property_list')  # Replace with the appropriate view for redirection

    # If GET request, render the form with the property details
    context = {
        'property': property,
    }
    return render(request, 'buy_property.html', context)



def userviewrental(request):
    user_id = request.session.get('user_id')
    print(user_id)
    if not user_id:
        return redirect('login')
    user=User.objects.get(id=user_id)
    print(user)
    rental_agreements = RentalAgreement.objects.all()
    print(rental_agreements)
    return render(request, 'userviewrental.html', {
        'rental_agreements': rental_agreements
    })

# def notification(request):
#     if request.session.get('user_id'):
#         user_id = request.session['user_id']
        
#         # Fetch all rental agreements that have been accepted (status=True) for the logged-in user
#         rental_agreements = RentalAgreement.objects.filter(renter_id=user_id, status=True).order_by('-notification_date')
        
#         # Fetch all unread messages where the sender is an owner and receiver is the logged-in user
#         unread_messages = Message.objects.filter(receiver_id=user_id, sender__role='owner', is_read=False).order_by('-timestamp')
#         return render(request, 'notification.html', {
#             'rental_agreements': rental_agreements,
#             'unread_messages': unread_messages,

#         })

#     return redirect('login')
def notification(request):
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        user = User.objects.get(id=user_id)
        
        # Debug prints
        print(f"\nChecking notifications for user ID: {user_id}")
        
        # Fetch rental agreements
        rental_agreements = RentalAgreement.objects.filter(
            renter_id=user_id, 
            status=True
        ).order_by('-notification_date')
        
        # Fetch unread regular messages
        unread_messages = Message.objects.filter(
            receiver_id=user_id,
            sender__role='owner',
            is_read=False,
            token_advance=False
        ).select_related('sender', 'property').order_by('-timestamp')
        
        # Fetch token messages
        token_advance_messages = Message.objects.filter(
            receiver_id=user_id,
            sender__role='owner',
            token_advance=True,
            token_status='accepted',
            is_read=False
        ).select_related('sender', 'property').order_by('-timestamp')
        
        # Debug prints
        print(f"Found {unread_messages.count()} unread messages")
        print(f"Found {token_advance_messages.count()} token messages")
        
        # Print details of each token message
        for msg in token_advance_messages:
            print(f"""
            Token Message Details:
            - ID: {msg.id}
            - Sender: {msg.sender.name} ({msg.sender.role})
            - Property: {msg.property.property_name}
            - Status: {msg.token_status}
            - Price: {msg.token_price}
            """)

        # Get maintenance request notifications
        maintenance_notifications = MaintenanceRequest.objects.filter(
            tenant=user,
            notification_date__isnull=True  # Only show unread notifications
        ).order_by('-updated_date')
        
        context = {
            'rental_agreements': rental_agreements,
            'unread_messages': unread_messages,
            'token_advance_messages': token_advance_messages,
            'maintenance_notifications': maintenance_notifications,
            'user': user
        }
        
        return render(request, 'notification.html', context)
    
    return redirect('login')

def clear_message(request, message_id):
    if request.session.get('user_id'):
        message = get_object_or_404(Message, id=message_id, receiver_id=request.session['user_id'])
        # Mark the message as read
        message.is_read = True
        message.save()
        return redirect('notification')
    return redirect('login')



def send_message(request, property_id):
    # Check if the user is logged in via session
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        
        if request.method == 'POST':
            message_content = request.POST.get('message')
            property = get_object_or_404(Property, id=property_id)
            owner = property.owner  # Assuming your Property model has an owner field
            
            # Validate message content
            if message_content:  # Check if message is not empty
                # Create a new message from the user to the owner
                Message.objects.create(
                    sender_id=user_id,  # Use user_id from session
                    receiver=owner,
                    property=property,
                    message=message_content
                )
                return redirect('conversation', property_id=property_id)
            else:
                # Handle the case where the message is empty
                return render(request, 'conversation.html', {
                    'property': property,
                    'error': 'Message cannot be empty.',  # Pass an error message to the template
                })
    
    # If the user is not authenticated, redirect to login
    return redirect('login')



def conversation(request, property_id):
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        user = get_object_or_404(User, id=user_id)
        property_instance = get_object_or_404(Property, id=property_id)
        messages = Message.objects.filter(
            property=property_instance,
            token_advance=False
        ).filter(
            Q(sender_id=user_id) | Q(receiver_id=user_id)
        ).order_by('timestamp')
        if request.method == "POST":
            if 'clear_messages' in request.POST:
                Message.objects.filter(property=property_instance).delete()
                return redirect('conversation', property_id=property_id)
            if 'token_price' in request.POST:
                token_price = request.POST.get('token_price')
                token_message = request.POST.get('token_message')
                Message.objects.create(
                    sender_id=user_id,
                    receiver_id=property_instance.owner.id,
                    property=property_instance,
                    message=token_message,
                    token_advance=True,
                    token_status='pending',
                    token_price=token_price
                )
                return redirect('conversation', property_id=property_instance.id)
            message_content = request.POST.get('message')
            if message_content:
                receiver_id = property_instance.owner.id if user_id != property_instance.owner.id else request.POST.get('receiver_id')
                Message.objects.create(
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    property=property_instance,
                    message=message_content
                )
                return redirect('conversation', property_id=property_instance.id)
        context = {
            'property': property_instance,
            'messages': messages,
            'user': user,
        }
        return render(request, 'conversation.html', context)
    return redirect('login')

def certificate(request, agreement_id):
    rental_agreement = get_object_or_404(RentalAgreement, id=agreement_id)
    context = {
        'agreement': rental_agreement,  # Rename this to match your template
    }
    return render(request, 'certificate.html', context)



# Views.py

def owner_conversation(request, property_id):
    if request.session.get('user_id'):
        owner_id = request.session['user_id']
        property_instance = get_object_or_404(Property, id=property_id, owner_id=owner_id)
        inquirer_id = request.GET.get('user_id')
        if inquirer_id:
            messages = Message.objects.filter(
                property=property_instance,
                sender_id__in=[owner_id, inquirer_id],
                receiver_id__in=[owner_id, inquirer_id]
            ).order_by('timestamp')
        else:
            messages = []
        if request.method == "POST":
            message_content = request.POST.get('message')
            if message_content and inquirer_id:
                Message.objects.create(
                    sender_id=owner_id,
                    receiver_id=inquirer_id,
                    property=property_instance,
                    message=message_content
                )
                return redirect(
                    f'/owner/conversation/{property_id}/?user_id={inquirer_id}')  # Redirect with inquirer_id
        context = {
            'property': property_instance,
            'messages': messages,
            'inquirer_id': inquirer_id
        }
        return render(request, 'owner_conversation.html', context)
    return redirect('login')



def clear_messages(request, sender_id, property_id):
    # Check if the user is logged in via session
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        
        # Get the property for which messages are to be cleared
        property = get_object_or_404(Property, id=property_id)

        # Clear all messages related to the property and sender
        Message.objects.filter(property=property, sender_id=sender_id).delete()

        # Redirect back to the notification page
        return redirect('notification_owner')
    
    # If the user is not authenticated, redirect to login
    return redirect('login')


def owner_conversation_viewuser(request, property_id):
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        
        # Get the property, ensuring it belongs to the logged-in owner
        property = get_object_or_404(Property, id=property_id, owner_id=user_id)
        
        # Get distinct senders of messages related to the property, excluding the owner
        messages = Message.objects.filter(property=property).exclude(sender_id=user_id).values('sender_id').distinct()
        
        # Get user objects for those sender IDs
        users = User.objects.filter(id__in=[msg['sender_id'] for msg in messages])
        # Pass property and users to the template
        return render(request, 'owner_conversation_viewuser.html', {'property': property, 'users': users})
    return redirect('login')

def notification_owner(request):
    owner_id = request.session.get('user_id')
    if owner_id:
        if request.method == "POST":
            message_id = request.POST.get('message_id')
            status = request.POST.get('status')
            
            if message_id and status:
                try:
                    # Get the original token request message
                    original_message = Message.objects.get(id=message_id)
                    print(f"Processing message ID: {message_id}, Status: {status}")
                    
                    if status == 'accepted':
                        # Create a new notification message for the user
                        notification_message = Message.objects.create(
                            sender_id=owner_id,  # Owner is sending the response
                            receiver=original_message.sender,  # Send to the original requester
                            property=original_message.property,
                            message=f"Your token request for {original_message.property.property_name} has been accepted",
                            token_advance=True,
                            token_status='accepted',
                            token_price=original_message.token_price,
                            is_read=False
                        )
                        print(f"Created new notification message ID: {notification_message.id}")
                    
                    # Update the original message
                    original_message.token_status = status
                    original_message.is_read = True
                    original_message.save()
                    
                    print(f"Updated original message status to: {status}")
                    return redirect('notification_owner')
                    
                except Message.DoesNotExist:
                    print(f"Message with ID {message_id} not found")
                except Exception as e:
                    print(f"Error processing message: {str(e)}")

        # Get unread messages (non-token)
        unread_messages = Message.objects.filter(
            receiver_id=owner_id,
            sender__role='user',
            is_read=False,
            token_advance=False
        ).select_related('property', 'sender')

        # Get token request messages
        token_messages = Message.objects.filter(
            receiver_id=owner_id,
            sender__role='user',
            is_read=False,
            token_advance=True,
            token_status='pending'
        ).select_related('property', 'sender')

        # Group regular messages by sender and property
        grouped_messages = {}
        for message in unread_messages:
            key = (message.sender, message.property)
            if key not in grouped_messages:
                grouped_messages[key] = []
            grouped_messages[key].append(message)

        # Add maintenance request notifications
        maintenance_notifications = MaintenanceRequest.objects.filter(
            property__owner_id=owner_id,
            status='reported',
            notification_date__isnull=True  # Only show unread notifications
        ).select_related('property', 'tenant').order_by('-reported_date')

        owner_name = User.objects.get(id=owner_id).name
        
        return render(request, 'notification_owner.html', {
            'grouped_messages': grouped_messages,
            'token_messages': token_messages,
            'maintenance_notifications': maintenance_notifications,
            'owner_name': owner_name
        })
    return redirect('login')

# Add new view for clearing maintenance notifications
def clear_maintenance_notification(request, request_id):
    if request.session.get('user_id'):
        maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
        maintenance_request.notification_date = timezone.now()
        maintenance_request.save()
        return redirect('notification_owner')
    return redirect('login')

def clear_owner_messages(request, property_id):
    if request.session.get('user_id'):
        owner_id = request.session['user_id']
        property_instance = get_object_or_404(Property, id=property_id, owner_id=owner_id)
        inquirer_id = request.GET.get('user_id')
        if inquirer_id:
            Message.objects.filter(
                property=property_instance,
                sender_id__in=[owner_id, inquirer_id],
                receiver_id__in=[owner_id, inquirer_id]
            ).delete()
        return redirect(f'/owner/conversation/{property_id}/?user_id={inquirer_id}')
    return redirect('login')


def buyer(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user = get_object_or_404(User, id=user_id)
        rental_agreement_id = request.GET.get('agreement_id')
        rental_agreement = get_object_or_404(RentalAgreement, id=rental_agreement_id, renter=user)
        
        if request.method == 'POST':
            payment = Payment.objects.create(
                rental_agreement=rental_agreement,
                user=user,
                amount=rental_agreement.property.monthly_rent,
                billing_address=request.POST.get('billing_address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                pin_code=request.POST.get('pin_code'),
                payment_status='pending',
                transaction_id=f"TXN_{int(time.time())}"
            )
            return redirect('biling_details', payment_id=payment.id)
            
        return render(request, 'buyer.html', {
            'user': user,
            'rental_agreement': rental_agreement
        })
    return redirect('login')

def biling_details(request, payment_id):
    if 'user_id' in request.session:
        payment = get_object_or_404(Payment, id=payment_id)
        return render(request, 'biling_details.html', {
            'payment': payment,
            'rental_agreement': payment.rental_agreement,
            'property': payment.rental_agreement.property,
            'user': payment.user,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID  # Use from Django settings
        })
    return redirect('login')

def thank(request):
    return render(request, 'thank.html')

def feedback_page(request, property_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = get_object_or_404(User, id=user_id)
    property = get_object_or_404(Property, id=property_id)
    feedback_list = Feedback.objects.filter(property=property)\
        .select_related('user')\
        .order_by('-created_at')
    user_feedback = feedback_list.filter(user=user)
    other_feedback = feedback_list.exclude(user=user)
    if request.method == "POST":
        if request.POST.get('delete_feedback'):
            feedback_id = request.POST.get('feedback_id')
            feedback = get_object_or_404(Feedback, id=feedback_id, user=user)
            feedback.delete()
            return JsonResponse({'status': 'success'})
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            try:
                Feedback.objects.create(
                    property=property,
                    user=user,
                    rating=int(rating),
                    comment=comment
                )
                return JsonResponse({
                    'status': 'success',
                    'message': 'Feedback submitted successfully!'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Please provide both rating and comment'
            }, status=400)
    
    return render(request, 'feedback_page.html', {
        'property': property,
        'feedback_list': feedback_list,
        'user_feedback': user_feedback,
        'other_feedback': other_feedback,
        'current_user': user
    })


# views.py
# views.py
import razorpay
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Payment
from django.conf import settings

from decimal import Decimal

def create_order(request, payment_id):
    if 'user_id' in request.session:
        payment = get_object_or_404(Payment, id=payment_id)
        amount_in_paise = int(payment.amount * Decimal(100))

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

        try:
            order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f'receipt_{payment.id}',
                'payment_capture': '1'
            }
            razorpay_order = client.order.create(data=order_data)
            payment.transaction_id = razorpay_order['id']
            payment.save()

            return JsonResponse({
                'id': razorpay_order['id'],
                'amount': razorpay_order['amount'],
                'currency': razorpay_order['currency']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return redirect('login')

def payment_success(request):
    payment_id = request.GET.get('payment_id')
    if payment_id:
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
            payment = client.payment.fetch(payment_id)

            if payment['status'] == 'captured':
                payment_record = get_object_or_404(Payment, transaction_id=payment['order_id'])
                payment_record.status = 'Paid'
                payment_record.save()
                return HttpResponse("Payment successful!")
            else:
                return HttpResponse("Payment verification failed.")
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")
    else:
        return HttpResponse("Payment ID not found.")

def owner_feedback_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    owner = get_object_or_404(User, id=user_id)
    properties = Property.objects.filter(owner=owner)
    feedback_list = Feedback.objects.filter(property__in=properties).select_related('user', 'property').order_by('-created_at')
    
    return render(request, 'owner_feedback_view.html', {
        'feedback_list': feedback_list,
        'owner_name': owner.name,
    })

def admin_feedback(request):
    # Ensure admin session is active
    admin_id = request.session.get('admin_id')
    # Retrieve all feedback, including related User and Property details
    feedbacks = Feedback.objects.select_related('user', 'property__owner').order_by('-created_at')

    # Debugging: Check if feedbacks are being fetched
    print(f"Feedbacks retrieved: {feedbacks}")

    # Pass feedback to the template
    return render(request, 'admin_feedback.html', {'feedbacks': feedbacks})
    
def proceedtopayment(request):
    if not request.session.get('user_id'): 
        return redirect('login')
    user_id = request.session['user_id']
    message_id = request.GET.get('message_id')
    if not message_id: 
        return redirect('notification')
    try:
        user = User.objects.get(id=user_id)
        message = Message.objects.get(
            id=message_id, 
            receiver_id=user_id, 
            token_advance=True, 
            token_status='accepted'
        )
        existing_payment = TokenPayment.objects.filter(
            message=message, 
            tenant=user
        ).first()
        user_data = {
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'address': user.address
        }
        if existing_payment:
            user_data.update({
                'billing_address': existing_payment.billing_address,
                'city': existing_payment.city,
                'state': existing_payment.state,
                'pin_code': existing_payment.pin_code
            })
        if request.method == 'POST':
            token_payment, created = TokenPayment.objects.update_or_create(
                message=message,
                tenant=user,
                defaults={
                    'owner': message.sender,
                    'property': message.property,
                    'amount': message.token_price,
                    'billing_address': request.POST.get('billing_address'),
                    'city': request.POST.get('city'),
                    'state': request.POST.get('state'),
                    'pin_code': request.POST.get('pin_code')
                }
            )
            request.session['token_payment_id'] = token_payment.id
            return redirect('proceedtopaymentview')
        return render(request, 'proceedtopayment.html', {
            'user_data': user_data,
            'token_price': message.token_price,
            'property': message.property,
            'message': message
        })
    except (User.DoesNotExist, Message.DoesNotExist):
        return redirect('notification')

def proceedtopaymentview(request):
    if not request.session.get('token_payment_id'):
        return redirect('notification')
    try:
        payment = TokenPayment.objects.select_related('property', 'tenant').get(
            id=request.session['token_payment_id']
        )
        context = {
            'payment_id': payment.id,
            'property': {
                'name': str(payment.property.property_name),
                'price': float(payment.property.price)
            },
            'token_amount': float(payment.amount),
            'tenant': {
                'name': str(payment.tenant.name),
                'email': str(payment.tenant.email),
                'phone': str(payment.tenant.phone)
            },
            'billing_address': str(payment.billing_address),
            'city': str(payment.city),
            'state': str(payment.state),
            'pin_code': str(payment.pin_code),
            'razorpay_key_id': settings.RAZORPAY_KEY_ID
        }
        return render(request, 'proceedtopaymentview.html', context)
    except TokenPayment.DoesNotExist:
        return redirect('notification')

from decimal import Decimal
def create_ordersss(request, payment_id):
    if not request.session.get('user_id'):
        return JsonResponse({'error': 'User not authenticated'}, status=401)
    try:
        payment = get_object_or_404(TokenPayment, id=payment_id)
        amount_in_paise = int(payment.amount * Decimal(100))
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'tkn_{payment.id}_{int(time.time())}',
            'payment_capture': '1'
        }
        order = client.order.create(data=order_data)
        payment.transaction_id = order['id']
        payment.save()
        return JsonResponse(order)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def token_advance_list(request):
    if not request.session.get('admin_email'):
        return redirect('login')
        
   # Fetch all token payment requests with related property and tenant information
    token_requests = TokenPayment.objects.select_related('property', 'tenant').all()

    # Extract distinct property names and associated details
    context = {
        'token_requests': token_requests,
    }
    return render(request, 'token_advance_list.html', context)




from django.http import JsonResponse
from google.cloud import dialogflow_v2 as dialogflow

PROJECT_ID = 'rentbot-yijh'  # Replace with your Dialogflow project ID

def chat_with_bot(request):
    # Get the user message from the request
    user_message = request.GET.get('message', '')

    # Set up Dialogflow session
    session_id = "12345"  # You can use a unique ID for each user
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, session_id)

    # Prepare the text input
    text_input = dialogflow.TextInput(text=user_message, language_code="en")
    query_input = dialogflow.QueryInput(text=text_input)

    # Send the request to Dialogflow
    response = session_client.detect_intent(request={"session": session, "query_input": query_input})
    bot_reply = response.query_result.fulfillment_text

    # Send the bot's reply back to the user
    return JsonResponse({"response": bot_reply})

def chatbot_page(request):
    return render(request, 'chatbot.html')


# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import Property
from django.db.models import Q

from django.http import JsonResponse
from django.db.models import Q

def owner_property_data(request):
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        # Fetch properties for the logged-in owner
        properties = Property.objects.filter(owner_id=user_id)
        
        # Get properties that have rental agreements
        properties_with_agreements = RentalAgreement.objects.filter(
            property__owner_id=user_id,
            status=True  # Only count approved rental agreements
        ).values_list('property_id', flat=True)
        
        # Count total properties (without excluding any)
        total_properties = properties.count()
        
        # Count rented properties (either marked as rented or has an active rental agreement)
        rented_count = properties.filter(
            Q(is_rented=True) | Q(id__in=properties_with_agreements)
        ).distinct().count()
        
        # Count properties for sale
        for_sale_count = properties.filter(listing_type__in=['Sale', 'Both']).count()
         # Summing all relevant counts
        total_count = rented_count + for_sale_count
        
        # Get property type distribution
        property_types = {
            'Apartment': properties.filter(property_type='Apartment').count(),
            'House': properties.filter(property_type='House').count()
        }
        
        # Get listing type distribution
        listing_types = {
            'Rent': properties.filter(listing_type='Rent').count(),
            'Sale': properties.filter(listing_type='Sale').count(),
            'Both': properties.filter(listing_type='Both').count()
        }

        data = {
            'total': total_count,  # Ensure this includes all properties
            'rented': rented_count,
            'for_sale': for_sale_count,
            'property_types': property_types,
            'listing_types': listing_types
        }
        return JsonResponse(data)

    return JsonResponse({'error': 'Unauthorized'}, status=403)



def owner_dashboard(request):
    return render(request, 'owner_dashboard.html')

def service_providers(request):
    return render(request, 'service_providers.html')



def maintanence(request):
    return render(request, 'maintanence')

def maintenance_request(request, property_id):
    # First check if user is logged in via session
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to submit maintenance requests')
        return redirect('login')  # Redirect to your login page
    
    try:
        # Get the logged-in user
        user = User.objects.get(id=user_id)
        
        # Get the property and verify the user has an active rental
        property = get_object_or_404(Property, id=property_id)
        rental = get_object_or_404(PropertyRental, 
                                property=property, 
                                user=user, 
                                is_active=True)

        if request.method == 'POST':
            try:
                # Create maintenance request
                maintenance = MaintenanceRequest.objects.create(
                    property=property,
                    tenant=user,  # Use the user from session
                    title=request.POST.get('title'),
                    description=request.POST.get('description'),
                    priority=request.POST.get('priority'),
                    status='reported',
                    reported_date=timezone.now()
                )

                # Handle image upload
                if 'image' in request.FILES:
                    maintenance.image = request.FILES['image']
                    maintenance.save()

                # Send email notification to property owner
                send_mail(
                    subject=f'New Maintenance Request - {property.property_name}',
                    message=f"""
                    A new maintenance request has been submitted:
                    
                    Property: {property.property_name}
                    Issue: {maintenance.title}
                    Priority: {maintenance.priority}
                    Description: {maintenance.description}
                    
                    Please log in to view the details and take action.
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[property.owner.email],
                    fail_silently=False,
                )

                messages.success(request, 'Maintenance request submitted successfully!')
                return redirect('userpage')  # or wherever you want to redirect after success

            except Exception as e:
                messages.error(request, f'Error submitting maintenance request: {str(e)}')
                return render(request, 'maintenance.html', {
                    'property': property,
                    'error': str(e),
                    'user': user  # Pass user to template
                })

        return render(request, 'maintenance.html', {
            'property': property,
            'user': user  # Pass user to template
        })
        
    except User.DoesNotExist:
        messages.error(request, 'User session expired. Please login again.')
        return redirect('login')
    except PropertyRental.DoesNotExist:
        messages.error(request, 'You are not authorized to submit maintenance requests for this property.')
        return redirect('userpage')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('userpage')

@require_POST
def update_maintenance_status(request, request_id):
    try:
        data = json.loads(request.body)
        maintenance_request = MaintenanceRequest.objects.get(id=request_id)
        maintenance_request.status = data['status']
        if data['status'] == 'completed':
            maintenance_request.completion_date = timezone.now()
        maintenance_request.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def update_maintenance_notes(request, request_id):
    try:
        data = json.loads(request.body)
        maintenance_request = MaintenanceRequest.objects.get(id=request_id)
        maintenance_request.owner_notes = data['notes']
        maintenance_request.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



def owner_maintenance_requests(request):
    # Check if owner is logged in
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please login to view maintenance requests')
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        # Get all maintenance requests for properties owned by this user
        maintenance_requests = MaintenanceRequest.objects.filter(
            property__owner_id=user_id  # Changed from property__owner=user
        ).select_related('property', 'tenant').order_by('-reported_date')
        
        # Group requests by status
        pending_requests = maintenance_requests.filter(status='reported')
        in_progress_requests = maintenance_requests.filter(status='in_progress')
        completed_requests = maintenance_requests.filter(status='completed')
        
        context = {
            'pending_requests': pending_requests,
            'in_progress_requests': in_progress_requests,
            'completed_requests': completed_requests,
            'user': user
        }
        
        return render(request, 'owner_maintenance.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'User session expired. Please login again.')
        return redirect('login')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def household_items(request):
    if not request.session.get('user_id'):
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    
    if request.method == 'POST':
        try:
            item = HouseholdItem.objects.create(
                name=request.POST['name'],
                description=request.POST['description'],
                category=request.POST['category'],
                condition=request.POST['condition'],
                price=request.POST['price'],
                brand=request.POST.get('brand'),
                seller=user,
                is_available=True,
                status=True
            )
            
            images = request.FILES.getlist('images')
            for image in images:
                HouseholdItemImage.objects.create(item=item, image=image)
            
            messages.success(request, 'Item added successfully!')
            return redirect('household_items')
            
        except Exception as e:
            messages.error(request, str(e))
            return redirect('household_items')
    
    items = HouseholdItem.objects.filter(status=True, is_available=True).order_by('-posted_date')
    # Get user's wishlist items
    wishlist_items = HouseholdItemWishlist.objects.filter(user=user).values_list('item_id', flat=True)
    
    return render(request, 'household_items.html', {
        'items': items, 
        'user': user,
        'wishlist_items': list(wishlist_items)  # Convert to list for template use
    })

def rental_compliance(request):
  
    return render(request, 'rental_compliance.html')



import pickle
import os
import numpy as np
from django.shortcuts import render
from django.http import JsonResponse

# Get the base directory dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Build the full path to the model file
MODEL_PATH = os.path.join(BASE_DIR, 'ml_model', 'ml_models', 'rental_price_model.pkl')

# Load the trained model
try:
    with open(MODEL_PATH, 'rb') as file:
        model = pickle.load(file)
except FileNotFoundError:
    model = None
    print(f"Model file not found at: {MODEL_PATH}")

def predict_price(request):
    if request.method == 'POST':
        # Check if the model was loaded successfully
        if not model:
            return JsonResponse({'error': 'Model file not found or failed to load.'})

        try:
            # Get input values from the request
            area = float(request.POST.get('area'))
            bedrooms = int(request.POST.get('bedrooms'))
            bathrooms = int(request.POST.get('bathrooms'))

            # Prepare data for prediction
            input_data = np.array([[area, bedrooms, bathrooms]])
            predicted_price = model.predict(input_data)[0]

            # Return the predicted price
            return JsonResponse({'predicted_price': f"{predicted_price:.2f}"})

        except Exception as e:
            # Handle any errors during prediction
            return JsonResponse({'error': str(e)})

    return render(request, 'predict_price.html')

def admin_household_items(request):
    # Get all household items with their related data
    items = HouseholdItem.objects.select_related('seller').prefetch_related('images').all().order_by('-posted_date')
    
    context = {
        'items': items
    }
    return render(request, 'admin_household_items.html', context)

def get_seller_details(request, seller_id):
    try:
        seller = User.objects.get(id=seller_id)
        return JsonResponse({
            'name': seller.name,
            'phone': seller.phone if seller.phone else 'Not provided'
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'Seller not found'}, status=404)

@require_POST
def toggle_household_wishlist(request, item_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'Please login first'})
    
    try:
        user = User.objects.get(id=user_id)
        item = HouseholdItem.objects.get(id=item_id)
        
        wishlist_item, created = HouseholdItemWishlist.objects.get_or_create(
            user=user,
            item=item
        )
        
        if not created:
            # Item was already in wishlist, so remove it
            wishlist_item.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Item removed from wishlist',
                'in_wishlist': False
            })
        
        return JsonResponse({
            'status': 'success',
            'message': 'Item added to wishlist',
            'in_wishlist': True
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

def payment_page(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    # Get the item_id from the URL parameters
    item_id = request.GET.get('item_id')
    if not item_id:
        return redirect('household_items')
    
    user = get_object_or_404(User, id=user_id)
    item = get_object_or_404(HouseholdItem, id=item_id)
    
    return render(request, 'payment_page.html', {
        'user': user,
        'item': item  # Pass the item to the template
    })


from django.shortcuts import render, get_object_or_404
from .models import User, HouseholdItem

def order_summary(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    # Get and validate item_id
    item_id = request.GET.get('item_id')
    if not item_id:
        messages.error(request, 'No item selected')
        return redirect('household_items')
    
    try:
        user = get_object_or_404(User, id=user_id)
        item = get_object_or_404(HouseholdItem, id=item_id)
        seller = item.seller
        
        context = {
            'buyer_name': user.name,
            'buyer_phone': user.phone,
            'seller_name': seller.name,
            'seller_phone': seller.phone,
            'item_name': item.name,
            'item_price': item.price,
            'item_condition': item.condition,
        }
        
        return render(request, 'order_summary.html', context)
    
    except (ValueError, HouseholdItem.DoesNotExist):
        messages.error(request, 'Invalid item selected')
        return redirect('household_items')





