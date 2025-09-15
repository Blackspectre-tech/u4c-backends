from django.db import models

# Create your models here.

class Faq(models.Model):
    question = models.CharField(max_length=250)
    answer = models.TextField()
    category = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.question


# class TermsAndConditions(models.Model):
#     tag = 
#     content = 