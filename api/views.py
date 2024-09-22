from decimal import Decimal
from venv import logger
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import requests
import stripe
from api import serializer as api_serializer
from rest_framework.response import Response  # Corrected import
from rest_framework import generics ,status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import CartDetails, CartElements, Category, Country, Coupon, Course, EnrolledCourse, Notification, OrderItems, OrdersDetails, Teacher
from userauths.models import User
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from backend.settings import EMAIL_HOST_USER
from django.contrib.auth.hashers import check_password
from cryptography.fernet import Fernet
from api.utils import generate_random_otp
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from django.db.models import Sum, F

# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY



class MyTokenObtainPairView(TokenObtainPairView): # like viewSet
    serializer_class = api_serializer.MyTokenObtainPairSerializer  # this custom serializer will be used to process the request data.
    

class RegisterView(generics.CreateAPIView): #The CreateAPIView class in Django REST Framework (DRF) is specifically designed for handling HTTP POST requests to create new instances of a model. It does not handle GET requests by default.
    queryset = User.objects.all() 
    serializer_class = api_serializer.RegisterSerializer
    
    # called called during the is_save
 

class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView): # specifically designed to handle GET requests for retrieving a single object
    queryset = User.objects.all() 
    serializer_class = api_serializer.UserSerializer

    # super().get_object() cant be used since pk is automatic by django 
    def get_object(self ):  # the following:a. Calls self.get_object() to retrieve the object , b. Passes the retrieved object to the serializer ,c. Returns the serialized data in the response

        email = self.kwargs.get('email')  # {'email': 'nbarsela@gmail.com'}
    
        user = User.objects.filter(email=email).first()
    
        if user:
        
            # Create a new RefreshToken object for the user
            #print( user.refresh_token)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            user.refresh_token= str(refresh)
            
            # refresh otp :
            user.otp = generate_random_otp()
            
            
            
            #print(f"New Access Token: {access_token}")
            #print(f"New Refresh Token: {refresh}")
            
            user.otp = generate_random_otp()
            
            # Generate the link
            link = f"http://localhost:5173/create-new-password/?otp={user.otp}&uuidb64={user.pk}&refresh_token={refresh}"
            
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
            #print("link ======", link)
            return user


class PasswordChangeAPIView(generics.UpdateAPIView):  # Changed to UpdateAPIView
    queryset = User.objects.all()
    serializer_class = api_serializer.ChangePasswordSerializer
    #lookup_field = 'email'  # Use email to find the user

    def update(self, request, *args, **kwargs):
        print(request)
        
        otp = request.data.get('otp')
        uuidb64 = request.data.get('uuidb64')
        new_password = request.data.get('new_password')

        
        print(otp ) 
        print(uuidb64 )
        
        user = User.objects.get(otp = otp, id = uuidb64 )
        print(user.email)
        if user: # compares the new_password with the hashed password filed.
                user.set_password(new_password)
                user.save()
                return Response(data={"message": "Password changed successfully", "icon": "success"}, status=200)
        else:
                return Response(data={"message": "Current password is incorrect", "icon": "error"}, status=400)
      
      
      
####################### business logic view ########################



class CategoryListAPIview(generics.ListAPIView): # handles only GET requests and returns an array (list) of serialized objects
    queryset = Category.objects.filter(active = True)
    serializer_class= api_serializer.CategorySerializer
    
class CourseListAPIview(generics.ListAPIView):
    queryset = Course.objects.filter(platform_status = 'Published')
    serializer_class = api_serializer.CourseSerializer
    
class CourseDetailAPIview(generics.RetrieveAPIView):
    queryset = Course.objects.filter(platform_status = 'Published')
    serializer_class = api_serializer.CourseSerializer
        
    def get_object(self):
        slug = self.kwargs.get('slug')
        course =  Course.objects.get(slug= slug ,platform_status = 'Published' )
        return course
    
class CartDetailsAPIview(generics.CreateAPIView):
        queryset = CartDetails.objects.all()
        serializer_class = api_serializer.CartDetailsSerializer
        
        def create(self, request):
                
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

              
                user = serializer.validated_data["user"]
                country= serializer.validated_data["country"]
      
                # retrieve the correct cart for user 
                
                cart = CartDetails.objects.filter(user = user).first()
                print(cart)
                if not cart:
                    return Response({"message": "Cart not found for user"}, status=status.HTTP_404_NOT_FOUND)
                  

                cart, created = CartDetails.objects.get_or_create( user=user,defaults={'country': country})
        
                  
                # course validation
                course_id = request.data.get("course")
                course = Course.objects.get(id=course_id)
               
                # create the cart element 
                cart_element = CartElements(
                    course = course,
                    cart = cart,
                    quantity=request.data.get("quantity", 1)  # Default to 1 if not specified
                )
                cart_element.save()
                return Response({"message": "created successfully"}, status=status.HTTP_201_CREATED)

        
        
class CartListAPIview(generics.ListAPIView): #  Serializes a queryset of multiple objects.
        queryset = CartElements.objects.all()
        serializer_class = api_serializer.CartElementsSerializer
        
        """  the search is by user_id instead of pk of the row """
        
        def get_queryset(self): # ,נותן לי את כל הקארטס ששייכים לאותו קארטאידי לפי איך שהוא עשה  או במקרה שלי לאותו יוסראידי
            user_id = self.kwargs.get("user_id")
            queryset = CartElements.objects.filter(cart_id__user_id=user_id) 
            print(type(queryset))
            return queryset

        """  overide to delete the row by user_id and item_id instead of pk | just finding the queryset nedeed and dont manualy delete """
class CartDeleteAPIview(generics.DestroyAPIView):  # deletes the returning row 
        queryset = CartElements.objects.all()  
        serializer_class = api_serializer.CartElementsSerializer           
        
        def get_object(self):
            user_id = self.kwargs.get("user_id")
            course_id = self.kwargs.get("item_id")
            
            if not user_id or not course_id:
                  raise NotFound("User ID or Course ID not provided")
    
            queryset = CartElements.objects.filter(cart__user=user_id, course=course_id).first()
            if queryset is None:
                 raise NotFound("Cart item not found")  # error inside get_object
            
            return queryset
            
           
class CartStatsAPIView(APIView):
    
    def get_users_cart_courses(self,user_id):
        return CartElements.objects.filter(cart__user = user_id)
    
    def get(self, request, *args, **kwargs):
        
        user_id = self.kwargs.get('user_id')
        if not user_id:
            return Response({"error": "user id did not provided."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_users_cart_courses(user_id)

        # Check if the cart exists
        if not queryset.exists():
            return Response({"error": "Cart ID does not exist."}, status=status.HTTP_404_NOT_FOUND)

        #print(queryset.aggregate(total_Sum = Sum('course__price')))
        price = queryset.aggregate(total_Sum = Sum('course__price'))['total_Sum'] or Decimal('0.00')
        
        cart_details = CartDetails.objects.filter(user = user_id).first()
        if not cart_details:
            return Response({"detail": "Cart details not found"}, status=status.HTTP_404_NOT_FOUND)

        tax = cart_details.country.tax_rate
        total = round(price + tax, 2)
        
        data = {
            "price": float(price),
            "tax": float(tax),
            "total": float(total),
        }

        return Response(data)
    
    
class CreateOrderApiView(generics.CreateAPIView):
    queryset = OrdersDetails.objects.all()
    serializer_class = api_serializer.OrderDetailsSerializer
    


class CreateOrderApiView(generics.CreateAPIView):
    queryset = OrdersDetails.objects.all()
    serializer_class = api_serializer.OrderDetailsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['student']
        country = serializer.validated_data['country']
        cart_elements = CartElements.objects.filter(cart__user=user)

        if not cart_elements:
            return Response({"message": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate the total sum in one go and validate order creation atomically
        try:
            with transaction.atomic():
                new_order = serializer.save()
                order_items = [
                    OrderItems(order=new_order, course=element.course, quantity=element.quantity)
                    for element in cart_elements
                ]
                OrderItems.objects.bulk_create(order_items) 
                
                total_sum = cart_elements.aggregate(total=Sum(F('course__price') * F('quantity')))['total']
                new_order.total = total_sum
                new_order.tax = country.tax_rate
                new_order.save()
        except ValidationError as e:
            return Response({"message": f"Error creating order: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Order created successfully"}, status=status.HTTP_201_CREATED)


class CouponApplyApiView(generics.UpdateAPIView):

    def update(self, request, *args, **kwargs):
        
        user_id = kwargs.get('user_id')
        teacher_id = kwargs.get('teacher_id')
        code = kwargs.get('code')

        user = User.objects.get(id = user_id )
        print(user)
        teacher = Teacher.objects.get(id = teacher_id)
        print(teacher)
                
        coupon = Coupon.objects.filter(teacher =teacher, code=code, active=True).first()
        if not coupon:
            return Response({"detail": "Invalid or inactive coupon."}, status=status.HTTP_400_BAD_REQUEST)

        
        cart_detail = CartDetails.objects.filter(user=user).first()
        print(cart_detail)
        if cart_detail:
            cart_detail.applied_coupon = True
            cart_detail.discount = coupon.discount
            cart_detail.save()
            return Response({"detail": "Coupon applied successfully."}, status=status.HTTP_200_OK)

        return Response({"detail": "Cart not found for the user."}, status=status.HTTP_404_NOT_FOUND)
    
    
"""
The goal is to provide the client with a secure payment page containing all the relevant transaction details.
This view integrates Stripe's payment processing by generating a ready-to-use Payment Page.
The Payment Page object in Stripe represents an ongoing transaction, including the products/services, accepted payment methods, customer billing information,
and URLs for success and cancellation pages.
"""
class StripeCheckoutAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CartDetailsSerializer


    def create(self, request, *args, **kwargs):
        print(self.kwargs)
        cart_id = self.kwargs['cart_id']
        cartD = CartDetails.objects.get(id=cart_id)

        if not cartD:
            return Response({"message": "Order Not Found"}, status=status.HTTP_404_NOT_FOUND)
        total =cartD.calculate_sum() * 100
   
        
        
        try:
            checkout_session = stripe.checkout.Session.create( # checkout session is the response #This step generates a unique session_id that represents the payment session on Stripe's servers.
                customer_email = cartD.user.email ,
                payment_method_types=['card'], #  pay using credit or debit cards.
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': cartD.user.full_name
                            },
                            'unit_amount': total 
                        },
                        'quantity': 1
                    }
                ],
                mode='payment',  # one time payment 
                success_url=settings.FRONTEND_SITE_URL + '/payment-success/' + str(cartD.id) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url= settings.FRONTEND_SITE_URL + '/payment-failed/'
            )
            print("checkout_session ====", checkout_session)
            print(checkout_session.id)
            cartD.stripe_session_id= checkout_session.id

            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            return Response({"message": f"Something went wrong when trying to make payment. Error: {str(e)}"})
        
"""provide your PayPal account's client_id and secret_key, and PayPal gives you an access
  token in return, which acts as a temporary key to access PayPal's services."""

def get_access_token(client_id, secret_key):
    token_url = "https://api.sandbox.paypal.com/v1/oauth2/token" #  URL where you send a request to get the access token
    data = {'grant_type': 'client_credentials'} #  telling PayPal that you want to use client credentials to get the token
    auth = (client_id, secret_key) 
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        print("Access TOken ====", response.json()['access_token'])
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to get access token from paypal {response.status_code}")
    

"""
    PaymentSuccessAPIView class handles two different payment methods: PayPal and Stripe. Depending on which method the user selects,
    the API verifies the payment status and processes the order accordingly.
"""

class PaymentSuccessAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.OrderDetailsSerializer
    queryset = OrdersDetails.objects.all()
  
    def create_notifications(order, order_items):
        """
        Create notifications for the student and teachers associated with the order items.
        """
        Notification.objects.create(user=order.student, order=order, type="Course Enrollment Completed")
        for item in order_items:
            Notification.objects.create(
                teacher=item.course.teacher,
                order=order,
                order_item=item,
                type="New Order"
            )

    def handle_paypal_payment(self , paypal_order_id, order, order_items): #  The ID of the PayPal order.
     
        paypal_api_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}"
        auth_token =  get_access_token(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET_ID)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {auth_token}" # get Token from paypal API Authentication
        }
        response = requests.get(paypal_api_url, headers=headers)

        if response.status_code != 200:
            return {"message": "PayPal Error Occurred", "status": response.status_code}

        paypal_order_data = response.json()
        if paypal_order_data.get('status') == "COMPLETED" and order.payment_status == "Processing":
            order.payment_status = "Paid"
            order.save()
            self.create_notifications(order, order_items)
            return {"message": "Payment Successful"}

        return {"message": "Already Paid" if order.payment_status == "Paid" else "Payment Failed"}

    def handle_stripe_payment(self, session_id, order, order_items):
        """
        retrieves details about a checkout session from the Stripe API based on the session_id you provide.
        The session_id refers to the unique identifier of the checkout session you created earlier, 
        and this call will return details like the payment status,
        customer information, products purchased, and more
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)  
        except stripe.error.InvalidRequestError:
            return {"message": "Invalid Stripe Session ID", "status": 400}

        if session.payment_status == "paid" and order.payment_status == "Processing":
            order.payment_status = "Paid"
            order.save()
            self.create_notifications(order, order_items)
            return {"message": "Payment Successful"}

        return {"message": "Already Paid" if order.payment_status == "Paid" else "Payment Failed"}

    def create(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        session_id = request.data.get('session_id')
        paypal_order_id = request.data.get('paypal_order_id')

        try:
            order = OrdersDetails.objects.get(id=order_id)
        except OrdersDetails.DoesNotExist:
            return Response({"message": "Order not found"}, status=404)
        
        order_items = OrderItems.objects.filter(order=order)

        # PayPal payment process
        if paypal_order_id :
            paypal_result = self.handle_paypal_payment(paypal_order_id, order, order_items)
            return Response(paypal_result, status=paypal_result.get("status", 200))

        # Stripe payment process
        if session_id :
            stripe_result = self.handle_stripe_payment(session_id, order, order_items)
            return Response(stripe_result, status=stripe_result.get("status", 200))

        return Response({"message": "Invalid Payment Method"})
    
   


class SearchCourseAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CourseSerializer

    def get_queryset(self):
        query = self.request.GET.get('query')
        # learn lms
        return Course.objects.filter(title__icontains=query, platform_status="Published")
    

