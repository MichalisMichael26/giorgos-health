import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_lock_birth_date_and_appointment_order"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="childprofile",
            name="emergency_share_enabled",
            field=models.BooleanField(default=False, verbose_name="Emergency QR ενεργό"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_share_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Emergency share token"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_share_show_identity",
            field=models.BooleanField(default=True, verbose_name="QR: όνομα & DOB"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_share_show_instructions",
            field=models.BooleanField(default=True, verbose_name="QR: βασικές ιατρικές οδηγίες"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_share_show_feeding",
            field=models.BooleanField(default=True, verbose_name="QR: πλάνο σίτισης"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_share_show_doctors",
            field=models.BooleanField(default=True, verbose_name="QR: θεράποντες ιατροί"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_share_show_phones",
            field=models.BooleanField(default=True, verbose_name="QR: τηλέφωνα"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_share_show_glucose",
            field=models.BooleanField(default=False, verbose_name="QR: τελευταία γλυκόζη"),
        ),
        migrations.AddField(
            model_name="productsafetyrecord",
            name="barcode",
            field=models.CharField(blank=True, db_index=True, max_length=64, verbose_name="Barcode"),
        ),
        migrations.AddField(
            model_name="productsafetyrecord",
            name="label_photo_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Όνομα φωτογραφίας ετικέτας"),
        ),
        migrations.AddField(
            model_name="productsafetyrecord",
            name="label_photo_mime",
            field=models.CharField(blank=True, max_length=120, verbose_name="Τύπος φωτογραφίας ετικέτας"),
        ),
        migrations.AddField(
            model_name="productsafetyrecord",
            name="label_photo_data",
            field=models.BinaryField(blank=True, editable=False, null=True, verbose_name="Φωτογραφία ετικέτας"),
        ),
        migrations.AlterField(
            model_name="productsafetyrecord",
            name="decision",
            field=models.CharField(
                choices=[
                    ("confirmed", "Επιβεβαιωμένο από ιατρό / φαρμακοποιό"),
                    ("checked", "Ελέγχθηκε — δεν εντοπίστηκε περιορισμός"),
                    ("avoid", "Να αποφεύγεται"),
                    ("caution", "Χρειάζεται έλεγχος"),
                ],
                max_length=20,
                verbose_name="Καταχωρημένη αξιολόγηση",
            ),
        ),
        migrations.AddField(
            model_name="symptomentry",
            name="photo_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Όνομα φωτογραφίας"),
        ),
        migrations.AddField(
            model_name="symptomentry",
            name="photo_mime",
            field=models.CharField(blank=True, max_length=120, verbose_name="Τύπος φωτογραφίας"),
        ),
        migrations.AddField(
            model_name="symptomentry",
            name="photo_data",
            field=models.BinaryField(blank=True, editable=False, null=True, verbose_name="Φωτογραφία"),
        ),
        migrations.AddField(
            model_name="diaperentry",
            name="photo_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Όνομα φωτογραφίας"),
        ),
        migrations.AddField(
            model_name="diaperentry",
            name="photo_mime",
            field=models.CharField(blank=True, max_length=120, verbose_name="Τύπος φωτογραφίας"),
        ),
        migrations.AddField(
            model_name="diaperentry",
            name="photo_data",
            field=models.BinaryField(blank=True, editable=False, null=True, verbose_name="Φωτογραφία"),
        ),
        migrations.CreateModel(
            name="LabResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Ημερομηνία εξέτασης")),
                ("time", models.TimeField(blank=True, null=True, verbose_name="Ώρα")),
                ("test_name", models.CharField(db_index=True, max_length=160, verbose_name="Εξέταση")),
                ("value", models.DecimalField(decimal_places=4, max_digits=12, verbose_name="Τιμή")),
                ("unit", models.CharField(blank=True, max_length=80, verbose_name="Μονάδα")),
                ("reference_min", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True, verbose_name="Κατώτερο όριο αναφοράς")),
                ("reference_max", models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True, verbose_name="Ανώτερο όριο αναφοράς")),
                ("laboratory", models.CharField(blank=True, max_length=180, verbose_name="Εργαστήριο")),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="lab_results", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-date", "-time", "test_name"]},
        ),
        migrations.CreateModel(
            name="HealthReminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reminder_type", models.CharField(choices=[("meal","Γεύμα"),("medication","Φάρμακο"),("vaccine","Εμβόλιο"),("measurement","Μέτρηση"),("lab","Εξέταση"),("other","Άλλο")], default="other", max_length=20, verbose_name="Τύπος")),
                ("title", models.CharField(max_length=180, verbose_name="Τίτλος")),
                ("due_at", models.DateTimeField(verbose_name="Ημερομηνία / ώρα")),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("active", models.BooleanField(default=True, verbose_name="Ενεργό")),
                ("completed", models.BooleanField(default=False, verbose_name="Ολοκληρώθηκε")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="health_reminders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["completed", "due_at"]},
        ),
        migrations.CreateModel(
            name="DoctorQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField(verbose_name="Ερώτηση για τον γιατρό")),
                ("status", models.CharField(choices=[("pending","Εκκρεμεί"),("answered","Απαντήθηκε")], default="pending", max_length=20, verbose_name="Κατάσταση")),
                ("answer", models.TextField(blank=True, verbose_name="Απάντηση / σημείωση")),
                ("answered_at", models.DateTimeField(blank=True, null=True, verbose_name="Απαντήθηκε στις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="doctor_questions", to="core.medicalappointment", verbose_name="Σχετικό ραντεβού")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="doctor_questions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["status", "-created_at"]},
        ),
        migrations.CreateModel(
            name="UserAccessProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("parent","Γονέας / πλήρης πρόσβαση"),("doctor_readonly","Ιατρός / μόνο προβολή")], default="parent", max_length=30, verbose_name="Ρόλος")),
                ("display_name", models.CharField(blank=True, max_length=120, verbose_name="Εμφανιζόμενο όνομα")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="access_profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="BackupRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(choices=[("success","Επιτυχία"),("failed","Αποτυχία")], max_length=20, verbose_name="Κατάσταση")),
                ("destination", models.CharField(blank=True, max_length=220, verbose_name="Προορισμός")),
                ("size_bytes", models.PositiveBigIntegerField(default=0, verbose_name="Μέγεθος")),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
