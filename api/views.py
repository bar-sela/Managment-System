import random
from django.http import HttpResponse
from django.shortcuts import render
from requests import Response, request
from api import serializer as api_serializer
from rest_framework.response import Response  # Corrected import
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from userauths.models import User
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from backend.settings import EMAIL_HOST_USER
from django.contrib.auth.hashers import check_password
from cryptography.fernet import Fernet

# Create your views here.



class MyTokenObtainPairView(TokenObtainPairView): # like viewSet
    serializer_class = api_serializer.MyTokenObtainPairSerializer  # this custom serializer will be used to process the request data.
    

class RegisterView(generics.CreateAPIView): #The CreateAPIView class in Django REST Framework (DRF) is specifically designed for handling HTTP POST requests to create new instances of a model. It does not handle GET requests by default.
    queryset = User.objects.all() 
    serializer_class = api_serializer.RegisterSerializer
    
    # called called during the is_save
 

def generate_random_otp(length=7):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView): # specifically designed to handle GET requests for retrieving a single object
    queryset = User.objects.all() 
    serializer_class = api_serializer.UserSerializer

    def get_object(self ):  # the following:a. Calls self.get_object() to retrieve the object , b. Passes the retrieved object to the serializer ,c. Returns the serialized data in the response

        email = self.kwargs.get('email')  # {'email': 'nbarsela@gmail.com'}
    
        user = User.objects.filter(email=email).first()
    
        if user:
            # Create a new RefreshToken object for the user
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            user.refresh_token = str(refresh)
            
            
            print(f"New Access Token: {access_token}")
            print(f"New Refresh Token: {refresh}")
            user.otp = generate_random_otp()
            
            # Generate the link
            link = f"http://localhost:5173/create-new-password/?otp={user.otp}&uuidb64={user.pk}&refresh_token={refresh_token}"
            
            # Prepare the email content
            subject = "New order is Placed"
            context = {
                'link': link,
                'username': user.username
            }
            
            # Render the HTML email content
        
            html_message = render_to_string("password_reset.html", context)
            
            # Send the email
            send_mail(
                subject=subject,
                message="",  # Plain text version (can be left empty if using HTML)
                from_email=EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=True,
                html_message=html_message
            )
            
            user.save()
            print("link ======", link)
            return user


class PasswordChangeAPIView(generics.UpdateAPIView):  # Changed to UpdateAPIView
    queryset = User.objects.all()
    serializer_class = api_serializer.ChangePasswordSerializer
    #lookup_field = 'email'  # Use email to find the user

    def update(self, request, *args, **kwargs):

        email = request.data.get('email')
        new_password = request.data.get('new_password')
        password = request.data.get('password')

        
        user = User.objects.get(email = email)
        if check_password(password, user.password): # compares the new_password with the hashed password filed.
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password changed successfully", "icon": "success"})
        else:
                return Response({"message": "Current password is incorrect", "icon": "error"}, status=400)
      

    