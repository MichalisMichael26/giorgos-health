from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_advanced_health_features"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SafetyRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", models.CharField(max_length=160, verbose_name="Συστατικό / όρος")),
                ("applies_to", models.CharField(
                    choices=[("food", "Τρόφιμα"), ("medicine", "Φάρμακα"), ("both", "Τρόφιμα και φάρμακα")],
                    default="both",
                    max_length=20,
                    verbose_name="Ισχύει για",
                )),
                ("guidance", models.CharField(
                    choices=[("avoid", "Να αποφεύγεται"), ("caution", "Χρειάζεται έλεγχος")],
                    default="caution",
                    max_length=20,
                    verbose_name="Οδηγία",
                )),
                ("note", models.CharField(
                    blank=True,
                    help_text="Π.χ. οδηγία παιδιάτρου, μεταβολικής ομάδας ή φαρμακοποιού.",
                    max_length=255,
                    verbose_name="Σημείωση / πηγή οδηγίας",
                )),
                ("active", models.BooleanField(default=True, verbose_name="Ενεργό")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["term"]},
        ),
        migrations.CreateModel(
            name="ProductSafetyRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(
                    choices=[("food", "Τρόφιμο / ρόφημα"), ("medicine", "Φάρμακο / σκεύασμα")],
                    max_length=20,
                    verbose_name="Τύπος",
                )),
                ("name", models.CharField(max_length=220, verbose_name="Ονομασία προϊόντος / φαρμάκου")),
                ("decision", models.CharField(
                    choices=[
                        ("confirmed", "Επιβεβαιωμένο από ιατρό / φαρμακοποιό"),
                        ("avoid", "Να αποφεύγεται"),
                        ("caution", "Χρειάζεται έλεγχος"),
                    ],
                    max_length=20,
                    verbose_name="Καταχωρημένη αξιολόγηση",
                )),
                ("ingredients", models.TextField(
                    blank=True,
                    help_text="Προαιρετικά: αντιγραφή από ετικέτα ή φύλλο οδηγιών.",
                    verbose_name="Συστατικά / έκδοχα",
                )),
                ("confirmed_by", models.CharField(
                    blank=True,
                    help_text="Για επιβεβαιωμένο προϊόν γράψε ιατρό ή φαρμακοποιό.",
                    max_length=180,
                    verbose_name="Επιβεβαιώθηκε από",
                )),
                ("reviewed_on", models.DateField(blank=True, null=True, verbose_name="Ημερομηνία ελέγχου")),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="product_safety_records",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering": ["kind", "name"]},
        ),
    ]
