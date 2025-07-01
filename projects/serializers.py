from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Project, Category, Milestone, 
    Milestone_Images, Expense, Update,
    )
from accounts.utils import resize_and_upload
from core.settings import IMG


class MiliestoneImagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Milestone_Images
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    # images = MiliestoneImagesSerializer(many=True)

    class Meta:
        model = Milestone
        fields = '__all__'

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
        return super().create(validated_data)
    

class MilestoneUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000,allow_empty_file=False),
        required=False, write_only=True,allow_empty=True,  # Optional: Allows an empty list
        max_length=10,     #Limits the number of items
    )
    class Meta:
        model = Milestone
        fields = ['images','title','details',]


    def update(self, instance, validated_data):

        images = validated_data.pop('images', None)
        title = instance.title
        if images:
            for img in images:
                image_url = resize_and_upload(img,{IMG['milestones']}+{title})
                Milestone_Images.objects.create(milestone=instance, image=image_url)
        return super().update(instance, validated_data)


class CreateProjectSerializer(serializers.ModelSerializer):
    
    categories = serializers.ListField(
        child = serializers.CharField(min_length=5),
        min_length=1,
        required=True
    )

    milestones = MilestoneSerializer(many=True, required=True)

    image = serializers.ImageField(write_only=True)

    class Meta:
        model = Project
        fields = [
            'title', 'goal', 'location', 'longitude', 'latitude',
            'description', 'categories', 'image', 'problem_to_address',
            'solution', 'summary', 'video', 'milestones'
            ]
        extra_kwargs = {
            'title': {'required': True},
            'goal':{'required': True},
            'image':{'required': True},
            'description':{'required': True},
            'location': {'required': True},
            'longitude':{'required': True},
            'latitude':{'required': True},
            'problem_to_address':{'required': True},
            'solution':{'required': True},
            'summary':{'required': True},
            'video': {'required': False},
        }

    def validate(self, attrs):
        categories = attrs.get('categories')
        processed_categories = [name.title() for name in categories]
        found_category_objects = Category.objects.filter(name__in=processed_categories)
        found_names_set = set(found_category_objects.values_list('name', flat=True))
         # Create a set of all names client sent
        desired_names_set = set(processed_categories) 
        
        # Find which desired names were NOT found
        missing_names = desired_names_set - found_names_set 

        if missing_names:
            raise serializers.ValidationError(f"The following categories do not exist: {missing_names}")
        
        return attrs


    def create(self, validated_data):
        categories_data = validated_data.pop('categories',None)
        milestones_data = validated_data.pop('milestones', None)
        image = validated_data.pop('image', None)

        # processed_categories = [name.title() for name in categories_data]
        # found_category_objects = Category.objects.filter(name__in=processed_categories)
        # found_names_set = set(found_category_objects.values_list('name', flat=True))
        
        # # Create a set of all names client sent
        # desired_names_set = set(processed_categories) 
        
        # # Find which desired names were NOT found
        # missing_names = desired_names_set - found_names_set 

        # if missing_names:
        #     raise serializers.ValidationError(f"The following categories do not exist: {missing_names}")
        
        #handle image
        image_url = resize_and_upload(image, f'{IMG['projects'] + validated_data.get('title')}')
        validated_data['image_url'] = image_url

        project = Project.objects.create(**validated_data)
        # project.categories.set(found_category_objects)
        project.categories.set(categories_data)
        project.save()

        
        for data in milestones_data:
            Milestone.objects.create(project=project, **data)

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