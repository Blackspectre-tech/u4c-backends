from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Organization, UserProfile
from tinymce.models import HTMLField
from accounts.utils import html_cleaner
from accounts.models import TimeStamps
from django.utils.html import format_html
from accounts.utils import resize_and_upload
from core.settings import IMG
from django.core.validators import MinLengthValidator,MaxLengthValidator

# Create your models here.


class TimeStamps(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True




class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Project(TimeStamps, models.Model):

    PENDING ='PENDING'
    APPROVED='✅APPROVED'
    DISAPPROVED ='❌DISAPPROVED'
    FLAGGED='FLAGGED'
    Funding ='Funding'
    Unimplemented ='Under Implementation'
    Cancelled ='Cancelled'
    Completed = 'Completed'


    approval = [
    (FLAGGED,'🚩FLAGGED'),
    (PENDING,'PENDING'),
    (APPROVED,'✅APPROVED'),
    (DISAPPROVED,'❌DISAPPROVED')]

    status = [
    (Funding,'Funding'),
    (Unimplemented,'Under Implementation'),
    (Cancelled,'Cancelled'),
    (Completed,'Completed'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255, blank=False)
    goal=models.DecimalField(decimal_places=2,max_digits=14, blank=False)
    country = models.CharField(max_length=30, blank=False)
    longitude = models.DecimalField(max_digits=65, decimal_places=6, null=True, blank=False)
    latitude = models.DecimalField(max_digits=65, decimal_places=6, null=True, blank=False)
    location = models.CharField(max_length=150, blank=False)
    categories = models.ManyToManyField(Category, related_name='projects', blank=False)
    image_url = models.URLField(blank=False)
    description = HTMLField(blank=False, null=True)
    problem_to_address = HTMLField(blank=False, null=True)
    solution = HTMLField(blank=False, null=True)
    summary = HTMLField(blank=False, null=True)
    video = models.URLField(null=True, blank=True)
    approval_status = models.CharField(max_length=20, choices=approval, default=PENDING)
    approverd_at = models.DateTimeField(null=True,blank=True)
    admin_action_at = models.DateTimeField(null=True,blank=True)
    admin_action_by = models.CharField(max_length=30, null=True)
    reason= models.TextField(null=True)
    status = models.CharField(max_length=20, choices=status, default=Funding)
    ended_at = models.DateTimeField(null=True)
    total_funds = models.DecimalField(decimal_places=2,max_digits=14,default=0)
    
    


    def __str__(self):
        return self.title

    @property
    def progress(self):
        return f'{(self.total_funds / self.goal) * 100 :.2f}%'

    def save(self, *args, **kwargs):
        # self.image = resize_and_upload(self.image, IMG['projects'] + self.title)
        html_fields = ['description', 'summary', 'problem_to_address', 'solution']
        for field in html_fields:
            value = getattr(self, field)
            if value:
                sanitized = html_cleaner.clean(
                    value
                )
                setattr(self, field, sanitized)
        super().save(*args, **kwargs)



    def image_preview(self):
        if self.image_url:
            return format_html('<img src="{}" style="max-height: 200px;" />', self.image_url)
        return "No Image"

    image_preview.short_description = "Image Preview"



class Milestone(TimeStamps, models.Model):

    Awaiting_Report ='Waiting for Report'
    Not_Started ='Not Started'
    Implemented ='Implemented'
    
    status = [
    (Awaiting_Report,'Waiting for Report'),
    (Not_Started,'Not Started'),
    (Implemented,'Implemented')
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    milestone_no = models.IntegerField(default=1,)
    title = models.CharField(max_length=250)
    details = HTMLField(blank=False, null=True)
    goal=models.DecimalField(decimal_places=2,max_digits=16)
    status = models.CharField(max_length=25, choices=status, default=Not_Started)
    funds=models.DecimalField(decimal_places=2,max_digits=14,default=0)


    def save(self, *args, **kwargs):
        self.details = html_cleaner.clean(
            self.details
        )
        super().save(*args, **kwargs)


    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ["-updated_at"]
    

    @property
    def progress(self):
        return f'{(self.funds / self.goal) * 100:.2f}%'
    


class Milestone_Images(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name= 'images')
    image = models.URLField()
    

    def __str__(self):
        return self.image
    

    def image_preview(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 200px;" />', self.image)
        return "No Image"

    image_preview.short_description = "Image Preview"




class Expense(models.Model):
    amount_spent = models.DecimalField(decimal_places=2,max_digits=14)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name= 'expenses')
    description = models.TextField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    proof_pdf_url = models.URLField() 

    def __str__(self):
        return self.milestone.title



class Update(models.Model):
    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=255)
    details = models.TextField()
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
   


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
    


class Donations(models.Model):
    pass

class Comment(models.Model):
    pass



