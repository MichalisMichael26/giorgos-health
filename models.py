from django.db import models
from django.contrib.auth.models import User


class MealEntry(models.Model):
    MEAL_STATUS = [
        ("completed", "Ολοκληρώθηκε"),
        ("partial", "Μερικό"),
        ("missed", "Δεν καταχωρήθηκε"),
    ]

    date = models.DateField("Ημερομηνία")
    scheduled_time = models.TimeField("Προγραμματισμένη ώρα")
    actual_time = models.TimeField("Πραγματική ώρα", blank=True, null=True)
    offered_ml = models.PositiveIntegerField("Προσφέρθηκαν (ml)", blank=True, null=True)
    consumed_ml = models.PositiveIntegerField("Ήπιε (ml)", blank=True, null=True)
    formula = models.CharField("Formula", max_length=120, blank=True)
    supplement = models.CharField("Συμπλήρωμα", max_length=120, blank=True)
    status = models.CharField(
        "Κατάσταση",
        max_length=20,
        choices=MEAL_STATUS,
        default="completed",
    )
    notes = models.TextField("Σημειώσεις", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meal_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-scheduled_time"]

    def __str__(self):
        return f"{self.date} {self.scheduled_time} - {self.consumed_ml or 0} ml"


class GlucoseReading(models.Model):
    CONTEXT_CHOICES = [
        ("pre_feed", "Πριν το γεύμα"),
        ("post_feed", "Μετά το γεύμα"),
        ("other", "Άλλο"),
    ]

    date = models.DateField("Ημερομηνία")
    time = models.TimeField("Ώρα")
    value = models.DecimalField("Γλυκόζη (mg/dL)", max_digits=6, decimal_places=1)
    context = models.CharField(
        "Σχέση με γεύμα",
        max_length=20,
        choices=CONTEXT_CHOICES,
        default="pre_feed",
    )
    related_meal = models.ForeignKey(
        MealEntry,
        verbose_name="Σχετικό γεύμα",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="glucose_readings",
    )
    notes = models.TextField("Σημειώσεις", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="glucose_readings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.date} {self.time} - {self.value} mg/dL"


class GrowthMeasurement(models.Model):
    date = models.DateField("Ημερομηνία")
    weight_kg = models.DecimalField("Βάρος (kg)", max_digits=5, decimal_places=3, blank=True, null=True)
    length_cm = models.DecimalField("Ύψος/Μήκος (cm)", max_digits=5, decimal_places=2, blank=True, null=True)
    head_cm = models.DecimalField("Περίμετρος κεφαλής (cm)", max_digits=5, decimal_places=2, blank=True, null=True)
    notes = models.TextField("Σημειώσεις", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return str(self.date)
