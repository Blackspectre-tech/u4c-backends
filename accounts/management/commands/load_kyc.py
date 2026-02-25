from django.core.management.base import BaseCommand
from accounts.models import KycRequirement

class Command(BaseCommand):
    help = 'Load fixed kyc requirements into the database'

    def handle(self, *args, **kwargs):
        requirements = [
            {
                "name": "cac document",
                "field_type": "document",
            },  
            {
                "name": "representative idcard",
                "field_type": "document",
            },
            {
                "name": "representative phone number",
                "field_type": "phone number",
                "is_required": False,
            },
            {
                "name": "registeration number",
                "field_type": "text",
            },
        ]



        for item in requirements:
            obj, created = KycRequirement.objects.get_or_create(
                name=item["name"],
                defaults={"field_type": item["field_type"],}
            )
            if item['name'] == 'representative phone number':
                obj.is_required = False
                obj.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Added kyc requirement: {item['name']}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ kyc requirement already exists: {item['name']}"))

        self.stdout.write(self.style.SUCCESS("kyc requirements loading complete!"))




        