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

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
from core.models import UserAccessProfile

User = get_user_model()

username = os.environ.get('DJANGO_DOCTOR_USERNAME', 'drsavvas')
password = os.environ.get('DJANGO_DOCTOR_PASSWORD')
display_name = os.environ.get('DJANGO_DOCTOR_DISPLAY_NAME', 'Δρ Σάββας Σάββα')

doctor = User.objects.filter(username=username).first()

if doctor is None and password:
    doctor = User.objects.create_user(username=username, password=password)

if doctor:
    doctor.is_staff = False
    doctor.is_superuser = False
    doctor.is_active = True

    if password:
        doctor.set_password(password)

    doctor.save()

    UserAccessProfile.objects.update_or_create(
        user=doctor,
        defaults={
            'role': 'doctor_readonly',
            'display_name': display_name,
        },
    )

    print('Doctor account enforced as read-only')
else:
    print('Doctor account does not exist and DJANGO_DOCTOR_PASSWORD is not set')
"

