from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0042_rename_tsiappa_dietitian"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NasogastricTubePlan",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[
                    ("not_placed", "Δεν έχει τοποθετηθεί / δεν έχει δηλωθεί"),
                    ("hospital", "Σε χρήση στο νοσοκομείο"),
                    ("home", "Σε χρήση στο σπίτι"),
                    ("removed", "Έχει αφαιρεθεί"),
                ], default="not_placed", max_length=20, verbose_name="Κατάσταση")),
                ("nostril", models.CharField(blank=True, choices=[
                    ("", "Δεν ορίστηκε"), ("left", "Αριστερό"), ("right", "Δεξί"),
                ], max_length=8, verbose_name="Ρουθούνι")),
                ("tube_size", models.CharField(blank=True, max_length=120, verbose_name="Μέγεθος / τύπος σωλήνα")),
                ("external_mark_cm", models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, verbose_name="Σημάδι στο ρουθούνι (cm)")),
                ("placed_on", models.DateField(blank=True, null=True, verbose_name="Ημερομηνία τοποθέτησης")),
                ("next_review_on", models.DateField(blank=True, null=True, verbose_name="Επανέλεγχος / αλλαγή κατά ιατρική οδηγία")),
                ("trained_carers", models.TextField(blank=True, verbose_name="Εκπαιδευμένοι φροντιστές")),
                ("checking_instructions", models.TextField(blank=True, verbose_name="Γραπτές οδηγίες επιβεβαίωσης θέσης")),
                ("tube_feed_instructions", models.TextField(blank=True, verbose_name="Εγκεκριμένο πλάνο σίτισης μέσω σωλήνα")),
                ("flush_instructions", models.TextField(blank=True, verbose_name="Εγκεκριμένες οδηγίες έκπλυσης / υγρών")),
                ("medication_instructions", models.TextField(blank=True, verbose_name="Εγκεκριμένα φάρμακα μέσω σωλήνα")),
                ("backup_plan", models.TextField(blank=True, verbose_name="Σχέδιο διακοπής σίτισης / βλάβης / υπογλυκαιμίας")),
                ("contact_instructions", models.TextField(blank=True, verbose_name="24ωρα τηλέφωνα και πότε καλούμε")),
                ("order_source", models.CharField(blank=True, max_length=250, verbose_name="Πηγή / ημερομηνία ιατρικής οδηγίας")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("child", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="nasogastric_plan", to="core.childprofile")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Πλάνο ρινογαστρικού σωλήνα"},
        ),
        migrations.CreateModel(
            name="NasogastricTubeEvent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Ημερομηνία και ώρα")),
                ("event_type", models.CharField(choices=[
                    ("position", "Έλεγχος θέσης"),
                    ("feed", "Σίτιση μέσω σωλήνα"),
                    ("medication", "Φάρμακο / έκπλυση"),
                    ("incident", "Πρόβλημα / μετατόπιση / απόφραξη"),
                    ("replacement", "Τοποθέτηση / αντικατάσταση από εκπαιδευμένο άτομο"),
                    ("training", "Εκπαίδευση φροντιστή"),
                    ("other", "Άλλο"),
                ], max_length=20, verbose_name="Είδος συμβάντος")),
                ("position_status", models.CharField(choices=[
                    ("not_checked", "Δεν ελέγχθηκε / δεν αφορά"),
                    ("confirmed", "Επιβεβαιώθηκε από εκπαιδευμένο άτομο κατά το πρωτόκολλο"),
                    ("uncertain", "Δεν επιβεβαιώθηκε / αμφίβολη θέση — μη χρήση"),
                ], default="not_checked", max_length=20, verbose_name="Έλεγχος θέσης")),
                ("gastric_ph", models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, verbose_name="pH αναρρόφησης")),
                ("external_mark_cm", models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, verbose_name="Σημάδι στο ρουθούνι (cm)")),
                ("volume_ml", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Ποσότητα (ml)")),
                ("notes", models.TextField(blank=True, verbose_name="Παρατηρήσεις / ενέργειες")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("child", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="nasogastric_events", to="core.childprofile")),
                ("recorded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-occurred_at", "-pk"], "verbose_name": "Καταγραφή ρινογαστρικού σωλήνα"},
        ),
    ]
