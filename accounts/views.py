from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import generics, status,exceptions
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from rest_framework import permissions, parsers
from django.shortcuts import get_object_or_404
from drf_nested_multipart.parser import NestedMultipartAndFileParser
from .serializers import (
    ProfileSerializer,
    UpdateProfileSerializer,
    AccountActivationSerializer, 
    ResendAccountActivationSerializer,
    UserPasswordResetSerializer,
    UserConfirmPasswordResetSerializer,
    OrganizationSerializer,
    UpdateOrganizationSerializer,
    UploadAvatarSerializer,
    WalletSerializer,
    OrganizationKYCSerializer,
    TransactionSerializer,

    )
from .utils import validate_otp, generate_otp, send_reset_password_otp,send_mail, send_account_activation_otp,send_html_mail
from .models import Organization, Donor, Transaction
from .permissions import isOrgOwner, Is_Org,Is_Donor
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
# Create your views here.




class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class RegisterUserView(generics.GenericAPIView):
    serializer_class = ProfileSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Registration successful. Please check your email for the OTP to verify your account."},
            status= status.HTTP_201_CREATED)



class RegisterOrganizationView(generics.GenericAPIView): 
    serializer_class = OrganizationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = serializer.save()
        return Response(
            {"message": "Registration successful. Please check your email for the OTP to verify your account."},
            status= status.HTTP_201_CREATED)

class OrganizationKYC(generics.GenericAPIView):
    serializer_class = OrganizationKYCSerializer
    permission_classes = [permissions.IsAuthenticated,Is_Org]
    parser_classes=[parsers.MultiPartParser]
    
    def patch(self, request):
        org = get_object_or_404(Organization, user=request.user)
        serializer = self.get_serializer(instance=org, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        

class AccountActivationView(generics.GenericAPIView):
    serializer_class = AccountActivationSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Account Activated Successfully'}, status= status.HTTP_200_OK)
        


class UserResendActivationView(generics.GenericAPIView):
    serializer_class = ResendAccountActivationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message":"New Activation OTP has been sent to your email"})



class UserPasswordResetView(generics.GenericAPIView):
    serializer_class = UserPasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user=get_user_model().objects.get(email=serializer.validated_data.get("email"))
        except get_user_model().DoesNotExist:
            raise exceptions.NotAcceptable(
                {"email":"User with the given email does not exist."}
            )
        
        otp = generate_otp()
        user.otp = otp
        user.otp_expiry = timezone.now()
        user.save()
        send_reset_password_otp(email=serializer.validated_data.get("email"), otp=otp)
        return Response({"message":"OTP has been Sent to your email. Expires in 5 minutes"})



class UserConfirmPasswordResetView(generics.GenericAPIView):
    serializer_class = UserConfirmPasswordResetSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            otp = serializer.validated_data.get("otp")
            new_password = serializer.validated_data.get("new_password")
            user = validate_otp(otp)
            user.set_password(new_password)
            user.save()
            subject=f"Password Reset Successful",
            message=f"Your password has been reset sucessfully, you can now login with your new password",
            send_html_mail(user.email,subject,message)
            
            return Response({"message":"Password reset successful."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated,Is_Donor]
    parser_classes=[parsers.MultiPartParser]
    serializer_class = UpdateProfileSerializer

    def patch(self, request):
        profile = get_object_or_404(Donor, user=request.user)
        serializer = self.get_serializer(instance=profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateOrganizationView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated,isOrgOwner]
    parser_classes=[parsers.MultiPartParser]
    serializer_class = UpdateOrganizationSerializer

    def patch(self, request):
        organization = get_object_or_404(Organization, user=request.user)
        self.check_object_permissions(request, organization)
        serializer = self.get_serializer(instance=organization, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UploadAvatarView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser]
    serializer_class = UploadAvatarSerializer
    
    def patch(self,request):
        serializer = self.get_serializer(instance=request.user,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile picture updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetrieveOrganization(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()
    lookup_field = 'pk'


class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, 'is_organization', False):
            return OrganizationSerializer
        return ProfileSerializer

    def get_object(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, 'is_organization', False):
            return user.organization
        return user.profile



class AddWalletView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletSerializer
    
    def patch(self, request):
        serializer = self.get_serializer(instance=request.user,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class TransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        wallets= self.request.user.wallets.all()

        return Transaction.objects.filter(wallet__in=wallets,status=Transaction.SUCCESSFUL).distinct()

    

class TipTreasuryCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    def perform_create(self, serializer):
        serializer.save(
            status=Transaction.SUCCESSFUL,
            event=Transaction.TIP
            )

    