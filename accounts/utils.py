from datetime import timedelta
import time
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
import random
import string
import threading
from rest_framework.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import bleach
from bleach.css_sanitizer import CSSSanitizer
from bleach.sanitizer import Cleaner
import markdown
from datetime import datetime


# def send_email_in_thread(subject,message,from_email,recipient_list):
#     email_threading=threading.Thread(target=send_mail,args=(subject,message,from_email,recipient_list))
#     email_threading.start()
#     send_mail(subject,message,from_email,recipient_list)



def send_email_with_html(subject, context, html_template_path, from_email, recipient_list):
    # Render the HTML template with context
    html_content = render_to_string(html_template_path, context)
    
    # Fallback plain text version (optional)
    text_content = f"{subject}"  # Or generate a plain version of the message
    from_email = f'United4Change Team <{from_email}>'
    # Compose the email
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, "text/html")

    try:
        email.send(fail_silently=False)
    except Exception as e:
        print("Failed to send email:", e)

def send_email_in_thread(subject, context, html_template_path, from_email, recipient_list):
    # Start a new thread to send the email
    email_threading = threading.Thread(
        target=send_email_with_html,
        args=(subject, context, html_template_path, from_email, recipient_list)
    )
    email_threading.start()







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
    subject = "Your OTP for your account Activation"
    message = f"Your OTP is: {otp}.  It is valid for 5 minutes."
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    context={'title':'Account Activation','message': message,'year': datetime.now().year}
    html_template_path="email/mail_template.html",
    send_email_in_thread(subject,context,html_template_path,from_email,recipient_list)

def send_reset_password_otp(email, otp):
    subject = "Your OTP for Password Reset"
    message = f"Your OTP is: {otp}. It is valid for 5 minutes"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    context={'title':'Password Reset','message': message,'year': datetime.now().year}
    html_template_path="email/mail_template.html",
    send_email_in_thread(subject,context,html_template_path,from_email,recipient_list)





def project_approval_mail(project, reason=None, approved=True):
    if approved:
        subject = f"“{project.title}” approval"
        message = (
            f"{project.organization.name},"
            f"Your project campaign “{project.title}” has been approved"
            )
        title = 'Project Approved'
    else:   
        subject = f"Your project “{project.title}” was disapproved"
        message = (
            f"{project.organization.name},"
            f"Your project campaign “{project.title}” was disapproved for this reason:"
            f"{reason}")
        title = 'Project Disapproved'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [project.organization.user.email]
    context={'title':title,'message': message,'year': datetime.now().year}
    html_template_path="email/mail_template.html",
    send_email_in_thread(subject,context,html_template_path,from_email,recipient_list)



def organization_approval_mail(organization, reason=None, approved=True):
    if approved:
        subject = f"“{organization.name}” approval"
        message = (
            f"We are pleased to inform Your Organization “{organization.name}” has been approved, you can now create projects  on our platform"
            )
        title = 'Organization Approved'
    else:   
        subject = f"Your Organization “{organization.name}” was disapproved"
        message = (
            f"Your organization “{organization.name}” was disapproved for the following reason:"
            )
        title = 'Organization Disapproved'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [organization.user.email]
    html_template_path="email/mail_template.html",
    context={'reason': reason,'title':title,'message': message,'year': datetime.now().year}
    send_email_in_thread(subject,context,html_template_path,from_email,recipient_list)




def resize_avatar(image_file):
    try:
        img = Image.open(image_file)
        img.verify()  # Will raise an exception if not a valid image
        image_file.seek(0)
    except Exception:
        raise ValidationError("Uploaded file is not a valid image.")
    img = Image.open(image_file)
    img = img.convert("RGB")
    img = img.resize((600, 600))  # Resize

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True, progressive=True) # setting teh quality to 85%
    buffer.seek(0)

    # result = upload(buffer, folder=f"u4c/avatars")
    # return result['secure_url'], result['public_id']
    return buffer

def resize_image(image_file, max_size=1024):
    try:
        img = Image.open(image_file)
        img.verify()  # Check if it’s a valid image
        image_file.seek(0)
    except Exception:
        raise ValidationError("Uploaded file is not a valid image.")

    # Reopen and resize
    img = Image.open(image_file)
    img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True, progressive=True)
    buffer.seek(0)

    # Create InMemoryUploadedFile (mimics a real uploaded image)
    resized_file = InMemoryUploadedFile(
        file=buffer,
        field_name="image",
        name=image_file.name,  # preserve original filename
        content_type="image/jpeg",
        size=buffer.getbuffer().nbytes,
        charset=None
    )

    return resized_file


# def upload_pdf(file):
#     result = upload(
#         file,
#         resource_type="raw",
#         folder="u4c/pdf"
#     )
#     return result["secure_url"], result['public_id']





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
