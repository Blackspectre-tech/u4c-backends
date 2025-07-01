from django.core.management.base import BaseCommand
from projects.models import Category

class Command(BaseCommand):
    help = 'Load fixed categories into the database'

    def handle(self, *args, **kwargs):
        categories = [
            'Clean Water', 'Education', 'Healthcare', 
            'Childcare', 'Climate Change', 'Disaster Recovery', 'Hunger'
        ]

 


        for name in categories:
            Category.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS('Categories loaded successfully!'))
