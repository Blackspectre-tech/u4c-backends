# # profiles/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import UserProfile, Organization
# from accounts.models import User

# @receiver(post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         if instance.is_organization:
#             Organization.objects.create(user=instance)
#         else:
#             UserProfile.objects.create(user=instance)
