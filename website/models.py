from django.db import models

# Create your models here.

class Faq(models.Model):
    question = models.CharField(max_length=250)
    answer = models.TextField()
    category = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.question


class ErrorLog(models.Model):
    data = models.TextField()
    error = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.error
    
    class Meta:
        ordering = ['-time']
