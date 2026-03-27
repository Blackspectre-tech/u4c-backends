import os
import django

# 1. Set the environment variable to your project's settings
# Replace 'your_project_name' with the folder name containing your settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 2. Initialize Django
django.setup()



from django.db import connection
from projects.models import Project

# campaign_id is from your webhook log
campaign_id = 2 

with connection.cursor() as cursor:
    # Use raw SQL to bypass Django's Decimal converter
    cursor.execute(f"SELECT * FROM projects_project WHERE contract_id = %s", [campaign_id])
    row = cursor.fetchone()
    columns = [col[0] for col in cursor.description]
    data = dict(zip(columns, row))

for field, value in data.items():
    print(f"{field}: {value}")
