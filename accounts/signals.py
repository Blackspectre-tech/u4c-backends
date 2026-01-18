# # profiles/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Organization, Kyc

# @receiver(post_save, sender=Organization)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Kyc.objects.get_or_create(organization=instance)
        
