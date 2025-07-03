from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Project, Category, Milestone, 
    Milestone_Images, Expense, Update,
    )
from accounts.utils import resize_and_upload
from core.settings import IMG
from django.core.exceptions import ValidationError


class MiliestoneImagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Milestone_Images
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Milestone
        fields = ['milestone_no','title','details','goal']

class ExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'

class UpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)
    image_url = serializers.URLField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    class Meta:
        model = Update
        fields = ['title', 'details','image','image_url']

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        image_url = resize_and_upload(image, IMG['updates'])
        validated_data['image_url'] = image_url
        
        
        return 
    

# class MilestoneUpdateSerializer(serializers.ModelSerializer):
#     images = serializers.ListField(
#         child=serializers.ImageField(max_length=1000000,allow_empty_file=False),
#         required=False, write_only=True,allow_empty=True,  # Optional: Allows an empty list
#         max_length=8,     #Limits the number of items
#     )
#     class Meta:
#         model = Milestone
#         fields = ['images','title','details',]


#     def update(self, instance, validated_data):

#         images = validated_data.pop('images', None)
#         title = instance.title
#         if images:
#             for img in images:
#                 image_url = resize_and_upload(img,{IMG['milestones']}+{title})
#                 Milestone_Images.objects.create(milestone=instance, image=image_url)
#         return super().update(instance, validated_data)




class ProjectSerializer(serializers.ModelSerializer):
    
    categories = serializers.ListField(
        child = serializers.CharField(min_length=5),
        min_length=1, required=True,write_only=True
    )

    milestones = MilestoneSerializer(many=True, required=False)

    image = serializers.ImageField(write_only=True, required=True)

    class Meta:
        model = Project
        fields = [
            'title', 'goal', 'country', 'location', 'longitude', 'latitude',
            'description', 'categories', 'image', 'problem_to_address',
            'solution', 'summary', 'video', 'milestones', 'image_url',
            ]
        extra_kwargs = {
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

    def create(self, validated_data):
        categories_data = validated_data.pop('categories',None)
        milestones_data = validated_data.pop('milestones', None)
        image = validated_data.pop('image', None)

        project = Project.objects.create(**validated_data)
        project.categories.set(categories_data)
        

        #handle image
        if image:
            try:
                image_url = resize_and_upload(image, f'{IMG['projects'] + validated_data.get('title')}')
                project.image_url = image_url
                project.save()
            except ValidationError as e:
                raise serializers.ValidationError({'image': e.message})  # Pass to serializer error
        
        try:
            for data in milestones_data:
                Milestone.objects.create(project=project, **data)
        except Exception as e:
            raise serializers.ValidationError({"milestones": f"Invalid milestone data: {str(e)}"})
        return project




    







# class UpdateProject(serializers.ModelSerializer):
#     categories = serializers.ListField(
#         child = serializers.CharField(min_length=5),
#         min_length=1,
#         required=True
#     )

#     milestones = MilestoneSerializer(many=True, required=True)

#     class Meta:
#         model = Project
#         fields = [
#             'title', 'goal', 'location', 'longitude', 'latitude',
#             'description', 'categories', 'image', 'problem_to_address',
#             'solution', 'summary', 'video', 'milestones'
#             ]
#         extra_kwargs = {
#             'title': {'required': True},
#             'goal':{'required': True},
#             'image':{'required': True},
#             'description':{'required': True},
#             'location': {'required': True},
#             'longitude':{'required': True},
#             'latitude':{'required': True},
#             'problem_to_address':{'required': True},
#             'solution':{'required': True},
#             'summary':{'required': True},
#             'video': {'required': False},
#         }