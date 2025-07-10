from rest_framework import serializers
from .models import (
    Project, Category, Milestone, 
    MilestoneImage, Expense, Update,
    Comment,Donation,
    )
from accounts.utils import resize_and_upload, upload_pdf
from core.settings import IMG
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from cloudinary.uploader import destroy



class MiliestoneImagesSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000,allow_empty_file=False),
        required=True, write_only=True,allow_empty=False,max_length=6,)
        
    class Meta:
        model = MilestoneImage
        fields = ['id','image_url', 'images']
        extra_kwargs = {
            'image_url': {'read_only': True},
            'id': {'read_only': True},
        }

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        milestone = self.context.get('milestone')
        instances = []

        if images:
            for img in images:
                image_url, image_id = resize_and_upload(img, f"{IMG['milestones']}{milestone.title}")
                instances.append(MilestoneImage(
                    milestone=milestone,
                    image_url=image_url,
                    img_public_id = image_id
                ))
            
            MilestoneImage.objects.bulk_create(instances)

        return instances
    




class ExpensesSerializer(serializers.ModelSerializer):
    pdf = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = Expense
        fields = ['amount_spent','description','date','proof_pdf_url','pdf',]
        extra_kwargs = {
        'proof_pdf_url': {'read_only': True},
        }  

    def validate_pdf(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        if value.size > 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 1MB.")
        return value

    def create(self, validated_data, **kwargs):
        pdf = validated_data.pop('pdf',None)
        if pdf:
            pdf_url, public_id = upload_pdf(pdf)

        return Expense.objects.create(pdf_public_id=public_id,proof_pdf_url=pdf_url,**validated_data)




class MilestoneSerializer(serializers.ModelSerializer):
    images = MiliestoneImagesSerializer(read_only=True, many=True)
    expenses = ExpensesSerializer(read_only=True, many=True)

    class Meta:
        model = Milestone
        fields = ['id','milestone_no','title','details','goal','images','expenses']
        extra_kwargs = {
        'id': {'read_only': True},
        }
    
    def update(self, instance, validated_data):
        image_id = instance.id
        destroy(image_id)
        return super().update(instance, validated_data)
    

    




class PostUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)
    
    class Meta:
        model = Update
        fields = ['title', 'details','image','image_url','created_at']
        extra_kwargs = {
            'image_url': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        image_url, image_id = resize_and_upload(image, IMG['updates'])

        return Update.objects.create(image_url=image_url,img_public_id=image_id,**validated_data) 




class CommentSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField()

    class Meta:
        model = Comment
        fields = ['id','username','details','created_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
        }
    





class ProjectSerializer(serializers.ModelSerializer):
    
    categories = serializers.ListField(
        child = serializers.CharField(min_length=5),
        min_length=1, required=True,write_only=True
    )
    categories_display = serializers.SerializerMethodField(read_only=True)
    milestones = MilestoneSerializer(many=True, required=False)

    image = serializers.ImageField(write_only=True, required=True)

    class Meta:
        model = Project
        fields = [
            'id','title','categories_display', 'goal', 'country', 'location', 'longitude', 'latitude',
            'description', 'categories', 'image', 'problem_to_address',
            'solution', 'summary', 'video', 'milestones', 'image_url',
            ]
        extra_kwargs = {
            'id': {'read_only': True},
            'title': {'required': True},
            'goal':{'required': True},
            'country': {'required': True},
            'description':{'required': True},
            'location': {'required': True},
            'longitude':{'required': True},
            'latitude':{'required': True},
            'problem_to_address':{'required': True},
            'solution':{'required': True},
            'summary':{'required': True},
            'video': {'required': False},
            'image_url': {'required': False},
        }

    def validate(self, attrs):
        incoming_category_names = attrs.get('categories')
        
        # Ensure consistent casing for comparison with database
        processed_category_names = [name.title() for name in incoming_category_names]
        
        # Retrieve actual Category objects based on the processed names
        # Use a list() to force evaluation of queryset
        found_category_objects = list(Category.objects.filter(name__in=processed_category_names))
        
        # Get names of found objects
        found_names_set = {cat.name for cat in found_category_objects}
        
        # Determine missing names
        desired_names_set = set(processed_category_names)
        missing_names = desired_names_set - found_names_set

        if missing_names:
            raise serializers.ValidationError(f"The following categories do not exist: {missing_names}")
        
        # If all categories exist, store the actual Category objects in attrs
        # We replace the list of names with the list of objects for `create`
        attrs['categories'] = found_category_objects 
        
        return attrs

    def get_categories_display(self, obj):
        return [cat.name for cat in obj.categories.all()]



    def create(self, validated_data,**kwargs):
        categories_data = validated_data.pop('categories', None)
        milestones_data = validated_data.pop('milestones', None)
        image = validated_data.pop('image', None)

        with transaction.atomic():
            project = Project.objects.create(**validated_data)
            project.categories.set(categories_data)

            # Validate milestone goal total
            p_goal = project.goal
            total_goal = sum(Decimal(item['goal']) for item in milestones_data)
            if total_goal != p_goal:
                raise serializers.ValidationError({
                    'milestones.goal': 'The sum of all milestone goals must equal the project goal.'
                })

            try:
                milestone_instances = [
                    Milestone(project=project, **data)
                    for data in milestones_data
                ]
                Milestone.objects.bulk_create(milestone_instances)
            except Exception as e:
                raise serializers.ValidationError({
                    "milestones": f"Invalid milestone data: {str(e)}"
                })

            # Handle image upload
            if image:
                try:
                    image_url, image_id = resize_and_upload(image, f"{IMG['projects']}{validated_data.get('title')}")
                    project.image_url = image_url
                    project.img_public_id = image_id
                except ValidationError as e:
                    raise serializers.ValidationError({'image': e.message})

            project.save()
        
        return project