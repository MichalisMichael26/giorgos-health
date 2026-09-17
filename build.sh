#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if password:
    user, created = User.objects.get_or_create(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print('Admin user configured successfully')
else:
    print('DJANGO_SUPERUSER_PASSWORD is not set')
"
