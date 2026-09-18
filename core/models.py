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



class ChildProfile(models.Model):
    name = models.CharField("Όνομα παιδιού", max_length=100, default="Γιώργος")
    full_name = models.CharField("Πλήρες όνομα", max_length=180, default="Giorgos Panayiotis Michael")
    birth_date = models.DateField("Ημερομηνία γέννησης")
    clinician_target_min_ml = models.PositiveIntegerField(
        "Στόχος ιατρού — ελάχιστο ml/24ωρο", blank=True, null=True
    )
    clinician_target_max_ml = models.PositiveIntegerField(
        "Στόχος ιατρού — μέγιστο ml/24ωρο", blank=True, null=True
    )
    clinician_target_note = models.CharField(
        "Σημείωση στόχου",
        max_length=220,
        blank=True,
        help_text="Π.χ. οδηγία παιδιάτρου / διαιτολόγου και ημερομηνία.",
    )
    emergency_instructions = models.TextField("Βασικές ιατρικές οδηγίες", blank=True)
    treating_doctors = models.TextField(
        "Θεράποντες ιατροί",
        blank=True,
        default="Δρ Σάββας Σάββα - Παιδίατρος\nΔρ Όλγα Γραφάκου - Κλινική ΝΑΜΙΙ",
    )
    emergency_contacts = models.TextField("Τηλέφωνα επικοινωνίας", blank=True)
    current_feeding_plan = models.TextField("Τρέχον πλάνο σίτισης", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Προφίλ παιδιού"
        verbose_name_plural = "Προφίλ παιδιού"

    def __str__(self):
        return self.name



class MedicalDocument(models.Model):
    CATEGORY_CHOICES = [
        ("discharge", "Εξιτήριο"),
        ("lab", "Εργαστηριακές εξετάσεις"),
        ("opinion", "Γνωμάτευση"),
        ("prescription", "Συνταγή"),
        ("imaging", "Απεικονιστική εξέταση"),
        ("other", "Άλλο"),
    ]

    date = models.DateField("Ημερομηνία εγγράφου")
    category = models.CharField("Κατηγορία", max_length=30, choices=CATEGORY_CHOICES, default="other")
    title = models.CharField("Τίτλος", max_length=220)
    original_filename = models.CharField("Όνομα αρχείου", max_length=255)
    content_type = models.CharField("Τύπος αρχείου", max_length=120, blank=True)
    file_size = models.PositiveIntegerField("Μέγεθος αρχείου", default=0)
    data = models.BinaryField(editable=False)
    notes = models.TextField("Σημειώσεις", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return self.title


class VaccineEntry(models.Model):
    date = models.DateField("Ημερομηνία εμβολιασμού")
    name = models.CharField("Εμβόλιο", max_length=180)
    dose_label = models.CharField("Δόση", max_length=100, blank=True)
    next_date = models.DateField("Επόμενη δόση", blank=True, null=True)
    reminder_days_before = models.PositiveSmallIntegerField("Υπενθύμιση (ημέρες πριν)", default=7)
    notes = models.TextField("Σημειώσεις", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vaccine_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "name"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return f"{self.name} - {self.date}"


class SymptomEntry(models.Model):
    SEVERITY_CHOICES = [
        ("mild", "Ήπιο"),
        ("moderate", "Μέτριο"),
        ("severe", "Έντονο"),
    ]
    RELATION_CHOICES = [
        ("before_feed", "Πριν το γεύμα"),
        ("during_feed", "Κατά το γεύμα"),
        ("after_feed", "Μετά το γεύμα"),
        ("unrelated", "Δεν σχετίζεται"),
        ("unknown", "Άγνωστο"),
    ]

    date = models.DateField("Ημερομηνία")
    time = models.TimeField("Ώρα")
    symptom = models.CharField("Σύμπτωμα / επεισόδιο", max_length=180)
    severity = models.CharField("Ένταση", max_length=20, choices=SEVERITY_CHOICES, default="mild")
    duration_minutes = models.PositiveIntegerField("Διάρκεια (λεπτά)", blank=True, null=True)
    relation_to_feed = models.CharField("Σχέση με γεύμα", max_length=20, choices=RELATION_CHOICES, default="unknown")
    notes = models.TextField("Σημειώσεις", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="symptom_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return f"{self.date} {self.time} - {self.symptom}"


class DiaperEntry(models.Model):
    KIND_CHOICES = [
        ("wet", "Βρεγμένη πάνα"),
        ("stool", "Κένωση"),
        ("both", "Ούρα + κένωση"),
    ]

    date = models.DateField("Ημερομηνία")
    time = models.TimeField("Ώρα")
    kind = models.CharField("Τύπος", max_length=20, choices=KIND_CHOICES, default="wet")
    stool_color = models.CharField("Χρώμα κένωσης", max_length=100, blank=True)
    stool_consistency = models.CharField("Σύσταση", max_length=120, blank=True)
    notes = models.TextField("Σημειώσεις", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diaper_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        return f"{self.date} {self.time} - {self.get_kind_display()}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Δημιουργία"),
        ("update", "Επεξεργασία"),
        ("delete", "Διαγραφή"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    action = models.CharField(max_length=12, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=120)
    object_id = models.CharField(max_length=80, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.model_name} - {self.timestamp}"
