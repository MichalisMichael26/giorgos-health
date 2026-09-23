from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_daily_medication_reminders"),
    ]

    operations = [
        migrations.AddField(
            model_name="useraccessprofile",
            name="last_seen_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Τελευταία δραστηριότητα",
            ),
        ),
        migrations.AddField(
            model_name="useraccessprofile",
            name="last_seen_path",
            field=models.CharField(
                blank=True,
                max_length=240,
                verbose_name="Τελευταία σελίδα",
            ),
        ),
        migrations.AddField(
            model_name="useraccessprofile",
            name="last_seen_user_agent",
            field=models.CharField(
                blank=True,
                max_length=500,
                verbose_name="Τελευταία συσκευή / browser",
            ),
        ),
        migrations.CreateModel(
            name="UserAccessLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("login_at", models.DateTimeField(verbose_name="Είσοδος")),
                (
                    "last_seen_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Τελευταία δραστηριότητα",
                    ),
                ),
                (
                    "logout_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Έξοδος",
                    ),
                ),
                (
                    "entry_source",
                    models.CharField(
                        choices=[
                            ("login", "Κανονικό login"),
                            ("existing_session", "Ήδη ενεργή συνεδρία"),
                        ],
                        default="login",
                        max_length=30,
                        verbose_name="Τρόπος εισόδου",
                    ),
                ),
                (
                    "user_agent",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="Συσκευή / browser",
                    ),
                ),
                (
                    "first_path",
                    models.CharField(
                        blank=True,
                        max_length=240,
                        verbose_name="Πρώτη σελίδα",
                    ),
                ),
                (
                    "last_path",
                    models.CharField(
                        blank=True,
                        max_length=240,
                        verbose_name="Τελευταία σελίδα",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="giorgos_access_logs",
                        to="auth.user",
                    ),
                ),
            ],
            options={
                "ordering": ["-login_at"],
            },
        ),
        migrations.AddIndex(
            model_name="useraccesslog",
            index=models.Index(
                fields=["user", "-login_at"],
                name="gh_access_user_login",
            ),
        ),
        migrations.AddIndex(
            model_name="useraccesslog",
            index=models.Index(
                fields=["-last_seen_at"],
                name="gh_access_last_seen",
            ),
        ),
    ]
