import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prompt_builder.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')
        print("Admin user 'admin' (password: admin1234) created successfully!")
    else:
        print("Admin user already exists.")

if __name__ == '__main__':
    create_admin()
