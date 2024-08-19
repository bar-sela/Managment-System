from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save

class User(AbstractUser):
    username = models.CharField(unique=True, max_length=100)
    email = models.EmailField ( unique=True)
    full_name = models.CharField(unique=True, max_length=100)
    otp = models.CharField(max_length=100, null=True, blank=True) # can be empty(blank)


    USERNAME_FIELD = 'email'  # unique identifier for authentication 

    #The REQUIRED_FIELDS attribute is a list of fields that are required when creating a user 
    #  By default, Django requires the username field. Since you’re using email as the unique identifier, you'll need to include username 
    # in REQUIRED_FIELDS so that it is still required when creating a user
    
    REQUIRED_FIELDS = ['username']  

    def __str__(self):
        return self.email
    
    """
    def save(self, *args, **kwargs):
        email_username, full_name = self.email.split("@")
        if self.full_name == "" or self.full_name == None:
            self.full_name == email_username
        if self.username == "" or self.username == None:
            self.username = email_username
        super(User, self).save(*args, **kwargs)
    """
    
  
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

    REQUIRED_FIELDS = [full_name]  
    
    def __str__(self):
            return str(self.full_name)
   