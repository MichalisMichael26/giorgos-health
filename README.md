# Giorgos Health

Private Django health-tracking application.

## Local setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000/

## Important

Do not store passwords, medical records, API keys, or other private data in GitHub.
Use environment variables for production secrets.
