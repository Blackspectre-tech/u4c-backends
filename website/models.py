from django.db import models

# Create your models here.

class Faq(models.Model):
    question = models.CharField(max_length=250)
    answer = models.TextField()


# class TermsAndConditions(models.Model):
#     tag = 
#     content = 