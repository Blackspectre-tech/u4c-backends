from rest_framework import serializers
from .models import (
    Project, Category, Milestone, 
    MilestoneImage, Expense, Update,
    Comment,Donation,
    )
from accounts.utils import resize_image
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from drf_spectacular.utils import extend_schema_field



class MilestoneImagesSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000,allow_empty_file=False),
        required=True, write_only=True,allow_empty=False,max_length=6,)
        
    class Meta:
        model = MilestoneImage
        fields = ['id','image', 'images']
        extra_kwargs = {
            'image': {'read_only': True},
            'id': {'read_only': True},
        }

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        milestone = self.context.get('milestone')
        instances = []

        if images:
            for img in images:
                image = resize_image(img)
                instances.append(MilestoneImage(
                    milestone=milestone,
                    image=image,
                ))
            
            MilestoneImage.objects.bulk_create(instances)

        return instances
    




class ExpensesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Expense
        fields = ['amount_spent','description','date','proof_pdf',]
        extra_kwargs = {
        'proof_pdf_url': {'read_only': True},
        }  

    def validate_pdf(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        if value.size > 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 1MB.")
        return value




class MilestoneSerializer(serializers.ModelSerializer):
    images = MilestoneImagesSerializer(read_only=True, many=True)
    expenses = ExpensesSerializer(read_only=True, many=True)
    percentage = serializers.IntegerField()
    goal = serializers.CharField(required=False)
    milestone_no = serializers.IntegerField(required=False)

    class Meta:
        model = Milestone
        fields = ['id','milestone_no','percentage','title','details','goal','images','expenses',]
        extra_kwargs = {
        'id': {'read_only': True},
        #'goal': {'read_only': True},
        }
    
    



class PostUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Update
        fields = ['title', 'details','image','created_at']
        extra_kwargs = {
            'created_at': {'read_only': True},
        }

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        validated_data['image'] = resize_image(image)

        return Update.objects.create(**validated_data) 




class CommentSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField()

    class Meta:
        model = Comment
        fields = ['id','username','details','created_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
        }
    



class DonationSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField()
    class Meta:
        model = Donation
        fields = [ 'username', 'amount']

    # @extend_schema_field(serializers.CharField)
    # def get_username(self,obj):
    #     return obj.username



class ProjectSerializer(serializers.ModelSerializer):

    categories = serializers.ListField(
        child = serializers.CharField(min_length=5),
        min_length=1, required=True,write_only=True
    )
    categories_display = serializers.SerializerMethodField(read_only=True)
    milestones = MilestoneSerializer(many=True, required=True)

    progress = serializers.SerializerMethodField(read_only=True)
    donations = DonationSerializer(read_only=True)
    duration_in_days = serializers.IntegerField(min_value=14, max_value=365)
    class Meta:
        model = Project
        fields = [
            'id','title','categories_display', 'goal', 'country', 'address', 'longitude', 'latitude',
            'description', 'categories', 'image', 'summary', 'duration_in_days', 
            #'problem_to_address','solution', 
            'video', 'milestones','donations','progress',
            ]
        extra_kwargs = {
            'id': {'read_only': True},
            'title': {'required': True},
            'goal':{'required': True},
            'country': {'required': True},
            'description':{'required': True},
            'address': {'required': True},
            'longitude':{'required': True},
            'latitude':{'required': True},
            #'problem_to_address':{'required': True},
            #'solution':{'required': True},
            'summary':{'required': True},
            'video': {'required': False},
            'image': {'required': True},
            'duration_in_days': {'required': True},
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

        # Validate milestone
        milestones = attrs.get('milestones') 
        if len(milestones) > 3:
            raise serializers.ValidationError('You can only have a maximum of 3 milestones.')
                 
        p_goal =  attrs.get('goal')
        milestones = attrs.get('milestones')
        count = 0
        previous_percentage = 0

        for item in milestones:
            current_percentage = item['percentage']
            
            # 1. Monotonicity check
            if current_percentage <= previous_percentage:
                raise serializers.ValidationError({
                    'milestones.percentage': "Milestone percentages must be in increasing order."
                    })
            count +=1
            item['goal'] = (p_goal/100) * Decimal(current_percentage)
            item['milestone_no'] = count
            previous_percentage = current_percentage
    
        
        if milestones[-1]['percentage'] != 100:
            raise serializers.ValidationError({
                'milestones.percentage': "The final milestone must be set to 100%."
            })
        
        attrs['milestones'] = milestones

        return attrs
    
    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_categories_display(self, obj):
        return [cat.name for cat in obj.categories.all()]
    
    # @extend_schema_field(serializers.CharField)
    # def get_progress(self,obj):
    #     return obj.progress

    def create(self, validated_data,**kwargs):
        categories_data = validated_data.pop('categories', None)
        milestones_data = validated_data.pop('milestones', None)
        image = validated_data.pop('image', None)

        with transaction.atomic():
            project = Project.objects.create(**validated_data)
            project.categories.set(categories_data)

            # Validate milestone goal total
            # p_goal = project.goal
            
            # count = 0
            # previous_percentage = 0

            # for item in milestones_data:
            #     current_percentage = item['percentage']
                
            #     # 1. Monotonicity check
            #     if current_percentage <= previous_percentage:
            #         raise serializers.ValidationError({
            #             'milestones.percentage': "Milestone percentages must be in increasing order."
            #          })
            #     count +=1
            #     item['goal'] = (p_goal/100) * Decimal(current_percentage)
            #     item['milestone_no'] = count
            #     previous_percentage = current_percentage
        
            
            # if milestones_data[-1]['percentage'] != 100:
            #     raise serializers.ValidationError({
            #         'milestones.percentage': "The final milestone must be set to 100%."
            #     })
            
            
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
                    image = resize_image(image)
                    project.image = image
                except ValidationError as e:
                    raise serializers.ValidationError({'image': e.message})

            project.save()
        
        return project
    
    def update(self, instance, validated_data):
        new_image = validated_data.get('image')
        if new_image:
            try:
                image = resize_image(image)
                instance.image = image
            except ValidationError as e:
                raise serializers.ValidationError({'image': e.message})

        return super().update(instance, validated_data)
    

class ProjectListSerializer(serializers.ModelSerializer):
    organization = serializers.StringRelatedField(read_only=True)
    progress = serializers.ReadOnlyField()
    class Meta:
        model = Project
        fields = ['id','title','image','goal','progress','description','summary','status','organization',]