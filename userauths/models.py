from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.utils.text import slugify

#note : 
#. By default, Django automatically creates a primary key field named id 


class User(AbstractUser):   
    username = models.CharField(unique=True, max_length=100, blank=False, null=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    otp = models.CharField(max_length=100, null=True, blank=True) # can be empty(blank)
    refresh_token = models.CharField(max_length=100 , null=True , blank=True)   
    
    USERNAME_FIELD = 'email'  # unique identifier for authentication logging
    
    def save(self, *args, **kwargs):
        if self.full_name == "":
            self.full_name = self.username
        super().save(*args, **kwargs)
        Profile.objects.get_or_create(user=self)  # creating a new profile 
       

    #The REQUIRED_FIELDS attribute is a list of fields that are required when creating a user 
    #  By default, Django requires the username field. Since you’re using email as the unique identifier, you'll need to include username 
    # in REQUIRED_FIELDS so that it is still required when !creating a user!
    
    REQUIRED_FIELDS = ['username']  

    def __str__(self):
        return f'{self.pk} - {self.email}'
    
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to="user_folder", default="default-user.jpg", null=True, blank=True)
    
    #user_folder = This specifies the directory where the uploaded files will be stored
    #default="default-user.jpg": This sets a default file to be used if no file is uploaded by the user.
    #null=True: This allows the database to store NULL for this field, meaning it’s not required to have a file associated with the model instance
    #blank=True: This allows the field to be empty in forms, meaning it's optional when creating or editing the model instance through forms
   
    full_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True) # date_created will be automatically set to the current date and time when a new instance of MyModel is created. This field will not change on subsequent updates to the model instance.

    def save(self, *args, **kwargs):
        if self.full_name == "" or self.full_name == None:
            self.full_name = self.user.username
        super().save(*args, **kwargs)
    
    def __str__(self):
            return str(self.full_name)


#The post_save signal in Django is triggered after a model's save() method is called, and the instance is successfully saved to the database.
# This signal is often used to perform actions automatically after an object is created or updated, such as updating related models
# , sending notifications, or logging changes.

"""
def create_user_profile(sender, instance, created, **kwargs): # sender = User 
    if created:
        Profile.objects.create(user=instance)
        

post_save.connect(create_user_profile, sender=User) #signal should only be triggered for the User model only when creartion of USER
"""
#post_save.connect(save_user_profile, sender=User) #  hapends each time user instace saved(create and update)



