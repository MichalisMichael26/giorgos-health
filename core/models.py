from django.contrib.auth.models import User
from django.db import models

GREEK_WEEKDAYS = [
    "Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη",
    "Παρασκευή", "Σάββατο", "Κυριακή",
]


def greek_weekday(value):
    return GREEK_WEEKDAYS[value.weekday()] if value else ""


class MealEntry(models.Model):
    STATUS_CHOICES = [
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
        choices=STATUS_CHOICES,
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

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return f"{self.date} {self.scheduled_time.strftime('%H:%M')}"


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

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return f"{self.date} {self.time.strftime('%H:%M')} - {self.value} mg/dL"


class GrowthMeasurement(models.Model):
    date = models.DateField("Ημερομηνία")
    weight_kg = models.DecimalField(
        "Βάρος (kg)", max_digits=6, decimal_places=3, blank=True, null=True
    )
    length_cm = models.DecimalField(
        "Μήκος (cm)", max_digits=6, decimal_places=2, blank=True, null=True
    )
    head_cm = models.DecimalField(
        "Περίμετρος κεφαλής (cm)", max_digits=6, decimal_places=2, blank=True, null=True
    )
    notes = models.TextField("Σημειώσεις", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return str(self.date)


class MedicationEntry(models.Model):
    UNIT_CHOICES = [
        ("ml", "ml"),
        ("mg", "mg"),
        ("g", "g"),
        ("drops", "Σταγόνες"),
        ("scoops", "Κουταλάκια"),
        ("dose", "Δόση"),
        ("other", "Άλλο"),
    ]

    date = models.DateField("Ημερομηνία")
    time = models.TimeField("Ώρα")
    name = models.CharField("Φάρμακο / συμπλήρωμα", max_length=160)
    dose = models.DecimalField("Ποσότητα", max_digits=8, decimal_places=2)
    unit = models.CharField("Μονάδα", max_length=20, choices=UNIT_CHOICES, default="ml")
    notes = models.TextField("Σημειώσεις", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medication_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return f"{self.date} {self.time.strftime('%H:%M')} - {self.name}"


class MedicalAppointment(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Προγραμματισμένο"),
        ("completed", "Ολοκληρώθηκε"),
        ("cancelled", "Ακυρώθηκε"),
    ]

    date = models.DateField("Ημερομηνία")
    time = models.TimeField("Ώρα")
    doctor = models.CharField("Ιατρός", max_length=160, blank=True)
    clinic = models.CharField("Κλινική / νοσοκομείο", max_length=180, blank=True)
    purpose = models.CharField("Λόγος / επανέλεγχος", max_length=220)
    reminder_days_before = models.PositiveSmallIntegerField(
        "Υπενθύμιση (ημέρες πριν)",
        default=1,
    )
    status = models.CharField(
        "Κατάσταση",
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
    )
    notes = models.TextField("Σημειώσεις", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "time"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return f"{self.date} {self.time.strftime('%H:%M')} - {self.purpose}"
