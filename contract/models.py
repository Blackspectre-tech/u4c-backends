from django.db import models

# Create your models here.

class ContractLog(models.Model):
    data = models.TextField()
    error = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)