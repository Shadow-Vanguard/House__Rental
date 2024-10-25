from django.shortcuts import render,redirect,get_object_or_404
from .models import User,Property,PropertyImage,Adminm,Wishlist,RentalAgreement,Message
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
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, get_object_or_404


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
        
        # Retrieve the logged-in user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect('login')  # Redirect to login if user not found
        properties = Property.objects.filter(is_verified=True)  # Only show verified properties

        # # Retrieve all properties (or filter them later based on the owner)
        # properties = Property.objects.all()
         # Only show active (status=True) and verified (is_verified=True) properties
        properties = Property.objects.filter(is_verified=True, status=True)
        # Get search parameters from the GET request
        location = request.GET.get('location', '')
        category = request.GET.get('category', '')
        price = request.GET.get('price', '')
        bhk = request.GET.get('bhk', '')

        # Filter properties based on the search criteria
        if location:
            properties = properties.filter(city__icontains=location) | properties.filter(state__icontains=location)
        
        
        if category:
            properties = properties.filter(property_type__iexact=category)
        
        if price:
            try:
                max_price = float(price)
                properties = properties.filter(price__lte=max_price)
            except ValueError:
                pass  # If price is not a valid number, skip this filter
        
        if bhk:
            try:
                bhk_value = int(bhk)
                properties = properties.filter(beds=bhk_value)
            except ValueError:
                pass  # If bhk is not a valid number, skip this filter

        # Pass the filtered properties to the template
        context = {
            'user': user,
            'properties': properties,
            'request': request  # Pass the request to the template for showing the form values
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
    if request.method == 'POST':
        if 'add_to_wishlist' in request.POST:
            user_id = request.session.get('user_id')
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
    user.status = False  # Set the status to inactive
    user.save()

    # Send an email notification
    send_mail(
        'Account Deactivation',
        f'Hello {user.name},\n\nYour account has been deactivated. If you have any questions, please contact support.',
        'your_email@example.com',  # Replace with your email or from_email
        [user.email],
        fail_silently=False,
    )

    messages.success(request, 'User has been deactivated and notified via email.')
    
    # Redirect to manage_users with the role parameter
    return redirect('manage_users', role=user.role)  # Adjust user.role based on how you retrieve it

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



def rental_agreement(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    user_id = request.session.get('user_id')
    print("User id:",user_id)
    if not user_id:
        return redirect('login')
    user = get_object_or_404(User, id=user_id)
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
        return HttpResponseRedirect('thank')
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
                rental_agreement.status = True
                
                # Check if there's a digital signature uploaded
                if 'owner_digital_signature' in request.FILES:
                    rental_agreement.owner_digital_signature = request.FILES['owner_digital_signature']  # Save the uploaded signature image
                
                # Update notification date when the agreement is accepted
                rental_agreement.notification_date = timezone.now()
                rental_agreement.save()

                # Send email notification to the renter
                subject = 'Your Rental Agreement has been Approved'
                message = (
                    f"Dear {rental_agreement.renter.name},\n\n"  # Using the renter's username or name
                    "Your rental agreement has been approved. You can continue with the next steps.\n\n"
                    "Thank you for using our service!\n"
                    "Best regards,\n"
                    "The Rental Team"
                )
                recipient_list = [rental_agreement.renter.email]  # Correctly referencing the renter's email

                # Sending the email
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=False,  # Set to True to suppress errors
                )
            
            elif action == "decline":
                rental_agreement.status = False
            
            rental_agreement.save()  # Save the status change and signature
            
            return redirect('ownerview')  # Redirect to the owner view after processing

    return redirect('login')  # Redirect if user is not authenticated


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

def notification(request):
    if request.session.get('user_id'):
        user_id = request.session['user_id']
        
        # Fetch all rental agreements that have been accepted (status=True) for the logged-in user
        rental_agreements = RentalAgreement.objects.filter(renter_id=user_id, status=True).order_by('-notification_date')
        
        # Fetch all unread messages where the sender is an owner and receiver is the logged-in user
        unread_messages = Message.objects.filter(receiver_id=user_id, sender__role='owner', is_read=False).order_by('-timestamp')
        
        return render(request, 'notification.html', {
            'rental_agreements': rental_agreements,
            'unread_messages': unread_messages
        })

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
        property = get_object_or_404(Property, id=property_id)
        messages = Message.objects.filter(
            property=property,
            token_advance=False
        ).filter(
            Q(sender_id=user_id) | Q(receiver_id=user_id)
        ).order_by('timestamp')
        if request.method == "POST":
            if 'token_price' in request.POST:
                token_price = request.POST.get('token_price')
                token_message = request.POST.get('token_message')
                Message.objects.create(
                    sender_id=user_id,
                    receiver_id=property.owner.id,
                    property=property,
                    message=token_message,
                    token_advance=True,
                    token_status='pending',
                    token_price=token_price
                )
                return redirect('conversation', property_id=property.id)
            message_content = request.POST.get('message')
            if message_content:
                receiver_id = property.owner.id if user_id != property.owner.id else request.POST.get('receiver_id')
                Message.objects.create(
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    property=property,
                    message=message_content
                )
                return redirect('conversation', property_id=property.id)
        context = {
            'property': property,
            'messages': messages,
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
                Message.objects.filter(id=message_id).update(token_status=status, is_read=True)
                return redirect('notification_owner')

        unread_messages = Message.objects.filter(
            receiver_id=owner_id,
            sender__role='user',
            is_read=False,
            token_advance=False
        ).select_related('property', 'sender').order_by('-timestamp')
        grouped_messages = {}
        for message in unread_messages:
            key = (message.sender, message.property)
            if key not in grouped_messages:
                grouped_messages[key] = []
            grouped_messages[key].append(message)

        token_messages = Message.objects.filter(
            receiver_id=owner_id,
            sender__role='user',
            is_read=False,
            token_advance=True
        ).select_related('property', 'sender').order_by('-timestamp')
        owner_name = User.objects.get(id=owner_id).name
        return render(request, 'notification_owner.html', {
            'grouped_messages': grouped_messages,
            'token_messages': token_messages,
            'owner_name': owner_name
        })
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
    return render(request, 'buyer.html')

def biling_details(request):
    return render(request, 'biling_details.html')

def thank(request):
    return render(request, 'thank.html')
