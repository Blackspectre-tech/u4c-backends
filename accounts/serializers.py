from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils import timezone
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import Token
from rest_framework.validators import UniqueValidator
from phonenumber_field.serializerfields import PhoneNumberField
from django.db.models import Q
from projects.models import Project
from django.core.exceptions import ValidationError
# from django.contrib.auth.password_validation import validate_password
from .utils import (
    validate_otp, 
    generate_otp, 
    send_account_activation_otp,
    validate_password,
    resize_image
)
from .models import Organization, Profile, Social, User, Transaction, Wallet
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema_field
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

class UserEmailUniqueValidator(UniqueValidator):
    message = "User with the provided email already exists"




class UsernameValidator(UniqueValidator):
    message = "Username already taken"


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email"})

        # If user exists but is not active
        if not user.is_active:
            otp = generate_otp()
            user.otp = otp
            user.otp_expiry = timezone.now()
            user.save()

            send_account_activation_otp(user.email, otp)

            return {
                "email": "Account not verified. OTP sent to your email.",
                "is_active": user.is_active,
            }

        # If user is active → check password
        if not user.check_password(password):
            raise serializers.ValidationError({
                "password": "Invalid password"
            })

        # Generate tokens if all good
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "is_active": user.is_active,
        }



class UserCreateSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        required = True
    )
    email = serializers.EmailField(
        validators=[UserEmailUniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True,required=True)

    password2 = serializers.CharField(write_only=True, required=True)

    # wallets = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'password', 'password2', 'is_organization', 'avatar','all_wallets']
        extra_kwargs = {
            'avatar': {'read_only': True},
            'all_wallets': {'read_only': True},
        }
    def validate(self, attrs):
        password = attrs['password']
        password2=attrs['password2']
        if password != password2:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        secure, message = validate_password(password)

        if not secure:
            raise serializers.ValidationError({"password": message})
        
        return attrs

    # @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    # def get_wallets(self, obj):
    #     return [wallet.address for wallet in obj.wallets.all()]

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
        )
        if validated_data.get('is_organization'):
            user.is_organization = True
        user.set_password(validated_data['password'])
        otp = generate_otp()
        user.otp = otp
        user.otp_expiry = timezone.now()
        user.save()
        send_account_activation_otp(user.email, otp)
        return user



class SocialsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Social
        fields = ['instagram', 'facebook', 'youtube', 'twitter']



class OrganizationSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()  #nested user creation
    socials = SocialsSerializer(required=False)
    #reg_no = serializers.CharField(min_length=7, max_length=8, required=True)
    website = serializers.CharField(required = False)
    
    class Meta:
        model = Organization
        fields = [
            'id','user','name','country','address','description','socials',
            'website','approved_projects','onchain_projects','total_projects','approval_status',
        ]
        extra_kwargs = {
        'id': {'read_only': True},
        'approved_projects': {'read_only': True},
        'approval_status': {'read_only': True},
        }  


    # def validate_cac_document(self, value):
    #     if not value.name.endswith('.pdf'):
    #         raise serializers.ValidationError("Only PDF files are allowed.")
    #     if value.size > 1024 * 1024:
    #         raise serializers.ValidationError("File size cannot exceed 1MB.")
    #     return value

    def validate(self, attrs):
        name = attrs['name'].title()
        if Organization.objects.filter(name=name).exists():
            raise serializers.ValidationError({"name":"Organization name already exists"})
        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        socials_data = validated_data.pop('socials', {})

        # Create user
        user_data['is_organization'] = True
        user_serializer = UserCreateSerializer(
            data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # Create organization
        org = Organization.objects.create(
            user=user,
            **validated_data
        )

        # Create socials
        socials = Social.objects.create(organization=org)
        for key, value in socials_data.items():
            setattr(socials, key, value)
        socials.save()

        return org


class OrganizationKYCSerializer(serializers.ModelSerializer):
    # reg_no = serializers.CharField(min_length=7, max_length=8, required=True)
    cac_document=serializers.FileField(required=True)


    class Meta:
        model = Organization
        fields = ['cac_document',]

    def validate_cac_document(self, value):
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        if value.size > 2*(1024*1024):
            raise serializers.ValidationError("File size cannot exceed 2MB.")
        return value

class ProfileSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()
    username = serializers.CharField(
        validators=[UsernameValidator(queryset=Profile.objects.all())],
        required=True)
    
    
    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "username",
            "first_name",
            "last_name",
            "anonymous",
        ]
        extra_kwargs = {
            'id': {'read_only': True},
        }

    
    def create(self, validated_data):
        user_data = validated_data.pop('user')

        # Create user
        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # Create UserProfile
        profile = Profile.objects.create(
            user=user,
            **validated_data
        )

        return profile



class UpdateProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=Profile.objects.all())],
        )
    
    class Meta:
        model = Profile
        fields = ['username', 'first_name', 'last_name', 'anonymous']



class UpdateOrganizationSerializer(serializers.ModelSerializer):
    socials = SocialsSerializer()

    class Meta:
        model = Organization
        fields = ['socials','website','address','description']

    # def validate_cac_document(self, value):
    #     if not value.name.endswith('.pdf'):
    #         raise serializers.ValidationError("Only PDF files are allowed.")
    #     if value.size > 1024 * 1024:
    #         raise serializers.ValidationError("File size cannot exceed 1MB.")
    #     return value    


    def update(self, instance, validated_data):
        # Update socials
        socials_data = validated_data.pop('socials', {})
        if socials_data:
            socials = instance.socials  # OneToOne
            for key, value in socials_data.items():
                setattr(socials, key, value)
            socials.save()

        return super().update(instance, validated_data)



class UploadAvatarSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    
    def update(self, instance, validated_data):
        image_file = validated_data.pop('image', None)

        if image_file:
            try:
                instance.avatar = image_file
                instance.save()
            except ValidationError as e:
                raise serializers.ValidationError({'image': e.message})
        
        return instance



class AccountActivationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6,required=True)

    def validate(self, attrs):
        otp = attrs['otp']
        user = validate_otp(otp)
        attrs['user'] = user
        
        return attrs
    
    def save(self,**kwargs):
        user = self.validated_data['user']
        user.is_active = True
        user.save(update_fields=["is_active"])

        return user

            

class ResendAccountActivationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        user = (
            get_user_model()
            .objects.filter(email=attrs["email"])
            .first()
        )
        if user is None:
            raise serializers.ValidationError(
                {"email": "No user with the given email."}
            )
        else:
            otp = generate_otp()
            user.otp = otp
            user.otp_expiry = timezone.now()
            user.save()
            send_account_activation_otp(attrs["email"], otp)
            return attrs



class UserPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)



class UserConfirmPasswordResetSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6,required=True)
    new_password = serializers.CharField(min_length=8, required=True)

    # def validate(self, attrs):        
    #     # try:
    #     #     validate_password(password=attrs.get("new_password"), user = None)
    #     # except ValidationError as err:
    #     #     raise serializers.ValidationError(err.messages)
    #     if len(attrs.get("new_password"))<8:
    #         raise serializers.ValidationError({"password": "Password should be eight or more characters."})

    #     return attrs



class WalletSerializer(serializers.ModelSerializer):
    wallet_address = serializers.CharField(write_only=True, required=True, allow_blank=False)
    class Meta:
        model = User
        fields = ['all_wallets','wallet_address']
        extra_kwargs = {
            'all_wallets': {'read_only': True},
        }
    
    def update(self, instance, validated_data):
        new_wallet = validated_data.pop('wallet_address', None)
        wallet,created = Wallet.objects.get_or_create(address__iexact=new_wallet)
        # if not created:
        #     #wallet.users.clear()
        #     wallet.users.set([instance])
        
        # instance.wallets.add(wallet)

        if instance.is_organization:
            all_projects= Project.objects.filter(deployed=False,)
            linked_orgs = wallet.users.filter(is_organization=True)
            if linked_orgs.first() != instance or linked_orgs.count() > 1:
                all_projects.filter(wallet_address__iexact=new_wallet).update(wallet_address=None)
            all_projects.filter(
                organization = instance.organization,
                deployed=False,
                ).update(wallet_address=new_wallet)
            instance.wallets.add(wallet)
        else:
            wallet.users.set([instance])
        
        # if instance.is_organization:
        #     org_pks = list(
        #         wallet.users
        #             .filter(is_organization=True)
        #             .values_list('pk', flat=True)[:2]
        #     )  
        #     needs_clearing = False
        #     if not org_pks:
        #         needs_clearing = True
        #     elif org_pks[0] != instance.pk:
        #         needs_clearing = True
        #     elif len(org_pks) > 1:
        #         needs_clearing = True

        #     with transaction.atomic():
        #         if needs_clearing:
        #             Project.objects.filter(
        #                 wallet_address=new_wallet,
        #                 deployed=False
        #             ).update(wallet_address=None)

        #         Project.objects.filter(
        #             organization=instance.organization,
        #             deployed=False
        #         ).update(wallet_address=new_wallet)
        #         instance.wallets.add(wallet)

        # else:
        #     wallet.users.set([instance])
            
        return instance



# class WalletSerializer(serializers.ModelSerializer):
#     wallet_address = serializers.CharField(write_only=True, required=True, allow_blank=False)
#     class Meta:
#         model = Wallet
#         fields = ['address','wallet_address']
#         extra_kwargs = {
#             'address': {'read_only': True},
#         }
    
#     def update(self, instance, validated_data):
#         new_wallet = validated_data.pop('wallet_address', None)
#         wallet,created = Wallet.objects.get_or_create(address=new_wallet)
#         # if not created:
#             #wallet.users.clear()
#         wallet.users.set([instance])
            
#         # instance.wallets.add(wallet)

#         if instance.users.filter().first().is_organization:
#             Project.objects.filter(
#                 organization = instance.organization,
#                 deployed=False,
#                 ).update(wallet_address=new_wallet)
                
#         return instance






class TransactionSerializer(serializers.ModelSerializer):
    wallet_address = serializers.CharField()
    class Meta:
        model = Transaction
        fields = ['tx_hash','wallet_address','created_at','event',]
        extra_kwargs = {
            'tx_hash': {'required': True},
            'event': {'read_only': True},
        }
        
    def create(self, validated_data):
        transaction_wallet= validated_data.pop('wallet_address',None)
        wallet = Wallet.objects.filter(address__iexact=transaction_wallet).first()
        if not wallet:
            raise serializers.ValidationError(
                {"wallet_address": "No user with the given wallet."}
            )
        validated_data['wallet']=wallet
        return super().create(validated_data)
    

