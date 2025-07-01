from datetime import timedelta
import time
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
import random
import string
import threading
from rest_framework.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from cloudinary.uploader import upload
from PIL import Image
import bleach
from bleach.css_sanitizer import CSSSanitizer
from bleach.sanitizer import Cleaner
import markdown

def send_email_in_thread(subject,message,from_email,recipient_list):
    email_threading=threading.Thread(target=send_mail,args=(subject,message,from_email,recipient_list))
    email_threading.start()
    send_mail(subject,message,from_email,recipient_list)


def generate_otp(length=6):
    characters = string.digits
    otp = "".join(random.choice(characters) for _ in range(length))
    return otp


# def validate_otp(otp, minutes=5):
#     try:
#         user = get_user_model().objects.get(otp=otp)
#     except get_user_model().DoesNotExist:
#         return None
#     time_diff = timezone.now() - user.otp_expiry
#     if user.otp == otp and time_diff < timedelta(minutes=minutes):
#         user.otp = None
#         user.otp_expiry = None
#         return user

def validate_otp(otp, minutes=5):
    User = get_user_model()

    try:
        user = User.objects.get(otp=otp)
    except User.DoesNotExist:
        raise ValidationError("Invalid OTP.")

    if timezone.now() - user.otp_expiry > timedelta(minutes=minutes):
        raise ValidationError("OTP has expired.")

    if user.otp != otp:
        raise ValidationError("Incorrect OTP.")

    # Invalidate OTP after successful use
    user.otp = None
    user.otp_expiry = None
    user.save(update_fields=["otp", "otp_expiry"])

    return user

# def send_otp_by_phone(phone_number,otp):
#     account_sid="your_account_id"
#     auth_token="your_auth_token"
#     twilio_phone_number="your_twilio_phone_number"

#     client=Client(account_sid,auth_token)
#     message=client.messages.create(
#        body=f"Your OTP is: {otp}",
#        from_=twilio_phone_number,
#        to=phone_number

#     )


# def send_verify_email_otp(email, otp):
#     subject = "Your OTP for Email Verification"
#     message = f"Your OTP is: {otp}"
#     from_email = settings.EMAIL_HOST_USER
#     recipient_list = [email]
#     sendreset_password_otp(email, otp):
#     subject = "Your OTP for Password Reset"
#     message = f"Your OTP is: {otp}. It is valid for 10mins"
#     from_email = settings.EMAIL_HOST_USER
#     recipient_list = [email]
#     send_email_in_thread(subject, message, from_email, recipient_list)


# def send_reset_pin_otp(email, otp):
#     subject = "Your OTP for PIN Reset"
#     message = f"Your OTP is: {otp}. It is valid for 10mins"
#     from_email = settings.EMAIL_HOST_USER
#     recipient_list = [email]
#     send_email_in_thread(subject, message, from_email, recipient_list)




def send_account_activation_otp(email, otp):
    subject = "Your OTP for your account Activation/Deactivation"
    message = f"Your OTP is: {otp}.  It is valid for 5 minutes."
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_email_in_thread(subject, message, from_email, recipient_list)

def send_reset_password_otp(email, otp):
    subject = "Your OTP for Password Reset"
    message = f"Your OTP is: {otp}. It is valid for 5 minutes"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_email_in_thread(subject, message, from_email, recipient_list)





def project_approval_mail(project, reason=None, approved=True):
    if approved:
        subject = f"“{project.title}” approval"
        message = (
            f"{project.organization.name},\n\n"
            f"Your project request “{project.title}” has been approved:\n\n"
            f"Regards,\n United-4-Change Admin Team")
    else:   
        subject = f"Your project “{project.title}” was disapproved"
        message = (
            f"{project.organization.name},\n\n"
            f"Your project request “{project.title}” was disapproved for this reason:\n\n"
            f"{reason}\n\nRegards,\nAdmin Team")
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [project.organization.user.email]
    send_email_in_thread(subject, message, from_email, recipient_list)



def organization_approval_mail(organization, reason=None, approved=True):
    if approved:
        subject = f"“{organization.name}” approval"
        message = (
            f"{organization.name},\n\n"
            f"Your Organization “{organization.name}” has been approved:\n\n"
            f"Regards,\n United-4-Change Admin Team")
    else:   
        subject = f"Your Organization “{organization.name}” was disapproved"
        message = (
            f"{organization.name},\n\n"
            f"Your organization “{organization.title}” was disapproved for this reason:\n\n"
            f"{reason}\n\nRegards,\nAdmin Team")
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [organization.user.email]
    send_email_in_thread(subject, message, from_email, recipient_list)




def resize_and_upload_avatar(image_file):
    img = Image.open(image_file)
    img = img.convert("RGB")
    img = img.resize((600, 600))  # Resize

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True, progressive=True) # setting teh quality to 85%
    buffer.seek(0)

    result = upload(buffer, folder=f"u4c/avatars")
    return result['secure_url']


def resize_and_upload(image_file, location, max_size=1024):
    img = Image.open(image_file)
    img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True, progressive=True) # setting teh quality to 85%
    buffer.seek(0)

    result = upload(buffer, folder=f"u4c/{location}")
    return result['secure_url']

def upload_pdf(file):
    result = upload(
        file,
        resource_type="raw",
        folder="cac_documents"
    )
    return result["secure_url"]

# def resize_and_upload(image_file, location, max_size=1024):
#     img = Image.open(image_file)
#     img = img.convert("RGB")

#     # Resize with aspect ratio preserved
#     img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

#     buffer = BytesIO()
#     img.save(buffer, format='JPEG', quality=85, optimize=True, progressive=True)
#     buffer.seek(0)

#     result = upload(buffer, folder=f"u4c/{location}")
#     return result['secure_url']





ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p', 'h1', 'h2', 'h3', 'pre', 'code', 'hr', 'br','ul', 'ol', 'li', 'br',
]
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'style'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title'],
}
ALLOWED_CSS_PROPERTIES = [
    'list-style-type', 'margin-left', 'padding-left', 'margin-bottom'
]

css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)
html_cleaner = Cleaner(
    tags=ALLOWED_TAGS,
    attributes=ALLOWED_ATTRIBUTES,
    css_sanitizer=css_sanitizer,
    strip=True,            
    strip_comments=True    
)
