from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils import timezone
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import Token
from rest_framework.validators import UniqueValidator
from phonenumber_field.serializerfields import PhoneNumberField
from django.db.models import Q

from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .utils import (
    validate_otp, 
    generate_otp, 
    send_account_activation_otp, 
    resize_image, 
    resize_avatar,
)
from .models import Organization, Profile, Social, User

class UserRegistionUniqueValidator(UniqueValidator):
    message = "User with the provided email already exists"


class UserCreateSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True,required=True)

    password2 = serializers.CharField(write_only=True, required=True)

    wallet_address = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'password', 'password2', 'is_organization', 'wallet_address']

    def validate(self, attrs):
        password = attrs['password']
        password2=attrs['password2']
        if password != password2:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        if len(password)<8:
            raise serializers.ValidationError({"password": "Password should be eight or more characters."})
        return attrs

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
            'user',
            'name',
            'country',
            'address',
            'description',
            'socials',
            #'reg_no',
            #'cac_document',
            'website',
        ]


    # def validate_cac_document(self, value):
    #     if not value.name.endswith('.pdf'):
    #         raise serializers.ValidationError("Only PDF files are allowed.")
    #     if value.size > 1024 * 1024:
    #         raise serializers.ValidationError("File size cannot exceed 1MB.")
    #     return value

    def validate(self, attrs):
        name = attrs['name'].title()
        if Organization.objects.filter(name=name).exists():
            raise serializers.ValidationError("Organization name already exists")
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


class ProfileSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=Profile.objects.all())],
        required=True)
    
    class Meta:
        model = Profile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "anonymous"
        ]

    
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
                image = resize_avatar(image_file)
            except ValidationError as e:
                raise serializers.ValidationError({'image': e.message})  # Pass to serializer error

        instance.avatar = image
        instance.save()
        return instance



class AccountActivationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6)

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
    email = serializers.EmailField()

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
    email = serializers.EmailField()


class UserConfirmPasswordResetSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(min_length=5, max_length=5)

    def validate(self, attrs):        
        try:
            validate_password(password=attrs.get("new_password"), user = None)
        except ValidationError as err:
            raise serializers.ValidationError(err.messages)

        return attrs


class WalletSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['wallet_address']

   