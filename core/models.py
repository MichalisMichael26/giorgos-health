from datetime import date
import uuid
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
    actual_time = models.TimeField("Ώρα έναρξης", blank=True, null=True)
    finished_time = models.TimeField("Ώρα ολοκλήρωσης", blank=True, null=True)
    offered_ml = models.PositiveIntegerField("Προσφέρθηκαν (ml)", blank=True, null=True)
    consumed_ml = models.PositiveIntegerField("Ήπιε (ml)", blank=True, null=True)
    remaining_ml = models.PositiveIntegerField("Έμεινε (ml)", blank=True, null=True)
    formula = models.CharField("Formula", max_length=120, blank=True)
    supplement = models.CharField("Maxijul (scoops)", max_length=120, blank=True)
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
    measured_by = models.CharField("Μετρήθηκε από", max_length=180, blank=True)
    notes = models.TextField("Σημειώσεις", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    @property
    def bmi(self):
        if self.weight_kg is None or self.length_cm in (None, 0):
            return None
        meters = float(self.length_cm) / 100
        if not meters:
            return None
        return round(float(self.weight_kg) / (meters * meters), 1)

    @property
    def age_week_number(self):
        birth_date = date(2026, 6, 27)
        if not self.date or self.date < birth_date:
            return None
        return ((self.date - birth_date).days // 7) + 1

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


class MedicationPlan(models.Model):
    UNIT_CHOICES = MedicationEntry.UNIT_CHOICES

    name = models.CharField("Φάρμακο / συμπλήρωμα", max_length=160)
    dose = models.DecimalField("Ποσότητα", max_digits=8, decimal_places=2)
    unit = models.CharField("Μονάδα", max_length=20, choices=UNIT_CHOICES, default="ml")
    frequency = models.CharField("Συχνότητα", max_length=120, default="1 φορά/ημέρα")
    notes = models.TextField("Σημειώσεις", blank=True)
    unit_confirmation_required = models.BooleanField(
        "Χρειάζεται επιβεβαίωση μονάδας",
        default=False,
    )
    reminder_enabled = models.BooleanField("Καθημερινή υπενθύμιση", default=False)
    reminder_time = models.TimeField("Ώρα υπενθύμισης", blank=True, null=True)
    active = models.BooleanField("Ενεργό", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.dose} {self.get_unit_display()} - {self.frequency}"


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
        ordering = ["-date", "-time"]

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

    # Feeding-plan-specific targets. These are deliberately separate because
    # an energy-fortified regimen must not silently reuse a standard-formula
    # population volume target.
    target_with_maxijul_min_ml = models.PositiveIntegerField(
        "Με Maxijul — ελάχιστο ml/24ωρο",
        blank=True,
        null=True,
    )
    target_with_maxijul_max_ml = models.PositiveIntegerField(
        "Με Maxijul — μέγιστο ml/24ωρο",
        blank=True,
        null=True,
    )
    target_without_maxijul_min_ml = models.PositiveIntegerField(
        "Χωρίς Maxijul — ελάχιστο ml/24ωρο",
        blank=True,
        null=True,
    )
    target_without_maxijul_max_ml = models.PositiveIntegerField(
        "Χωρίς Maxijul — μέγιστο ml/24ωρο",
        blank=True,
        null=True,
    )
    feeding_target_note = models.CharField(
        "Σημείωση εξατομικευμένων στόχων",
        max_length=300,
        blank=True,
        help_text="Πηγή/ημερομηνία οδηγίας μεταβολικής ομάδας ή παιδιάτρου.",
    )
    feeding_interval_minutes = models.PositiveSmallIntegerField(
        "Διάστημα επόμενου γεύματος από το τέλος (λεπτά)",
        default=180,
        help_text="Το επόμενο γεύμα υπολογίζεται από την ώρα ολοκλήρωσης του προηγούμενου.",
    )
    maxijul_plan_active = models.BooleanField(
        "Τρέχον πλάνο με Maxijul",
        default=True,
        help_text="Χρησιμοποιείται μόνο όταν δεν υπάρχουν ακόμη γεύματα για τη σημερινή ημέρα.",
    )
    planned_maxijul_scoops_per_feed = models.DecimalField(
        "Προγραμματισμένα scoops Maxijul / γεύμα",
        max_digits=5,
        decimal_places=2,
        default=1,
    )
    maxijul_scoop_grams = models.DecimalField(
        "Maxijul — γραμμάρια ανά scoop",
        max_digits=5,
        decimal_places=2,
        default=4.20,
        help_text="Ελέγξτε ότι αντιστοιχεί στο scoop που χρησιμοποιείτε.",
    )
    maxijul_kcal_per_100g = models.DecimalField(
        "Maxijul — kcal / 100 g",
        max_digits=6,
        decimal_places=1,
        default=380,
    )
    maxijul_carbs_per_100g = models.DecimalField(
        "Maxijul — υδατάνθρακες g / 100 g",
        max_digits=6,
        decimal_places=1,
        default=95,
    )
    known_allergies = models.TextField(
        "Γνωστές αλλεργίες",
        blank=True,
        help_text="Καταχώρησε μόνο επιβεβαιωμένες/γνωστές αλλεργίες. Άφησέ το κενό αν δεν υπάρχουν.",
    )
    emergency_instructions = models.TextField("Βασικές ιατρικές οδηγίες", blank=True)
    treating_doctors = models.TextField(
        "Θεράποντες ιατροί",
        blank=True,
        default="Δρ Σάββας Σάββα - Παιδίατρος\nΔρ Όλγα Γραφάκου - Κλινική ΝΑΜΙΙ",
    )
    father_phone = models.CharField("Τηλέφωνο μπαμπά", max_length=40, blank=True)
    mother_phone = models.CharField("Τηλέφωνο μαμάς", max_length=40, blank=True)
    dr_savvas_phone = models.CharField("Τηλέφωνο Δρ Σάββας Σάββα", max_length=40, blank=True)
    dr_grafakou_phone = models.CharField("Τηλέφωνο Δρ Όλγα Γραφάκου", max_length=40, blank=True)
    emergency_contacts = models.TextField(
        "Άλλο τηλέφωνο / επαφή",
        blank=True,
        help_text="Προαιρετικά: άλλο τηλέφωνο, κλινική, νοσοκομείο ή επαφή.",
    )
    current_feeding_plan = models.TextField("Τρέχον πλάνο σίτισης", blank=True)
    emergency_share_enabled = models.BooleanField("Emergency QR ενεργό", default=False)
    emergency_share_token = models.UUIDField("Emergency share token", default=uuid.uuid4, unique=True, editable=False)
    emergency_share_show_identity = models.BooleanField("QR: όνομα & DOB", default=True)
    emergency_share_show_instructions = models.BooleanField("QR: βασικές ιατρικές οδηγίες", default=True)
    emergency_share_show_feeding = models.BooleanField("QR: πλάνο σίτισης", default=True)
    emergency_share_show_doctors = models.BooleanField("QR: θεράποντες ιατροί", default=True)
    emergency_share_show_phones = models.BooleanField("QR: τηλέφωνα", default=True)
    emergency_share_show_glucose = models.BooleanField("QR: τελευταία γλυκόζη", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Προφίλ παιδιού"
        verbose_name_plural = "Προφίλ παιδιού"

    FIXED_BIRTH_DATE = date(2026, 6, 27)

    def save(self, *args, **kwargs):
        # Birth date is intentionally fixed for this single-child private app.
        self.birth_date = self.FIXED_BIRTH_DATE
        super().save(*args, **kwargs)

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
    photo_name = models.CharField("Όνομα φωτογραφίας", max_length=255, blank=True)
    photo_mime = models.CharField("Τύπος φωτογραφίας", max_length=120, blank=True)
    photo_data = models.BinaryField("Φωτογραφία", blank=True, null=True, editable=False)
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
    possible_diarrhea = models.BooleanField("Πιθανή διάρροια", default=False)
    notes = models.TextField("Σημειώσεις", blank=True)
    photo_name = models.CharField("Όνομα φωτογραφίας", max_length=255, blank=True)
    photo_mime = models.CharField("Τύπος φωτογραφίας", max_length=120, blank=True)
    photo_data = models.BinaryField("Φωτογραφία", blank=True, null=True, editable=False)
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



class SafetyRule(models.Model):
    APPLIES_TO_CHOICES = [
        ("food", "Τρόφιμα"),
        ("medicine", "Φάρμακα"),
        ("both", "Τρόφιμα και φάρμακα"),
    ]
    GUIDANCE_CHOICES = [
        ("avoid", "Να αποφεύγεται"),
        ("caution", "Χρειάζεται έλεγχος"),
    ]

    term = models.CharField("Συστατικό / όρος", max_length=160)
    applies_to = models.CharField(
        "Ισχύει για",
        max_length=20,
        choices=APPLIES_TO_CHOICES,
        default="both",
    )
    guidance = models.CharField(
        "Οδηγία",
        max_length=20,
        choices=GUIDANCE_CHOICES,
        default="caution",
    )
    note = models.CharField(
        "Σημείωση / πηγή οδηγίας",
        max_length=255,
        blank=True,
        help_text="Π.χ. οδηγία παιδιάτρου, μεταβολικής ομάδας ή φαρμακοποιού.",
    )
    active = models.BooleanField("Ενεργό", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["term"]

    def __str__(self):
        return f"{self.term} - {self.get_guidance_display()}"


class ProductSafetyRecord(models.Model):
    KIND_CHOICES = [
        ("food", "Τρόφιμο / ρόφημα"),
        ("medicine", "Φάρμακο / σκεύασμα"),
    ]
    DECISION_CHOICES = [
        ("confirmed", "Επιβεβαιωμένο από ιατρό / φαρμακοποιό"),
        ("checked", "Ελέγχθηκε — δεν εντοπίστηκε περιορισμός"),
        ("avoid", "Να αποφεύγεται"),
        ("caution", "Χρειάζεται έλεγχος"),
    ]

    kind = models.CharField("Τύπος", max_length=20, choices=KIND_CHOICES)
    name = models.CharField("Ονομασία προϊόντος / φαρμάκου", max_length=220)
    barcode = models.CharField("Barcode", max_length=64, blank=True, db_index=True)
    decision = models.CharField("Καταχωρημένη αξιολόγηση", max_length=20, choices=DECISION_CHOICES)
    ingredients = models.TextField(
        "Συστατικά / έκδοχα",
        blank=True,
        help_text="Προαιρετικά: αντιγραφή από ετικέτα ή φύλλο οδηγιών.",
    )
    confirmed_by = models.CharField(
        "Επιβεβαιώθηκε από",
        max_length=180,
        blank=True,
        help_text="Για επιβεβαιωμένο προϊόν γράψε ιατρό ή φαρμακοποιό.",
    )
    reviewed_on = models.DateField("Ημερομηνία ελέγχου", blank=True, null=True)
    notes = models.TextField("Σημειώσεις", blank=True)
    label_photo_name = models.CharField("Όνομα φωτογραφίας ετικέτας", max_length=255, blank=True)
    label_photo_mime = models.CharField("Τύπος φωτογραφίας ετικέτας", max_length=120, blank=True)
    label_photo_data = models.BinaryField("Φωτογραφία ετικέτας", blank=True, null=True, editable=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_safety_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["kind", "name"]

    def __str__(self):
        return f"{self.name} - {self.get_decision_display()}"



class LabResult(models.Model):
    date = models.DateField("Ημερομηνία εξέτασης")
    time = models.TimeField("Ώρα", blank=True, null=True)
    test_name = models.CharField("Εξέταση", max_length=160, db_index=True)
    value = models.DecimalField("Τιμή", max_digits=12, decimal_places=4)
    unit = models.CharField("Μονάδα", max_length=80, blank=True)
    reference_min = models.DecimalField("Κατώτερο όριο αναφοράς", max_digits=12, decimal_places=4, blank=True, null=True)
    reference_max = models.DecimalField("Ανώτερο όριο αναφοράς", max_digits=12, decimal_places=4, blank=True, null=True)
    laboratory = models.CharField("Εργαστήριο", max_length=180, blank=True)
    notes = models.TextField("Σημειώσεις", blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="lab_results"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time", "test_name"]

    @property
    def weekday_name(self):
        return greek_weekday(self.date)

    def __str__(self):
        suffix = f" {self.unit}" if self.unit else ""
        return f"{self.date} - {self.test_name}: {self.value}{suffix}"


class HealthReminder(models.Model):
    TYPE_CHOICES = [
        ("meal", "Γεύμα"),
        ("medication", "Φάρμακο"),
        ("vaccine", "Εμβόλιο"),
        ("measurement", "Μέτρηση"),
        ("lab", "Εξέταση"),
        ("appointment", "Ραντεβού"),
        ("other", "Άλλο"),
    ]

    reminder_type = models.CharField("Τύπος", max_length=20, choices=TYPE_CHOICES, default="other")
    title = models.CharField("Τίτλος", max_length=180)
    due_at = models.DateTimeField("Ημερομηνία / ώρα")
    notes = models.TextField("Σημειώσεις", blank=True)
    auto_generated = models.BooleanField("Αυτόματη υπενθύμιση", default=False)
    source_key = models.CharField(
        "Κλειδί αυτόματης υπενθύμισης",
        max_length=140,
        blank=True,
        null=True,
        unique=True,
    )
    notify_minutes_before = models.PositiveSmallIntegerField(
        "Push ειδοποίηση (λεπτά πριν)",
        default=0,
        help_text="0 = στην ακριβή ώρα της υπενθύμισης.",
    )
    repeat_if_incomplete_minutes = models.PositiveSmallIntegerField(
        "Επανάληψη αν δεν ολοκληρωθεί (λεπτά μετά)",
        default=0,
        help_text="0 = χωρίς δεύτερη ειδοποίηση.",
    )
    push_notified_at = models.DateTimeField("Πρώτη push ειδοποίηση", blank=True, null=True)
    push_repeat_notified_at = models.DateTimeField("Επαναληπτική push ειδοποίηση", blank=True, null=True)
    active = models.BooleanField("Ενεργό", default=True)
    completed = models.BooleanField("Ολοκληρώθηκε", default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="health_reminders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["completed", "due_at"]

    def __str__(self):
        return f"{self.title} - {self.due_at:%d/%m/%Y %H:%M}"


class DoctorQuestion(models.Model):
    STATUS_CHOICES = [
        ("pending", "Εκκρεμεί"),
        ("answered", "Απαντήθηκε"),
    ]

    question = models.TextField("Ερώτηση για τον γιατρό")
    status = models.CharField("Κατάσταση", max_length=20, choices=STATUS_CHOICES, default="pending")
    appointment = models.ForeignKey(
        MedicalAppointment,
        verbose_name="Σχετικό ραντεβού",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="doctor_questions",
    )
    answer = models.TextField("Απάντηση / σημείωση", blank=True)
    answered_at = models.DateTimeField("Απαντήθηκε στις", blank=True, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="doctor_questions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-created_at"]

    def __str__(self):
        return self.question[:80]


class UserAccessProfile(models.Model):
    ROLE_CHOICES = [
        ("parent", "Γονέας / πλήρης πρόσβαση"),
        ("doctor_readonly", "Ιατρός / μόνο προβολή"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="access_profile")
    role = models.CharField("Ρόλος", max_length=30, choices=ROLE_CHOICES, default="parent")
    display_name = models.CharField("Εμφανιζόμενο όνομα", max_length=120, blank=True)

    def __str__(self):
        return self.display_name or self.user.username


class BackupRun(models.Model):
    STATUS_CHOICES = [
        ("success", "Επιτυχία"),
        ("failed", "Αποτυχία"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField("Κατάσταση", max_length=20, choices=STATUS_CHOICES)
    destination = models.CharField("Προορισμός", max_length=220, blank=True)
    size_bytes = models.PositiveBigIntegerField("Μέγεθος", default=0)
    notes = models.TextField("Σημειώσεις", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%d/%m/%Y %H:%M} - {self.get_status_display()}"



class PushSubscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.TextField("Push endpoint", unique=True)
    p256dh = models.TextField("P256DH key")
    auth = models.TextField("Auth key")
    user_agent = models.TextField("Συσκευή / browser", blank=True)
    active = models.BooleanField("Ενεργή", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:55]}"


class PushConfig(models.Model):
    private_key_pem = models.TextField("VAPID private key PEM")
    public_key_b64 = models.TextField("VAPID public key")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Push configuration"
        verbose_name_plural = "Push configuration"

    def __str__(self):
        return f"Push configuration {self.pk}"


class PushDeliveryLog(models.Model):
    reminder = models.ForeignKey(
        HealthReminder,
        on_delete=models.CASCADE,
        related_name="push_delivery_logs",
    )
    subscription = models.ForeignKey(
        PushSubscription,
        on_delete=models.CASCADE,
        related_name="delivery_logs",
    )
    delivery_kind = models.CharField(
        "Τύπος αποστολής",
        max_length=20,
        choices=[("initial", "Αρχική"), ("repeat", "Επανάληψη")],
    )
    success = models.BooleanField("Επιτυχία", default=False)
    status_code = models.IntegerField("HTTP status", blank=True, null=True)
    error = models.TextField("Σφάλμα", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reminder_id} - {self.delivery_kind} - {'OK' if self.success else 'FAILED'}"
