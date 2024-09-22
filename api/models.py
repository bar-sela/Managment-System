from django.db import models
from django.db import models
from django.forms import ValidationError
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator
from moviepy.editor import VideoFileClip
from datetime import timedelta
from userauths.models import Profile, User
from django_countries.fields import CountryField
from django.db.models import Sum
from django.db.models import F, Sum
# Create your models here.


   
    ########################   Validators #########################
    
def validate_non_negative_duration(value):
        if value and value < timedelta(0):
            raise ValidationError("Duration cannot be negative.")
        
        
    ######################################################
    
    
LANGUAGE = (
    ("English", "English"),   
    ("Spanish", "Spanish"),
    ("French", "French"),
)

LEVEL = (
    ("Beginner", "Beginner"),
    ("Intemediate", "Intemediate"),
    ("Advanced", "Advanced"),
)


TEACHER_STATUS = (
    ("Draft", "Draft"),
    ("Disabled", "Disabled"),
    ("Published", "Published"),
)

PAYMENT_STATUS = (
    ("Paid", "Paid"),
    ("Processing", "Processing"),
    ("Failed", "Failed"),
)


PLATFORM_STATUS = (
    ("Review", "Review"),
    ("Disabled", "Disabled"),
    ("Rejected", "Rejected"),
    ("Draft", "Draft"),
    ("Published", "Published"),
)

RATING = (
    (1, "1 Star"),  # data base store 1 , user see "1 star"
    (2, "2 Star"),
    (3, "3 Star"),
    (4, "4 Star"),
    (5, "5 Star"),
)

NOTI_TYPE = (
    ("New Order", "New Order"),
    ("New Review", "New Review"),
    ("New Course Question", "New Course Question"),
    ("Draft", "Draft"),
    ("Course Published", "Course Published"),
    ("Course Enrollment Completed", "Course Enrollment Completed"),
)




######## Teacher 


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to="course-file", blank=True, null=True, default="default.jpg") #relative to  media root | If no file is uploaded, "default.jpg" will be used. 
    full_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=100, null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True) # validates that the input is a properly formatted URL
    linkedin = models.URLField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self) :
        return self.full_name
    
    def students(self):
        return OrderItems.objects.filter(teacher = self) 
    
    def courses(self ):
           return self.course_set.all() # Efficient reverse relation
    
    def review(self):
        #return Course.objects.filter(teacher=self).count() # for repeting this for couple of teachers : Category.objects.annotate(num_courses=Count('course'))
        return self.courses().count()
    
class Category(models.Model): 
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="course-file", default="category.jpg", null=True, blank=True)
    active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, null=True, blank=True ,  db_index=True) # When creating a new article with the title "Django Basics", Django will automatically generate the slug "django-basics" for you

    class Meta:
        verbose_name_plural = "Category"
        ordering = ['title'] # apply .order_by('title') by defualt to each query model 

    def __str__(self):
        return self.title
    
    def course_count(self):
        return self.course_set.all().count()
    
    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title) 
        super().save(*args, **kwargs) #TODO make sure no identical slugs
        

class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True) # if category deleted this field turns to NULL
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)   # teacher gets delete - > course gets delete
    file = models.FileField(upload_to="course-file",default="course.jpg", blank=True, null=True) #TODO 
    image = models.FileField(upload_to="course-file",default="course_image.jpg", blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00 , validators=[MinValueValidator(0.0, message="Price must be greater than or equal to 0")])
    language = models.CharField(choices=LANGUAGE, default="English", max_length=100)
    level = models.CharField(choices=LEVEL, default="Beginner", max_length=100)
    platform_status = models.CharField(choices=PLATFORM_STATUS, default="Published", max_length=100)
    featured = models.BooleanField(default=False)
    #course_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    slug = models.SlugField(unique=True, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now) 
    discount = models.DecimalField(max_digits=12 , decimal_places= 2 , default= 0.00 , validators=[MinValueValidator(0.0, message="Discount must be greater than or equal to 0")])

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug == None:
            self.slug = slugify(self.title) + str(self.pk)
        super(Course, self).save(*args, **kwargs)

    def students(self):
        return EnrolledCourse.objects.filter(course=self)
    
    def curriculum(self):
        return Variant.objects.filter(course=self)
    
    def lectures(self):
        return VariantItem.objects.filter(variant__course=self)
    
    def average_rating(self):
        average_rating = Review.objects.filter(course=self, active=True).aggregate(avg_rating=models.Avg('rating'))
        return average_rating['avg_rating']
    
    def rating_count(self):
        return Review.objects.filter(course=self, active=True).count()
    
    def reviews(self):
        return Review.objects.filter(course=self, active=True) 


# SECTION 
 
class Variant(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000)
    #variant_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
    
    def variant_items(self):
        return VariantItem.objects.filter(variant=self)
    
    def items(self):
        return self.variant_items()
    

#appears to represent the information of a lesson or a specific piece of content within a course
class VariantItem(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="variant_items")
    title = models.CharField(max_length=1000)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to="course-file", null=True, blank=True)
    duration = models.DurationField(null=True, blank=True , validators=[validate_non_negative_duration] )
    content_duration = models.CharField(max_length=1000, null=True, blank=True)
    preview = models.BooleanField(default=False)  # is available for preview 
    #variant_item_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.variant.title} - {self.title}"
    
    
    def save(self, *args, **kwargs):
        if self.file:
            clip = VideoFileClip(self.file.path)
            duration_seconds = clip.duration
            minutes, seconds = divmod(duration_seconds, 60)
            self.content_duration = f"{int(minutes)}m {int(seconds)}s"
        super().save(*args, **kwargs)
                
class Question_Answer(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    #qa_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    class Meta:
        ordering = ['-date']  # Question_Answer.object.all() will include sorting SQL

    def messages(self):
        return Question_Answer_Message.objects.filter(question=self)
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
class Question_Answer_Message(models.Model):
    #course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question = models.ForeignKey(Question_Answer, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    #qam_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    #qa_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    class Meta:
        ordering = ['date']

    def profile(self):
        return Profile.objects.get(user=self.user)
    
    
#temporary collection of items that the user intends to purchase.


class Country(models.Model):
    name = CountryField(blank_label='(select country)', null=False, blank=False)
    tax_rate = models.IntegerField(default=5)
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name.name)
    
############### CART 
    
class CartDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    applied_coupon = models.BooleanField(default=False)
    saved = models.DecimalField(max_digits=12, default=0.00, decimal_places=2) # how much money was saved from the original total price.
    discount = models.DecimalField(max_digits=12, default=0.00, decimal_places=2) 
    stripe_session_id = models.CharField(max_length=1000, null=True, blank=True)
    
    def calculate_sum(self):
        return CartElements.objects.filter(cart=self).aggregate( total_sum=Sum(F('course__price') * F('quantity')))['total_sum'] or 0

    def __str__(self):
        return f'{self.pk} -  Cart of {self.user.username}'
    
    
class CartElements(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    cart = models.ForeignKey(CartDetails, on_delete=models.CASCADE )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('course', 'cart')
            
    def __str__(self):
        return f'{self.pk} - {self.cart} - {self.course}'

# Represents a completed order based on the items in the cart. It's a permanent record of the transaction.
class OrdersDetails(models.Model):
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    tax =  models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    payment_status = models.CharField(choices=PAYMENT_STATUS, default="Processing", max_length=100)
    country = CountryField(blank_label='(select country)', null=False, blank=False)
    date = models.DateTimeField(default=timezone.now)
    applied_coupon = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date']
    
    def order_items(self):
       return self.orderItems_set.all()
    
    def __str__(self):
        return f'{self.student} - {self.date}' 
   
    def clean(self):  # make sure to use if their is manual change to the instance 

        if self.total < 0:
            raise ValidationError({'total': 'Total cannot be negative.'})
        if self.tax < 0:
            raise ValidationError({'tax': 'Tax cannot be negative.'})

class OrderItems(models.Model):
    order = models.ForeignKey(OrdersDetails, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True) 
    
    class Meta:
        unique_together = ('course', 'order')
        ordering = ['-created_at']
    
    def order_id(self):
        return f"Order ID #{self.order.pk}"
    
    def payment_status(self):
        return f"{self.order.payment_status}"
    
    def __str__(self):
        return f'{self.pk} - {self.order.pk} - {self.course.__str__}' 

class Certificate(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #certificate_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    

class CompletedLesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    variant_item = models.ForeignKey(VariantItem, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
    
 # טבלת הרשמה של יוסרים והקורסים שלהם   
class EnrolledCourse(models.Model):   
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    #teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(OrderItems, on_delete=models.CASCADE)
    #enrollment_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)
    
    
    def __str__(self):
        return self.course.title
    
    def lectures(self):
        return VariantItem.objects.filter(variant__course=self.course)
    
    def completed_lesson(self):
        return CompletedLesson.objects.filter(course=self.course, user=self.user)
    
    def curriculum(self):
        return Variant.objects.filter(course=self.course)
    
    def note(self):
        return Note.objects.filter(course=self.course, user=self.user)
    
    def question_answer(self):
        return Question_Answer.objects.filter(course=self.course)
    
    def review(self):
        return Review.objects.filter(course=self.course, user=self.user).first()
    
class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000, null=True, blank=True)
    note = models.TextField()
    #note_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    date = models.DateTimeField(default=timezone.now)   

    def __str__(self):
        return self.title
  
#Rating   
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    reply = models.CharField(null=True, blank=True, max_length=1000)
    active = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)   

    def __str__(self):
        return self.course.title
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(OrdersDetails, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(OrderItems, on_delete=models.SET_NULL, null=True, blank=True)
    review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=100, choices=NOTI_TYPE)
    seen = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)  

    def __str__(self):
        return self.type


class Coupon(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    used_by = models.ManyToManyField(User, blank=True)
    code = models.CharField(max_length=50)
    discount = models.IntegerField(default=1)
    active = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)   

    def __str__(self):
        return self.code


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.course.title)
    
    