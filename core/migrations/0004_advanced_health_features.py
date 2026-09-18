from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_childprofile"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="childprofile",
            name="full_name",
            field=models.CharField(default="Giorgos Panayiotis Michael", max_length=180, verbose_name="Πλήρες όνομα"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_instructions",
            field=models.TextField(blank=True, verbose_name="Βασικές ιατρικές οδηγίες"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="treating_doctors",
            field=models.TextField(blank=True, default="Δρ Σάββας Σάββα - Παιδίατρος\nΔρ Όλγα Γραφάκου - Κλινική ΝΑΜΙΙ", verbose_name="Θεράποντες ιατροί"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="emergency_contacts",
            field=models.TextField(blank=True, verbose_name="Τηλέφωνα επικοινωνίας"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="current_feeding_plan",
            field=models.TextField(blank=True, verbose_name="Τρέχον πλάνο σίτισης"),
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("action", models.CharField(choices=[("create", "Δημιουργία"), ("update", "Επεξεργασία"), ("delete", "Διαγραφή")], max_length=12)),
                ("model_name", models.CharField(max_length=120)),
                ("object_id", models.CharField(blank=True, max_length=80)),
                ("object_repr", models.CharField(blank=True, max_length=255)),
                ("changes", models.JSONField(blank=True, default=dict)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-timestamp"]},
        ),
        migrations.CreateModel(
            name="DiaperEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Ημερομηνία")),
                ("time", models.TimeField(verbose_name="Ώρα")),
                ("kind", models.CharField(choices=[("wet", "Βρεγμένη πάνα"), ("stool", "Κένωση"), ("both", "Ούρα + κένωση")], default="wet", max_length=20, verbose_name="Τύπος")),
                ("stool_color", models.CharField(blank=True, max_length=100, verbose_name="Χρώμα κένωσης")),
                ("stool_consistency", models.CharField(blank=True, max_length=120, verbose_name="Σύσταση")),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="diaper_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-date", "-time"]},
        ),
        migrations.CreateModel(
            name="MedicalDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Ημερομηνία εγγράφου")),
                ("category", models.CharField(choices=[("discharge", "Εξιτήριο"), ("lab", "Εργαστηριακές εξετάσεις"), ("opinion", "Γνωμάτευση"), ("prescription", "Συνταγή"), ("imaging", "Απεικονιστική εξέταση"), ("other", "Άλλο")], default="other", max_length=30, verbose_name="Κατηγορία")),
                ("title", models.CharField(max_length=220, verbose_name="Τίτλος")),
                ("original_filename", models.CharField(max_length=255, verbose_name="Όνομα αρχείου")),
                ("content_type", models.CharField(blank=True, max_length=120, verbose_name="Τύπος αρχείου")),
                ("file_size", models.PositiveIntegerField(default=0, verbose_name="Μέγεθος αρχείου")),
                ("data", models.BinaryField(editable=False)),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="medical_documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="SymptomEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Ημερομηνία")),
                ("time", models.TimeField(verbose_name="Ώρα")),
                ("symptom", models.CharField(max_length=180, verbose_name="Σύμπτωμα / επεισόδιο")),
                ("severity", models.CharField(choices=[("mild", "Ήπιο"), ("moderate", "Μέτριο"), ("severe", "Έντονο")], default="mild", max_length=20, verbose_name="Ένταση")),
                ("duration_minutes", models.PositiveIntegerField(blank=True, null=True, verbose_name="Διάρκεια (λεπτά)")),
                ("relation_to_feed", models.CharField(choices=[("before_feed", "Πριν το γεύμα"), ("during_feed", "Κατά το γεύμα"), ("after_feed", "Μετά το γεύμα"), ("unrelated", "Δεν σχετίζεται"), ("unknown", "Άγνωστο")], default="unknown", max_length=20, verbose_name="Σχέση με γεύμα")),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="symptom_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-date", "-time"]},
        ),
        migrations.CreateModel(
            name="VaccineEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Ημερομηνία εμβολιασμού")),
                ("name", models.CharField(max_length=180, verbose_name="Εμβόλιο")),
                ("dose_label", models.CharField(blank=True, max_length=100, verbose_name="Δόση")),
                ("next_date", models.DateField(blank=True, null=True, verbose_name="Επόμενη δόση")),
                ("reminder_days_before", models.PositiveSmallIntegerField(default=7, verbose_name="Υπενθύμιση (ημέρες πριν)")),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vaccine_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-date", "name"]},
        ),
    ]
