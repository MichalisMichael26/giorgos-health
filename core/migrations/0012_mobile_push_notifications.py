from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_seed_discharge_lab_results"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="healthreminder",
            name="notify_minutes_before",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="0 = στην ακριβή ώρα της υπενθύμισης.",
                verbose_name="Push ειδοποίηση (λεπτά πριν)",
            ),
        ),
        migrations.AddField(
            model_name="healthreminder",
            name="repeat_if_incomplete_minutes",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="0 = χωρίς δεύτερη ειδοποίηση.",
                verbose_name="Επανάληψη αν δεν ολοκληρωθεί (λεπτά μετά)",
            ),
        ),
        migrations.AddField(
            model_name="healthreminder",
            name="push_notified_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Πρώτη push ειδοποίηση"),
        ),
        migrations.AddField(
            model_name="healthreminder",
            name="push_repeat_notified_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Επαναληπτική push ειδοποίηση"),
        ),
        migrations.CreateModel(
            name="PushConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("private_key_pem", models.TextField(verbose_name="VAPID private key PEM")),
                ("public_key_b64", models.TextField(verbose_name="VAPID public key")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Push configuration",
                "verbose_name_plural": "Push configuration",
            },
        ),
        migrations.CreateModel(
            name="PushSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("endpoint", models.TextField(unique=True, verbose_name="Push endpoint")),
                ("p256dh", models.TextField(verbose_name="P256DH key")),
                ("auth", models.TextField(verbose_name="Auth key")),
                ("user_agent", models.TextField(blank=True, verbose_name="Συσκευή / browser")),
                ("active", models.BooleanField(default=True, verbose_name="Ενεργή")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="push_subscriptions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-last_seen_at"]},
        ),
        migrations.CreateModel(
            name="PushDeliveryLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("delivery_kind", models.CharField(choices=[("initial","Αρχική"),("repeat","Επανάληψη")], max_length=20, verbose_name="Τύπος αποστολής")),
                ("success", models.BooleanField(default=False, verbose_name="Επιτυχία")),
                ("status_code", models.IntegerField(blank=True, null=True, verbose_name="HTTP status")),
                ("error", models.TextField(blank=True, verbose_name="Σφάλμα")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reminder", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="push_delivery_logs", to="core.healthreminder")),
                ("subscription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delivery_logs", to="core.pushsubscription")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
