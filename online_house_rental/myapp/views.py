# Create your views here.
from django.shortcuts import render,redirect,get_object_or_404
from .models import User,Property,PropertyImage,Adminm
from django.contrib import messages
import logging
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.core.mail import send_mail


def index(request):
    return render(request, 'index.html')
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        admin = Adminm.objects.filter(email=email, password=password).first() 
        if admin:
            request.session['admin_email'] = admin.email
            return redirect('admin')
        user = User.objects.filter(email=email, password=password).first()
        if user:
            request.session['user_id'] = user.id
            request.session['name'] = user.name
            request.session['role'] = user.role
            if user.role == 'owner':
                return redirect('owner')
            elif user.role == 'user':
                return redirect('userpage')
        else:
            return render(request, 'login.html', {'error': 'Invalid email or password'})
    return render(request, 'login.html')
def register(request):
    if request.method == 'POST':
        name =request.POST.get('name')
        address=request.POST.get('address')
        email =request.POST.get('email')
        phone=request.POST.get('contact')
        password =request.POST.get('password')
        confirm_password =request.POST.get('confirmPassword')
        role = request.POST.get('role')
        if password != confirm_password:
            return render(request, 'register.html', {'error': 'Passwords do not match'})
        user = User(name=name, address=address, email=email, phone=phone, password=password, role=role)
        user.save()
        messages.success(request, 'Registration successful')
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
def userpage(request):
        if request.session.get('user_id'):
            user_name = request.session.get('name')  # Get user's name from session
            return render(request, 'userpage.html', {'user_name': user_name})
        else:
            return redirect('login')

    # return render(request, 'userpage.html')
def owner(request):
    if request.session.get('user_id'):
        owner_name = request.session.get('name')  # Get owner's name from session
        return render(request, 'owner.html', {'owner_name': owner_name})
    else:
        return redirect('login') 
    # return render(request, 'owner.html')
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
def propertyview(request,id):
    property_instance = Property.objects.get(id=id)
    return render(request, 'propertyview.html',{'property': property_instance})
def propertypage(request):
    properties = Property.objects.all()  # Fetch all properties
    return render(request, 'propertypage.html', {'properties': properties})
def house(request):
    return render(request, 'house.html')
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
        owner_id = request.session.get('user_id')
        owner = User.objects.get(id=owner_id)
        property_instance = Property.objects.create(
            property_name=property_name,description=description,address=address,city=city,state=state,
            price=price,property_type=property_type,listing_type=listing_type,owner=owner
        )
        property_photos = request.FILES.getlist('property_photos')
        for photo in property_photos:
            PropertyImage.objects.create(property=property_instance, image=photo)
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
    


