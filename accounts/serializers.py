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
    resize_and_upload, 
    resize_and_upload_avatar,
    upload_pdf
)
from .models import Organization, UserProfile, Social

class UserRegistionUniqueValidator(UniqueValidator):
    message = "User with the provided email already exists"


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = '__all__'


class SocialsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Social
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer):
    socials = SocialsSerializer()

    class Meta:
        model = Organization
        fields = '__all__'


class UserRegisterationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(
        required=True,
        validators=[UserRegistionUniqueValidator(queryset=get_user_model().objects.all())],
        )
    phone_number = PhoneNumberField()
    password = serializers.CharField(write_only=True,required=True,)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = get_user_model()
        fields = [
            "password",
            "email",
            "phone_number",
        ]
        extra_kwargs = {
            "email": {"required": True},
            "password": {"required": True},
            "phone_number": {"reqired": True},
        }

    def validate(self, attrs):
        try:
            validate_password(password=attrs["password"], user = None)
        except ValidationError as err:
            raise serializers.ValidationError(err.messages)
        
        username = attrs['username'].lower()
        if UserProfile.profile.objects.filter(username=username).exists() :
            raise serializers.ValidationError("Username already exist")

        return attrs
    
    def create(self, validated_data):

        user = get_user_model().objects.create(
            email=validated_data["email"],
            phone_number = validated_data['phone_number']
            )

        user.set_password(validated_data["password"])
        otp = generate_otp()
        user.otp = otp
        user.otp_expiry = timezone.now()
        user.save()
        send_account_activation_otp(validated_data.get("email"), otp)
        user.profile.objects.create(
            user = user,
            username = validated_data['username'],
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
        )

        return user


class OrganizationRegisterationSerializer(serializers.ModelSerializer):
    socials = SocialsSerializer(required=False)
    email = serializers.EmailField(
        required=True,
        validators=[UserRegistionUniqueValidator(queryset=get_user_model().objects.all())],
        )
    password = serializers.CharField(write_only=True,required=True,)
    cac_document = serializers.FileField(write_only=True, required =True)
    
    class Meta:
        model = get_user_model()
        fields = [
            "password",
            "email",
            "name",
            "country",
            "location",
            "description",
            "socials",
            "reg_no"
            "cac_document",
        ]
        extra_kwargs = {
            "email": {"required": True},
            "password": {"required": True},
            "name": {"reqired": True},
            "country": {"reqired": True},
            "location": {"reqired": True},
            "description": {"reqired": True},
            "reg_no": {"reqired": True},
            "cac_document": {"reqired": True},
        }


    # def validate_cac_document(self, value):
    #     max_size_mb = 1
    #     if value.size > max_size_mb * 1024 * 1024:
    #         raise serializers.ValidationError("File size must not exceed 1MB.")
    #     return value

    def validate(self, attrs):
        try:
            validate_password(password=attrs["password"], user = None)
        except ValidationError as err:
            raise serializers.ValidationError(err.messages)

        name = attrs['name'].title()
        if Organization.objects.filter(name=name).exists() :
            raise serializers.ValidationError("Organization name already exist")


    def create(self, validated_data):
        socials_data = validated_data.pop('socials', {})
        doc = validated_data.pop('cac_document', {})

        user = get_user_model().objects.create(
            email=validated_data["email"],
            phone_number = validated_data['phone_number'],
            is_organization = True
            )

        user.set_password(validated_data["password"])
        otp = generate_otp()
        user.otp = otp
        user.otp_expiry = timezone.now()
        user.save()
        send_account_activation_otp(validated_data.get("email"), otp)
        #for pdf upload
        doc_url = upload_pdf(doc)

        org = Organization.objects.create(
            user = user,
            name = validated_data['name'],
            country = validated_data['country'],
            location = validated_data['location'],
            description = validated_data['description'],
            reg_no = validated_data['reg_no'],
            cac_document_url = doc_url

        )
        socials = Social.objects.create(organization=org)
        #update socials
        if socials_data:
            for key, value in socials_data.items():
                setattr(socials, key, value)
            socials.save()

        return user




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
    



class UpdateProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    image = serializers.ImageField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['phone_number', 'image', 'profile']
        

    def update(self, instance, validated_data):
        # Handle avatar
        avatar = validated_data.pop('image', None)
        if avatar:
            avatar_url = resize_and_upload_avatar(avatar)
            instance.avatar = avatar_url

        # Handle profile data
        profile_data = validated_data.pop('profile', {})
        profile = instance.profile  # OneToOne related model

        username = profile.get('username').lower()
        if username:
            #checks if the username exists excluding the curent user's username
            if UserProfile.objects.filter(Q(username=username) & ~Q(id=profile.id)).exists():
                raise serializers.ValidationError({'username':'username already exists'})

        for key, value in profile_data.items():
            setattr(profile, key, value)
        profile.save()

        return super().update(instance, validated_data)





class UpdateOrganizationSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()
    socials = SocialsSerializer()
    cac_document = serializers.FileField(write_only=True)
    image = serializers.ImageField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['phone_number', 'image', 'organization', 'socials', 'cac_document']
        

    def update(self, instance, validated_data):
        # Handle avatar
        avatar = validated_data.pop('image', None)
        doc = validated_data.pop('cac_document', None)
        if avatar:
            avatar_url = resize_and_upload_avatar(avatar)
            instance.avatar = avatar_url

        # Handle profile data
        organization_data = validated_data.pop('organization', {})
        organization = instance.organization  # OneToOne related model

        name = organization.get('name').title()
        if name:
            #checks if the username exists excluding the curent user's username
            if UserProfile.objects.filter(Q(name=name) & ~Q(id=organization.id)).exists():
                raise serializers.ValidationError({'name':'organization name already exists'})
            organization['name'] = name

        if doc:
            doc_url = upload_pdf(doc)
            organization['cac_document_url']=doc_url

        for key, value in organization_data.items():
            setattr(organization, key, value)
        organization.save()

        # Update socials
        socials_data = validated_data.pop('socials', {})
        socials = organization.socials  # OneToOne
        for key, value in socials_data.items():
            setattr(socials, key, value)
        socials.save()

        return super().update(instance, validated_data)

