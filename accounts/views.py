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
    DonorSerializer,
    UpdateDonorSerializer,
    AccountActivationSerializer, 
    ResendAccountActivationSerializer,
    UserPasswordResetSerializer,
    UserConfirmPasswordResetSerializer,
    OrganizationSerializer,
    UpdateOrganizationSerializer,
    UploadAvatarSerializer,
    WalletSerializer,
    OrganizationKycItemSubmitSerializer,
    TransactionSerializer,

    )
from .utils import validate_otp, generate_otp, send_reset_password_otp,send_mail, send_account_activation_otp,send_html_mail
from .models import (
    Organization, 
    Donor,
    Transaction,
    KycRequirement,
    OrganizationKycItem,
    KycDocumentStatus,
)
from .permissions import isOrgOwner, Is_Org,Is_Donor
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
# Create your views here.




class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class RegisterUserView(generics.GenericAPIView):
    serializer_class = DonorSerializer
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
    serializer_class = UpdateDonorSerializer

    def patch(self, request):
        donor = get_object_or_404(Donor, user=request.user)
        serializer = self.get_serializer(instance=donor, data=request.data, partial=True)
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
        return DonorSerializer

    def get_object(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, 'is_organization', False):
            return user.organization
        return user.donor



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













class OrganizationKycView(APIView):
    permission_classes = [permissions.IsAuthenticated,Is_Org]

    def get(self, request):
        org = request.user.organization

        requirements = KycRequirement.objects.all()
        items = {
            item.requirement_id: item
            for item in OrganizationKycItem.objects.filter(organization=org)
        }

        response_requirements = []

        for requirement in requirements:
            item = items.get(requirement.id)

            if item:
                response_requirements.append({
                    "name": requirement.name,
                    "type": requirement.field_type,
                    "submitted": True,
                    "value": None if requirement.field_type == "document" else item.value,
                    "status": item.status,
                })
            else:
                response_requirements.append({
                    "name": requirement.name,
                    "type": requirement.field_type,
                    "submitted": False,
                    "status": "not_submitted",
                })

        return Response({
            "kyc_status": org.kyc_status,
            "requirements": response_requirements,
        })

    def post(self, request):
        return self._submit(request)

    def patch(self, request):
        return self._submit(request)

    def _submit(self, request):
        serializer = OrganizationKycItemSubmitSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        organization = request.user.organization
        requirement = serializer.validated_data["requirement"]

        item, _ = OrganizationKycItem.objects.get_or_create(
            organization=organization,
            requirement=requirement
        )

        # Prevent overwrite of approved items
        if item.status == KycDocumentStatus.APPROVED:
            return Response({
                "detail": "This KYC item has already been approved."
            }, status=400)

        # Reset review state
        item.status = KycDocumentStatus.PENDING
        item.rejection_reason = None
        item.reviewed_at = None
        item.reviewed_by = None

        if requirement.field_type == requirement.DOCUMENT:
            item.file = serializer.validated_data.get("file")
            item.value = None
        else:
            item.value = serializer.validated_data.get("value")
            item.file = None

        item.save()

        return Response({
            "message": "KYC item submitted successfully.",
            "requirement": requirement.name,
            "status": item.status,
            "kyc_status": organization.kyc_status
        })

