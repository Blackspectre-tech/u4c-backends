from django.db import models
from accounts.models import Organization, Profile,TimeStamps
from tinymce.models import HTMLField
from accounts.utils import html_cleaner
from django.utils.html import format_html
from django.core.validators import MinLengthValidator,MaxLengthValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from drf_spectacular.utils import extend_schema_field
from accounts.models import Wallet

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
    
    class Meta:
        verbose_name_plural = "Categories"


class Project(TimeStamps, models.Model):

    PENDING ='PENDING'
    APPROVED='APPROVED'
    DISAPPROVED ='DISAPPROVED'

    Funding ='Funding'
    Unimplemented ='Under Implementation'
    Cancelled ='Cancelled'
    Completed = 'Completed'
    Failed = 'Failed'

    approval = [
    (PENDING,'PENDING'),
    (APPROVED,'APPROVED'),
    (DISAPPROVED,'DISAPPROVED')]

    status = [
    (Funding,'Funding'),
    (Unimplemented,'Under Implementation'),
    (Cancelled,'Cancelled'),
    (Completed,'Completed'),
    (Failed,'Failed'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255, blank=False)
    goal=models.DecimalField(decimal_places=2,max_digits=14, blank=False)
    country = models.CharField(max_length=30, blank=False)
    address = models.CharField(max_length=150, blank=False)
    categories = models.ManyToManyField(Category, related_name='projects', blank=False)
    image = models.ImageField(upload_to='projects/',blank=False, null=False)
    description = HTMLField(blank=False, null=True)
    summary = HTMLField(blank=False, null=True)
    approval_status = models.CharField(max_length=20, choices=approval, default=PENDING)
    approverd_at = models.DateTimeField(null=True,blank=True)
    admin_action_at = models.DateTimeField(null=True,blank=True)
    admin_action_by = models.CharField(max_length=30, null=True)
    reason= models.TextField(null=True)
    status = models.CharField(max_length=20, choices=status, default=Funding)
    ended_at = models.DateTimeField(null=True)
    total_funds = models.DecimalField(decimal_places=2,max_digits=14,default=0)
    duration_in_days = models.DecimalField(null=True, blank=True,decimal_places=2,max_digits=5)
    wallet_address = models.CharField(max_length=255,null=True, blank=True)
    contract_id = models.IntegerField(null=True, blank=True)
    progress = models.DecimalField(decimal_places=2,max_digits=5,default=0.00)
    deployed = models.BooleanField(default=False)
    deadline = models.DateTimeField(null=True, blank=True)
    
#before deploying check if the user has an active fiat/crypto account 
    #payout = models.CharField(max_length=20, choices=payout_options, default=CRYPTO)
    
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-progress']
        verbose_name = "Campaign"

    @property
    @extend_schema_field(str)
    def progress_percenage(self):
        return f'{self.progress}%'
        # return f'{(self.total_funds / self.goal) * 100 :.2f}%'
    

    @property
    @extend_schema_field(int)
    def organization_id(self):
        return self.organization.id


    def save(self, *args, **kwargs):
        html_fields = ['description', 'summary']
        for field in html_fields:
            value = getattr(self, field)
            if value:
                sanitized = html_cleaner.clean(
                    value
                )
                setattr(self, field, sanitized)
        super().save(*args, **kwargs)


    def image_preview(self):
        if self.image:
            return format_html('<img src="{}" style="max-height: 200px;" />', self.image)
        return "No Image"

    image_preview.short_description = "Image Preview"



class Milestone(TimeStamps, models.Model):

    ACTIVE = 'Active'
    NOT_STARTED ='Not Started'
    COMPLETED = 'Completed'
    
    status = [
    (ACTIVE,'Active'),
    (NOT_STARTED,'Not Started'),
    (COMPLETED,'Completed')
    ]
    
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    milestone_no = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)],)
    title = models.CharField(max_length=250)
    details = HTMLField(blank=False, null=True)
    percentage = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    goal=models.DecimalField(decimal_places=2,max_digits=16)
    status = models.CharField(max_length=25, choices=status, default=NOT_STARTED)
    contract_index = models.IntegerField(null=True, blank=True)
    approved = models.BooleanField(default=False)
    withdrawn = models.BooleanField(default=False)
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
    
    @property
    def contract_id(self):
        return self.project.contract_id


def milestone_image_path(instance, filename):
    milestone =instance.milestone
    return f'milestone images/{milestone.project.title}/{milestone.milestone_no}'


class MilestoneImage(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name= 'images')
    image = models.ImageField(upload_to=milestone_image_path,blank=False, null=False)
    

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
    proof_pdf = models.FileField(upload_to='expenses/',blank=False, null=False) 


    def __str__(self):
        return self.milestone.title



class Update(models.Model):
    Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=255)
    details = models.TextField()
    image = models.ImageField(upload_to='updates/',blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
   

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
    


class Donation(models.Model):

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='donations')
    #donor = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(decimal_places=2,max_digits=14, blank=False)
    wallet = models.ForeignKey(Wallet,related_name='donations', blank=True, null=True, on_delete=models.CASCADE)
    refundable = models.BooleanField(default=False)
    refunded = models.BooleanField(default=False)

    
    class Meta:
        ordering = ["-amount"]

    def __str__(self):
        return f"{self.wallet} | amount: {self.amount} | project{self.project.title}"
    
    @property
    @extend_schema_field(str)
    def username(self):
        if not self.wallet:
            return "No Wallet"
        user = self.wallet.users.filter(is_organization=False).first()
        if not user or not hasattr(user, "profile"):
            return "Anonymous"
        # if user.is_organization:
        #     return "Anonymous"
        return user.profile.username or "Anonymous"

    @property
    @extend_schema_field(str)
    def wallet_address(self):
        if not self.wallet:
            return None
        return self.wallet.address



class Comment(TimeStamps,models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='comments')
    details = models.TextField()

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.profile.username
    
    @property
    @extend_schema_field(str)
    def username(self):
        return self.profile.username