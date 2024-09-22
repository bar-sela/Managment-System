from decimal import Decimal
from django.contrib.auth.password_validation import validate_password
from django.forms import ValidationError
from rest_framework.response import Response
from api import models as api_models

from rest_framework import serializers , status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import transaction
from userauths.models import Profile, User
from api.utils import generate_random_otp


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining a pair of access and refresh tokens.
    Extends the token payload with additional user information.
    """

    @classmethod
    def get_token(cls, user):
        """
        Override the default token generation method.
        Adds custom fields to the JWT token payload.

        Args:
            user (User): The authenticated user

        Returns:
            Token: The JWT token with custom payload
        """
        token = super().get_token(user)
        #print(token)

        # Add custom claims
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username

        return token
      
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password]) # cheaks password not to short or too common ect
    password2 = serializers.CharField(write_only=True, required=True) # NOT included in the model - > override create function 

    class Meta:
        model = User
        fields = ['full_name', 'email', 'username',  'password', 'password2']
 
    def validate(self, attr): # called automatically during the is_valid
        if attr['password'] != attr['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attr  # returns the validate data 
    
    def create(self, validated_data):   # is_valid returns a dictionary with all keys of all the bad inputs and the correspond messages for each one 
        try:
            with transaction.atomic():
                # Create a new user instance
                user = User(
                    otp = generate_random_otp(),
                    full_name=validated_data['full_name'],
                    email=validated_data['email'],
                    username=validated_data['username']
                )
                user.set_password(validated_data['password'])
                user.save()

            return user
        
        except Exception as e:
            # Handle any unexpected exceptions
            raise ValidationError({"detail": f"An unexpected error occurred: {str(e)}"})
  
        
    

class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirmed_password = serializers.CharField(write_only=True, required=True) # insures password is enough hard

    class Meta:
        model = User
        fields = ['password', 'confirmed_password']

    def validate(self, attrs):
        if attrs['password'] == attrs['confirmed_password']:
            raise serializers.ValidationError({"new_password": "New password must be different from the old password."})
        return attrs


    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"
        
        
################################################################# business logic ###############################################

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        fields = ['title', 'image', 'slug', 'course_count']
        model = api_models.Category


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.OrderItems
            
class TeacherSerializer(serializers.ModelSerializer):
    students = OrderItemSerializer(many = True)
    courses = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()

    class Meta:
        fields = [ "user", "image", "full_name", "bio", "facebook", "twitter", "linkedin", "about", "country", "students", "courses", "review",]
        model = api_models.Teacher


class VariantItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = '__all__'
        model = api_models.VariantItem

class VariantSerializer(serializers.ModelSerializer):
    variant_items = VariantItemSerializer(many=True)
    items = VariantItemSerializer(many=True)
    
    class Meta:
        fields = ['course', 'title', 'date', 'variant_items', 'items']
        model = api_models.Variant

class ReviewSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False)

    class Meta:
        fields = '__all__'
        model = api_models.Review

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Notification
        
class CouponSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset = User.objects.all()  , write_only=True)
    teacher = serializers.PrimaryKeyRelatedField(queryset=api_models.Country.objects.all() , write_only=True)
    
    class Meta:
        fields = '__all__'
        model = api_models.Coupon

class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Country
        
class WishlistSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Wishlist

class CompletedLessonSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.CompletedLesson
        
class NoteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Note

class CartDetailsSerializer(serializers.ModelSerializer):
     user = serializers.PrimaryKeyRelatedField(queryset=api_models.User.objects.all(),write_only=True)
     country = serializers.PrimaryKeyRelatedField(queryset=api_models.Country.objects.all() , write_only=True)
     
     class Meta:
        fields = ['user' , 'created_at' , 'country' , 'calculate_sum', 'discount' , 'applied_coupon']
        model = api_models.CartDetails
     


class CartElementsSerializer(serializers.ModelSerializer):
    
    cart_details = CartDetailsSerializer(read_only=True ,  source='cart')
    course = serializers.PrimaryKeyRelatedField (queryset=api_models.Course.objects.all(), write_only=True)


    class Meta:
        fields = ['cart' , 'course' , 'quantity' , 'cart_details']
        model = api_models.CartElements            
    
# order details 
class OrderDetailsSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=api_models.User.objects.all(),write_only=True) # converts the int primary key to actual instance  
    country = serializers.PrimaryKeyRelatedField(queryset=api_models.Country.objects.all() , write_only=True)
    
    class Meta:
        fields = ['student', 'total','tax', 'payment_status', 'country', 'date' ,'applied_coupon']
        model = api_models.OrdersDetails       
    
    #the user validate data already has the User type and not the inside the student key 
    
    
# oder items 
class OrderItemsSerializer(serializers.ModelSerializer):
       
    class Meta:
        fields = ['order' , 'course' , 'quantity' , 'created_at']       
        model = api_models.OrderItems

    
class Question_Answer_MessageSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False)

    class Meta:
        fields = '__all__'
        model = api_models.Question_Answer_Message

class CertificateSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = api_models.Certificate


class Question_AnswerSerializer(serializers.ModelSerializer):
    messages = Question_Answer_MessageSerializer(many=True)
    profile = ProfileSerializer(many=False)
    
    class Meta:
        fields = ['course','user','title', 'date','messages','profile']
        model = api_models.Question_Answer
        
class EnrolledCourseSerializer(serializers.ModelSerializer):
    lectures = VariantItemSerializer(many=True, read_only=True)
    completed_lesson = CompletedLessonSerializer(many=True, read_only=True)
    curriculum =  VariantSerializer(many=True, read_only=True)
    note = NoteSerializer(many=True, read_only=True)
    question_answer = Question_AnswerSerializer(many=True, read_only=True)
    review = ReviewSerializer(many=False, read_only=True)


    class Meta:
        fields = ['lectures','completed_lesson','curriculum','note','question_answer','review','course','user','order_item','date']
        model = api_models.EnrolledCourse
        
class CourseSerializer(serializers.ModelSerializer):
    students = EnrolledCourseSerializer(many=True, required=False, read_only=True,)
    curriculum = VariantSerializer(many=True, required=False, read_only=True,)
    lectures = VariantItemSerializer(many=True, required=False, read_only=True,)
    reviews = ReviewSerializer(many=True,  required=False,read_only=True)
    class Meta:
        fields = ["category", "teacher", "file", "image", "title", "description", "price", "language", "level", "platform_status", "featured", "slug", "date", "students", "curriculum", "lectures", "average_rating", "rating_count", "reviews",]
        model = api_models.Course
        
        
