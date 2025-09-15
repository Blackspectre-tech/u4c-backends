from django.core.management.base import BaseCommand
from website.models import Faq


class Command(BaseCommand):
    help = 'Load FAQs into the database'

    def handle(self, *args, **kwargs):
        faqs = [
            {
                "question": "What is United4Change (U4C)?",
                "answer": "U4C is a global giving platform connecting donors to grassroots-led, verified projects. Powered by BlackSpectre’s blockchain technology, U4C ensures that giving is secure, transparent, and borderless. U4C drives the social mission; BlackSpectre provides the engine.",
                "category": "Discover United4Change",
            },            
            {
                "question": "Why is giving through U4C different?",
                "answer": "Unlike traditional platforms, U4C uses smart contracts to tie donations to verified goals. Funds are held in smart vaults and only released when goals are met and you can track everything in real-time.",
                "category": "Discover United4Change.",
            },
            {
                "question": "Who is behind U4C?",
                "answer": "U4C is built and powered by BlackSpectre, a commercial tech provider specializing in blockchain infrastructure. Operating independently through a decentralized network, U4C partners with trusted NGOs and local groups to make giving more transparent and impactful.",
                "category": "Discover United4Change.",
            },
            {
                "question": "Where is U4C available?",
                "answer": "Everywhere. U4C is global, we support local currencies and digital cash. You can give or receive support from anywhere with confidence.",
                "category": "Discover United4Change.",
            },
            {
                "question": "How do I donate?",
                "answer": "Choose a campaign, enter your amount, and pay with your card, local currency, or digital cash like USDC/USDT. You can also leave an optional tip that goes directly into the U4C Treasury — a fund dedicated entirely to social impact and community empowerment. Supporters may also contribute to the Foundation directly through the Treasury without opening a campaign.",
                "category": "Global Giving Made Easy",
            },
            {
                "question": "Will I get a receipt?",
                "answer": "Yes. The receipts from your chosen project will be instantly available on your Donor Dashboard, along with your full donation history.",
                "category": "Global Giving Made Easy",
            },
            {
                "question": "Are donations tax-deductible?",
                "answer": "We're working on enabling tax-deduction options in more countries. Please check with your local tax advisor for country-specific details.",
                "category": "Global Giving Made Easy",
            },
            {
                "question": "How is my donation used?",
                "answer": "Your donation goes directly to the campaign you choose. Funds are released only when progress goals are verified by U4C admin (DAO). You’ll be able to track progress from your dashboard.",
                "category": "Global Giving Made Easy",
            },
            {
                "question": "How do I report a problem?",
                "answer": "Use the “Report” button on any campaign page or email us at support@united-4-change.org.",
                "category": "Global Giving Made Easy",
            },
            {
                "question": "Who can start a campaign on U4C?",
                "answer": "NGOs, and local organizations can create campaigns on U4C.",
                "category": "Starting A Campaign",            
            },
            {
                "question": "What’s the process like?",
                "answer": "The process is fully automated. Apply through our website and complete onboarding which includes document checks, ID verification, and KYC review, and your campaign will go live.",
                "category": "Starting A Campaign",            
            },
            {
                "question": "What documents are needed?",
                "answer": "We’ll request legal registration, proof of activity, ID, and any impact materials like photos, reports, or videos.",
                "category": "Starting A Campaign",            
            },
            {
                "question": "When do campaign creators receive funds?",
                "answer": "Funding is released in stages, as each campaign goal is achieved and verified by the U4C team. Creators can then withdraw to their bank account or crypto wallet.",
                "category": "Starting A Campaign",            
            },
            {
                "question": "What are smart contracts?",
                "answer": "They’re automated agreements coded to hold donations and release them only after a campaign goal is achieved and verified. No middlemen, just smart giving.",
                "category": "The Tech That Powers U4C",            
            },
            {
                "question": "What’s the U4C Treasury?",
                "answer": "Its a community-managed fund dedicated entirely to social impact and empowerment. It is funded only by optional donor tips and direct contributions — never from platform fees. The Treasury supports: Validator Compensation, Emergency Responses, Outreach & Engagement, Research & Innovation, DAO Experiments. Designed as a DAO (Decentralized Autonomous Organization), the Treasury is 100% transparent, secured with a multi-signature wallet, and collectively governed by the community.",
                "category": "The Tech That Powers U4C",              
            },
        ]

        for faq in faqs:
            obj, created = Faq.objects.get_or_create(
                question=faq["question"],
                defaults={"answer": faq["answer"],"category": faq["category"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Added FAQ: {faq['question']}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ FAQ already exists: {faq['question']}"))

        self.stdout.write(self.style.SUCCESS("🎉 FAQ loading complete!"))
