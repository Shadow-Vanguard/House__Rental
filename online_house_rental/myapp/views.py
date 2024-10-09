from django.shortcuts import render,redirect,get_object_or_404
from .models import User,Property,PropertyImage,Adminm,Wishlist,RentalAgreement
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
from django.http import HttpResponse

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout(request):
    request.session.flush()  # This clears the session data
    return redirect('login')


def index(request):
    return render(request, 'index.html')


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
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        email = request.POST.get('email')
        phone = request.POST.get('contact')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        role = request.POST.get('role')
        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {
                'email_error': 'An account with this email already exists.',
                'name': name,
                'address': address,
                'contact': phone,
                'role': role,
            })
        # Check if the passwords match
        if password != confirm_password:
            return render(request, 'register.html', {
                'error': 'Passwords do not match.',
                'name': name,
                'address': address,
                'contact': phone,
                'email': email,
                'role': role,
            })

        # Create and save the new user
        user = User(name=name, address=address, email=email, phone=phone, password=password, role=role)
        user.save()

        # Send registration success email
        send_mail(
            'Registration Successful',
            f'Hello {name},\n\nThank you for registering!\n\nBest regards,\nYour Team',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return redirect('login')

    return render(request, 'register.html')



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
        delete_property_id = request.POST.get('delete_property')
        property_id = request.POST.get('property_id')
        if delete_image_id:
            property_instance = get_object_or_404(Property, id=property_id)
            image_to_delete = PropertyImage.objects.filter(id=delete_image_id, property=property_instance).first()
            if image_to_delete:
                image_to_delete.delete()
                return JsonResponse({'status': 'success'})
        if delete_property_id:
            property_instance = get_object_or_404(Property, id=delete_property_id)
            property_instance.delete()
            return redirect('ownerproperty')
        property_instance = get_object_or_404(Property, id=property_id)
        property_instance.property_name = request.POST.get('property_name')
        property_instance.description = request.POST.get('description')
        property_instance.address = request.POST.get('address')
        property_instance.city = request.POST.get('city')
        property_instance.state = request.POST.get('state')
        property_instance.price = request.POST.get('price')
        property_instance.property_type = request.POST.get('property_type')
        property_instance.listing_type = request.POST.get('listing_type')
        monthly_rent = request.POST.get('monthly_rent')
        if monthly_rent:  # Check if the monthly rent was provided
            property_instance.monthly_rent = int(monthly_rent)  
        property_instance.save()
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
    property = get_object_or_404(Property, id=property_id)
    owner = property.owner
    messages = Message.objects.filter(property=property)

    if request.method == 'POST':
        message_text = request.POST.get('message')
        Message.objects.create(
            sender=request.user,
            receiver=owner,
            property=property,
            message=message_text,
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




def user_chat_view(request, owner_id):
    owner = get_object_or_404(User, id=owner_id)
    messages = Message.objects.filter(sender=request.user, receiver=owner) | Message.objects.filter(sender=owner, receiver=request.user)
    messages = messages.order_by('timestamp')
    
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            # Save the new message
            Message.objects.create(sender=request.user, receiver=owner, message=message_content)
            return redirect('user_chat', owner_id=owner_id)
    
    return render(request, 'user_chat.html', {'messages': messages, 'owner': owner})


def owner_chat_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(sender=request.user, receiver=user) | Message.objects.filter(sender=user, receiver=request.user)
    messages = messages.order_by('timestamp')
    
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            # Save the new message
            Message.objects.create(sender=request.user, receiver=user, message=message_content)
            return redirect('owner_chat', user_id=user_id)
    
    return render(request, 'owner_chat.html', {'messages': messages, 'user': user})


@login_required
def rental_agreement(request, property_id):
    # Retrieve the property based on its ID
    property = get_object_or_404(Property, id=property_id)

    if request.method == 'POST':
        # Retrieve data from the form submission
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        monthly_rent = request.POST.get('monthly_rent')
        terms = request.POST.get('terms') == 'on'
        digital_signature = request.FILES.get('digital_signature')  # For image-based signature

        # Check if terms were accepted
        if not terms:
            return HttpResponse('You must agree to the terms and conditions.')

        # Create a new RentalAgreement entry
        rental_agreement = RentalAgreement(
            property=property,
            renter=request.user,  # The current logged-in user
            start_date=start_date,
            end_date=end_date,
            monthly_rent=monthly_rent,
            terms=terms,
            digital_signature=digital_signature  # Save the uploaded signature image
        )
        rental_agreement.save()

        return HttpResponse('Rental agreement submitted successfully!')

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