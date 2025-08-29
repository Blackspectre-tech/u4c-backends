from django.contrib.auth.models import BaseUserManager,AbstractUser
from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinLengthValidator,MaxLengthValidator

# Create your models here.




class TimeStamps(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username=None
    first_name = None
    last_name = None
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(unique=True)
    avatar = models.ImageField(upload_to='avatars/',blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    otp = models.CharField(max_length=6,null=True,blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    is_organization = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    wallet_address = models.CharField(max_length=255, unique=True,null=True, blank=True)


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


    
    

class Profile(models.Model):
    username = models.CharField(max_length=25, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    anonymous = models.BooleanField(default=False)
    
    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        self.username = self.username.lower()
        self.first_name = self.first_name.title()
        self.last_name = self.last_name.title()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username}"

class Organization(models.Model):


    PENDING ='PENDING'
    APPROVED='✅APPROVED'
    DISAPPROVED ='❌DISAPPROVED'
    
    approval = [
    (PENDING,'PENDING'),
    (APPROVED,'✅APPROVED'),
    (DISAPPROVED,'❌DISAPPROVED')]


    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organization')
    website = models.URLField(null=True, blank=True)
    country = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    description=models.TextField()
    cac_document = models.FileField(null=True,blank=True)
    reg_no = models.CharField(max_length=8, blank = True,null=True)
    approval_status = models.CharField(max_length=20, choices=approval, default=PENDING)
    approverd_at = models.DateTimeField(null=True,blank=True)
    disapproverd_at = models.DateTimeField(null=True,blank=True)
    approved_by = models.CharField(max_length=30, null=True)
    disapproved_by = models.CharField(max_length=30, null=True)
    disapproval_reason= models.TextField(null=True)
    

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        self.country = self.country.title()

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.name}"
    

class Social(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='socials')
    instagram = models.URLField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    youtube = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True)


    def __str__(self):
        return f"{self.organization.name}"