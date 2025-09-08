from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from accounts.utils import send_html_mail
from .models import Faq
#from django.db import transaction
#from drf_spectacular.utils import extend_schema_field


class ContactUsSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone = PhoneNumberField(required=False)
    organization = serializers.CharField(required=False)
    message = serializers.CharField(required=True)
    inquiry_type = serializers.CharField(required=True)

    def save(self):
        data = self.validated_data
        email = 'support@united-4-change.org'
        subject = f"U4c Support inquiry: {data['inquiry_type']}"
        message = f"""
            Contact Us message from: {data['full_name']}
            
            User Information:
                email: {data.get("email")}
                phone number: {data.get("phone")}
                organization: {data.get("organization")}
            
            Message:
                {data.get("message")}
            """
        send_html_mail(email, subject, message, support=False)

class FaqSerializer(serializers.ModelSerializer):

    class Meta:
        model = Faq
        fields = ['question', 'answer',]
        # extra_kwargs = {
        # 'id': {'read_only': True},
        # }  
    