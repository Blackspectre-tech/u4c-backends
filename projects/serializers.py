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

                try:
                    image = resize_image(img)
                except ValidationError as e:
                    raise serializers.ValidationError({'image': e.message})

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

    def validate_proof_pdf(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError({"proof_pdf":"Only PDF files are allowed."})
        if value.size > 1024 * 1024:
            raise serializers.ValidationError({"proof_pdf":"File size cannot exceed 1MB."})
        return value




class MilestoneSerializer(serializers.ModelSerializer):
    images = MilestoneImagesSerializer(read_only=True, many=True)
    expenses = ExpensesSerializer(read_only=True, many=True)
    percentage = serializers.IntegerField()
    goal = serializers.DecimalField(required=False,decimal_places=2,max_digits=14)
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
        try:
            validated_data['image'] = resize_image(image)
    
        except ValidationError as e:
            raise serializers.ValidationError({'image': e.message})
        

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
        child=serializers.CharField(min_length=5),
        min_length=1, required=True, write_only=True
    )
    categories_display = serializers.SerializerMethodField(read_only=True)
    milestones = MilestoneSerializer(many=True, required=True)
    donations = DonationSerializer(read_only=True)
    duration_in_days = serializers.IntegerField(min_value=14, max_value=365)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'categories_display', 'goal', 'country', 'address', 'longitude', 'latitude',
            'description', 'categories', 'image', 'summary', 'duration_in_days',
            'video', 'milestones', 'donations', 'progress',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'title': {'required': True},
            'goal': {'required': True},
            'country': {'required': True},
            'description': {'required': True},
            'address': {'required': True},
            'longitude': {'required': True},
            'latitude': {'required': True},
            'summary': {'required': True},
            'video': {'required': False},
            'image': {'required': True},
            'duration_in_days': {'required': True},
            'progress': {'read_only': True},
        }

    def validate(self, attrs):
        instance = getattr(self, "instance", None)

        # ---------- Categories ----------
        incoming_category_names = attrs.get('categories')
        if incoming_category_names:
            print(incoming_category_names, flush=True)
            processed_category_names = [name.title() for name in incoming_category_names]
            found_category_objects = list(Category.objects.filter(name__in=processed_category_names))
            found_names_set = {cat.name for cat in found_category_objects}
            desired_names_set = set(processed_category_names)
            missing_names = desired_names_set - found_names_set

            if missing_names:
                raise serializers.ValidationError({"categories":f"The following categories do not exist: {missing_names}"})

            attrs['categories'] = found_category_objects

        # ---------- Milestones ----------
        milestones = attrs.get("milestones", None)
        new_goal = attrs.get("goal", getattr(instance, "goal", None))

        if milestones is not None:
            print(milestones,flush=True)
            if len(milestones) > 3:
                raise serializers.ValidationError({"milesontes":"You can only have a maximum of 3 milestones."})

            count = 0
            previous_percentage = 0
            for item in milestones:
                current_percentage = item['percentage']
                if current_percentage <= previous_percentage:
                    raise serializers.ValidationError({
                        'milestones.percentage': "Milestone percentages must be in increasing order."
                    })
                count += 1
                item['goal'] = (new_goal / 100) * Decimal(current_percentage)
                item['milestone_no'] = count
                previous_percentage = current_percentage

            if milestones[-1]['percentage'] != 100:
                raise serializers.ValidationError({
                    'milestones.percentage': "The final milestone must be set to 100%."
                })

            attrs['milestones'] = milestones

        # If ONLY goal changes (PATCH goal), recalc existing milestones
        elif "goal" in attrs and instance:
            for milestone in instance.milestones.all():
                milestone.goal = (Decimal(new_goal) / 100) * Decimal(milestone.percentage)
                milestone.save()

        return attrs

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_categories_display(self, obj):
        return [cat.name for cat in obj.categories.all()]

    def create(self, validated_data, **kwargs):
        categories_data = validated_data.pop('categories', None)
        milestones_data = validated_data.pop('milestones', None)
        image = validated_data.pop('image', None)

        with transaction.atomic():
            project = Project.objects.create(**validated_data)
            project.categories.set(categories_data)

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
        milestones_data = validated_data.pop('milestones', None)
        categories = validated_data.pop('categories', [])

        if new_image:
            try:
                validated_data['image'] = resize_image(new_image)
            except ValidationError as e:
                raise serializers.ValidationError({'image': e.message})

        with transaction.atomic():
            if milestones_data is not None:
                instance.milestones.all().delete()
                for milestone_data in milestones_data:
                    serializer = MilestoneSerializer(data=milestone_data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(project=instance)

            if categories:
                instance.categories.set(categories)

            instance = super().update(instance, validated_data)

        return instance






        
    

class ProjectListSerializer(serializers.ModelSerializer):
    organization = serializers.StringRelatedField(read_only=True)
    progress = serializers.ReadOnlyField()
    class Meta:
        model = Project
        fields = ['id','title','image','goal','progress','description','summary','status','organization',]