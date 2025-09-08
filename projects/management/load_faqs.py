# from django.core.management.base import BaseCommand
# from website.models import Faq


# class Command(BaseCommand):
#     help = 'Load FAQs into the database'

#     def handle(self, *args, **kwargs):
#         faqs = [
#             {
#                 "question": "What is United 4 Change?",
#                 "answer": "United 4 Change is a platform that connects donors with verified non-profit organizations to support impactful projects."
#             },
#             {
#                 "question": "How do I donate to a project?",
#                 "answer": "You can browse projects, choose one you want to support, and complete your donation securely via our payment gateway."
#             },
#             {
#                 "question": "Is my donation tax-deductible?",
#                 "answer": "Yes, depending on your country’s tax laws. We provide receipts that you can use for your records."
#             },
#             {
#                 "question": "Can I volunteer instead of donating?",
#                 "answer": "Some organizations accept volunteers. You can contact the project manager directly through our platform."
#             },
#             {
#                 "question": "How do I create an organization account?",
#                 "answer": "Register as an organization, upload your registration documents, and wait for verification before posting projects."
#             },
#         ]

#         for faq in faqs:
#             obj, created = Faq.objects.get_or_create(
#                 question=faq["question"],
#                 defaults={"answer": faq["answer"]}
#             )
#             if created:
#                 self.stdout.write(self.style.SUCCESS(f"✅ Added FAQ: {faq['question']}"))
#             else:
#                 self.stdout.write(self.style.WARNING(f"⚠️ FAQ already exists: {faq['question']}"))

#         self.stdout.write(self.style.SUCCESS("🎉 FAQ loading complete!"))
