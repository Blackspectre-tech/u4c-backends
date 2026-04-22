from rest_framework import serializers
from .models import (
    Project, Category, Milestone, 
    MilestoneImage, Expense, Update,
    Comment,Donation, ExpenseDocument,
    ProjectImage,
    )
from accounts.models import Transaction, Wallet
from accounts.utils import resize_image
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from website.models import ErrorLog
import traceback



class MilestoneImagesSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000,allow_empty_file=False),
        required=True, write_only=True,allow_empty=False,max_length=6,)
        
    class Meta:
        model = MilestoneImage
        fields = ['id','image', 'images']
        extra_kwargs = {
            'image': {'required': False},
            'id': {'read_only': True},
        }

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        milestone = self.context.get('milestone')
        instances = []
        existing_images = milestone.images.all()
        if images:
            with transaction.atomic():
            
                if existing_images:
                    existing_images.delete()

                for img in images:

                    # try:
                    #     image = resize_image(img)
                    # except ValidationError as e:
                    #     raise serializers.ValidationError({'image': e.message})

                    instances.append(MilestoneImage(
                        milestone=milestone,
                        image=img,
                    ))
                
                MilestoneImage.objects.bulk_create(instances)

        return milestone
    



class ExpenseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseDocument
        fields = ['id', 'document', 'document_type', 'uploaded_at']

class ExpenseSerializer(serializers.ModelSerializer):
    # Field for viewing existing documents
    documents = ExpenseDocumentSerializer(many=True, read_only=True)
    
    # Virtual fields for uploading via this endpoint
    document = serializers.FileField(write_only=True, required=False)
    document_type = serializers.ChoiceField(
        choices=ExpenseDocument.TYPE_CHOICES, 
        write_only=True, 
        required=True
    )

    class Meta:
        model = Expense
        fields = [
            'id', 'amount_spent', 'milestone', 'description', 
            'date', 'document', 'document_type', 'documents'
        ]
        read_only_fields = ['milestone', 'id']

    def create(self, validated_data):
        doc_file = validated_data.pop('document', None)
        doc_type = validated_data.pop('document_type', None)
        
        expense = Expense.objects.create(**validated_data)
        
        if doc_file:
            ExpenseDocument.objects.create(
                expense=expense, 
                document=doc_file, 
                document_type=doc_type
            )
        return expense

    def update(self, instance, validated_data):
        doc_file = validated_data.pop('document', None)
        doc_type = validated_data.pop('document_type', None)

        # 1. Update the main Expense fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 2. Handle Document Overwriting
        if doc_file:
            # We look for a document linked to THIS expense with THIS type
            # defaults= values are what get updated if a match is found
            ExpenseDocument.objects.update_or_create(
                expense=instance, 
                document_type=doc_type,
                defaults={'document': doc_file}
            )
            
        return instance




class MilestoneSerializer(serializers.ModelSerializer):
    images = MilestoneImagesSerializer(read_only=True, many=True)
    expenses = ExpenseSerializer(read_only=True, many=True)
    percentage = serializers.IntegerField()
    goal = serializers.DecimalField(required=False,decimal_places=2,max_digits=14)
    milestone_no = serializers.IntegerField(required=False)

    class Meta:
        model = Milestone
        fields = ['id','milestone_no','percentage','title','details','goal','images',
          'expenses','status', 'contract_id','approved','withdrawn']
        extra_kwargs = {
        'id': {'read_only': True},
        }
    
    



class PostUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Update
        fields = ['title', 'details','image','created_at']
        extra_kwargs = {
            'created_at': {'read_only': True},
            'image': {'required': True},
        }

    # def create(self, validated_data):
    #     image = validated_data.pop('image', None)
    #     try:
    #         validated_data['image'] = resize_image(image)
    
    #     except ValidationError as e:
    #         raise serializers.ValidationError({'image': e.message})
        

    #     return Update.objects.create(**validated_data) 




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

    class Meta:
        model = Donation
        fields = [ 'id','username', 'amount', 'wallet_address', 'refundable','refunded']
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {'read_only': True},
            'refunded': {'read_only': True},
            'refundable': {'read_only': True},
            'tip': {'required': False},
        }
    # @extend_schema_field(serializers.CharField)
    # def get_username(self,obj):
    #     return obj.username













class ProjectImagesSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000,allow_empty_file=False),
        required=True, write_only=True,allow_empty=False,max_length=5,)
        
    class Meta:
        model = ProjectImage
        fields = ['id','image', 'images']
        extra_kwargs = {
            'image': {'required': False},
            'id': {'read_only': True},
        }

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        project = self.context.get('project')
        instances = []
        existing_images = project.images.all()
        if images:
            with transaction.atomic():
            
                if existing_images:
                    existing_images.delete()

                for img in images:

                    # try:
                    #     image = resize_image(img)
                    # except ValidationError as e:
                    #     raise serializers.ValidationError({'image': e.message})

                    instances.append(ProjectImage(
                        project=project,
                        image=img,
                    ))
                
                ProjectImage.objects.bulk_create(instances)

        return project














class ProjectSerializer(serializers.ModelSerializer):

    categories = serializers.ListField(
        child=serializers.CharField(min_length=5),
        min_length=1, required=True, write_only=True
    )
    categories_display = serializers.SerializerMethodField(read_only=True)
    milestones = MilestoneSerializer(many=True, required=True)
    extra_images = ProjectImagesSerializer(source='images', read_only=True, many=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'organization_id','contract_id','title', 'categories_display', 'goal', 'country', 'address',
            'description', 'categories', 'image', 'extra_images', 'summary', 'duration_in_days','wallet_address',
            'milestones','progress','approval_status','status','created_at','deployed_at','deployed','deadline',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'title': {'required': True},
            'goal': {'required': True},
            'country': {'required': True},
            'description': {'required': True},
            'address': {'required': True},
            'summary': {'required': True},
            'image': {'required': True},
            'duration_in_days': {'required': True},
            'approval_status': {'read_only': True},
            'status': {'read_only': True},
            'progress': {'read_only': True},
            'created_at': {'read_only': True},
            'wallet_address': {'required': False},
            'contract_id': {'read_only': True},
            'deployed': {'read_only': True},
            'deadline': {'read_only': True},
            'deployed_at': {'read_only': True},
        }

    def validate(self, attrs):
        try:
            instance = getattr(self, "instance", None)

            # ---------- Categories ----------
            incoming_category_names = attrs.get('categories')
            if incoming_category_names:
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
        except Exception as e:
            ErrorLog.objects.create(
                data=attrs,
                error=f'LOGICAL ERROR: {str(e)}',
                notes=traceback.format_exc()
            )
            raise serializers.ValidationError({'error': str(e)})

        return attrs


    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_categories_display(self, obj):
        return [cat.name for cat in obj.categories.all()]
    

    def create(self, validated_data, **kwargs):
        try:
            categories_data = validated_data.pop('categories', None)
            milestones_data = validated_data.pop('milestones', None)
            # image = validated_data.pop('image', None)

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

                project.save()
            return project
        
        except Exception as e:
            ErrorLog.objects.create(
                data=validated_data,
                error=f'LOGICAL ERROR: {str(e)}',
                notes=traceback.format_exc()
            )
            raise serializers.ValidationError({'error': str(e)})



    def update(self, instance, validated_data):
        # new_image = validated_data.get('image')
        milestones_data = validated_data.pop('milestones', None)
        categories = validated_data.pop('categories', [])

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

        instance.approval_status = Project.PENDING
        return instance




class ProjectListSerializer(serializers.ModelSerializer):
    organization = serializers.StringRelatedField(read_only=True)
    progress = serializers.ReadOnlyField()
    class Meta:
        model = Project
        fields = ['id','title','image','goal','progress','description','summary','status','organization','created_at','deadline',]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }



class DonationTransactionSerializer(serializers.ModelSerializer):
    wallet = serializers.CharField()
    class Meta:
        model = Transaction
        fields = ['tx_hash','created_at','status','event','tip','amount','wallet',]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'tip': {'required': True},
            'amount': {'required': True},
            'wallet': {'required': True},
            'event': {'read_only': True},
            'tx_hash': {'read_only': True},
            'status': {'read_only': True},
        }
        
    def create(self, validated_data):
        transaction_wallet= validated_data.pop('wallet',None)
        wallet = Wallet.objects.filter(address__iexact=transaction_wallet).first()
        if not wallet:
            raise serializers.ValidationError(
                {"wallet": "No user with the given wallet."}
            )
        validated_data['wallet']=wallet

        return super().create(validated_data)
    

