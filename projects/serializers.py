from rest_framework import serializers
from .models import (
    Project, Category, Milestone, 
    MilestoneImage, Expense, Update,
    Comment,Donation,
    )
from accounts.models import Transaction, Wallet
from accounts.utils import resize_image
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from contract.models import ContractLog
import traceback



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



class ProjectSerializer(serializers.ModelSerializer):

    categories = serializers.ListField(
        child=serializers.CharField(min_length=5),
        min_length=1, required=True, write_only=True
    )
    categories_display = serializers.SerializerMethodField(read_only=True)
    milestones = MilestoneSerializer(many=True, required=True)
    donations = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True,read_only=True)
    class Meta:
        model = Project
        fields = [
            'id', 'organization_id','contract_id','title', 'categories_display', 'goal', 'country', 'address',
            'description', 'categories', 'image', 'summary', 'duration_in_days','wallet_address',
            'milestones', 'donations', 'progress','approval_status','status','created_at','deployed','deadline','comments'
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
            ContractLog.objects.create(
                data=attrs,
                error=f'LOGICAL ERROR: {str(e)}',
                notes=traceback.format_exc()
            )
            raise serializers.ValidationError({'error': str(e)})

        return attrs


    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_categories_display(self, obj):
        return [cat.name for cat in obj.categories.all()]
    


    @extend_schema_field(serializers.ListField(child=DonationSerializer()))
    def get_donations(self, obj):
        # donations__wallet__users__is_organization=False
        #donations = obj.donations.filter(refunded=False, wallet__isnull=False,wallet__users__is_organization=False)
        donations = obj.donations.filter(
            refunded=False,
            wallet__isnull=False,
            wallet__users__is_organization=False
        ).distinct()
        if donations:
            return DonationSerializer(donations, many=True).data
        else:
            return []



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

                # if image:
                #     try:
                #         image = resize_image(image)
                #         project.image = image
                #     except ValidationError as e:
                #         raise serializers.ValidationError({'image': e.message})

                project.save()
            return project
        
        except Exception as e:
            ContractLog.objects.create(
                data=validated_data,
                error=f'LOGICAL ERROR: {str(e)}',
                notes=traceback.format_exc()
            )
            raise serializers.ValidationError({'error': str(e)})



    def update(self, instance, validated_data):
        # new_image = validated_data.get('image')
        milestones_data = validated_data.pop('milestones', None)
        categories = validated_data.pop('categories', [])

        # if new_image:
        #     try:
        #         validated_data['image'] = resize_image(new_image)
        #     except ValidationError as e:
        #         raise serializers.ValidationError({'image': e.message})

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
    

