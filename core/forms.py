from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    GlucoseReading,
    GrowthMeasurement,
    MealEntry,
    MedicationEntry,
    MedicalAppointment,
    ChildProfile,
)


class PersistentAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        label="Να παραμείνω συνδεδεμένος",
        help_text="Σε προσωπική συσκευή, η σύνδεση μπορεί να παραμείνει ενεργή έως 90 ημέρες.",
    )


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, attrs=None, format=None):
        # HTML date inputs require YYYY-MM-DD. Without an explicit format,
        # localized Greek rendering can appear blank when editing an existing
        # record, forcing the user to enter the date again.
        super().__init__(attrs=attrs, format=format or "%Y-%m-%d")


class TimeInput(forms.TimeInput):
    input_type = "time"

    def __init__(self, attrs=None, format=None):
        # Keep existing times visible on every edit form.
        super().__init__(attrs=attrs, format=format or "%H:%M")


class MealEntryForm(forms.ModelForm):
    same_as_scheduled = forms.BooleanField(
        required=False,
        initial=True,
        label="Ώρα έναρξης ίδια με την προγραμματισμένη ώρα",
    )

    class Meta:
        model = MealEntry
        fields = [
            "date",
            "scheduled_time",
            "actual_time",
            "finished_time",
            "offered_ml",
            "remaining_ml",
            "consumed_ml",
            "formula",
            "supplement",
            "status",
            "notes",
        ]
        labels = {
            "scheduled_time": "Προγραμματισμένη ώρα γεύματος",
            "actual_time": "Ώρα έναρξης γεύματος",
            "finished_time": "Ώρα ολοκλήρωσης γεύματος",
            "formula": "Formula (κουταλάκια)",
            "supplement": "Maxijul (scoops)",
        }
        widgets = {
            "date": DateInput(),
            "scheduled_time": TimeInput(format="%H:%M"),
            "actual_time": TimeInput(format="%H:%M"),
            "finished_time": TimeInput(format="%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "offered_ml": forms.NumberInput(attrs={"inputmode": "numeric", "min": "0", "step": "1"}),
            "remaining_ml": forms.NumberInput(attrs={"inputmode": "numeric", "min": "0", "step": "1"}),
            "consumed_ml": forms.NumberInput(attrs={"inputmode": "numeric", "min": "0", "step": "1"}),
            "formula": forms.TextInput(attrs={"inputmode": "decimal"}),
            "supplement": forms.TextInput(attrs={"inputmode": "decimal"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields([
            "date",
            "scheduled_time",
            "same_as_scheduled",
            "actual_time",
            "finished_time",
            "offered_ml",
            "remaining_ml",
            "consumed_ml",
            "formula",
            "supplement",
            "status",
            "notes",
        ])

        self.fields["finished_time"].help_text = (
            "Προαιρετική καταγραφή. Δεν αλλάζει την ώρα του επόμενου γεύματος."
        )
        self.fields["remaining_ml"].help_text = (
            "Προαιρετικό. Αν το συμπληρώσεις, το «Ήπιε» υπολογίζεται αυτόματα: "
            "Προσφέρθηκαν − Έμεινε."
        )
        self.fields["consumed_ml"].help_text = (
            "Υπολογίζεται αυτόματα όταν συμπληρώνεται το «Έμεινε». "
            "Μπορείς επίσης να το γράψεις κανονικά όπως πριν."
        )

        if self.instance and self.instance.pk:
            self.fields["same_as_scheduled"].initial = bool(
                self.instance.actual_time
                and self.instance.scheduled_time
                and self.instance.actual_time == self.instance.scheduled_time
            )

    def clean(self):
        cleaned = super().clean()
        scheduled_time = cleaned.get("scheduled_time")
        if cleaned.get("same_as_scheduled") and scheduled_time:
            cleaned["actual_time"] = scheduled_time

        offered = cleaned.get("offered_ml")
        remaining = cleaned.get("remaining_ml")
        consumed = cleaned.get("consumed_ml")

        if remaining is not None:
            if offered is None:
                self.add_error(
                    "remaining_ml",
                    "Για να υπολογιστεί πόσο ήπιε, συμπλήρωσε πρώτα πόσα ml προσφέρθηκαν.",
                )
            elif remaining > offered:
                self.add_error(
                    "remaining_ml",
                    "Το υπόλοιπο δεν μπορεί να είναι μεγαλύτερο από όσα ml προσφέρθηκαν.",
                )
            else:
                cleaned["consumed_ml"] = offered - remaining
        elif offered is not None and consumed is not None:
            if consumed > offered:
                self.add_error(
                    "consumed_ml",
                    "Η ποσότητα που ήπιε δεν μπορεί να είναι μεγαλύτερη από όσα ml προσφέρθηκαν.",
                )
            else:
                cleaned["remaining_ml"] = offered - consumed

        return cleaned


class GlucoseReadingForm(forms.ModelForm):
    class Meta:
        model = GlucoseReading
        fields = ["date", "time", "value", "context", "related_meal", "notes"]
        widgets = {
            "date": DateInput(),
            "time": TimeInput(format="%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class GrowthMeasurementForm(forms.ModelForm):
    class Meta:
        model = GrowthMeasurement
        fields = ["date", "weight_kg", "length_cm", "head_cm", "notes"]
        widgets = {
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class MedicationEntryForm(forms.ModelForm):
    class Meta:
        model = MedicationEntry
        fields = ["date", "time", "name", "dose", "unit", "notes"]
        widgets = {
            "date": DateInput(),
            "time": TimeInput(format="%H:%M"),
            "dose": forms.NumberInput(attrs={"min": "0", "step": "0.01", "inputmode": "decimal"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class MedicalAppointmentForm(forms.ModelForm):
    PROVIDER_CHOICES = [
        ("savvas", "Δρ Σάββας Σάββα - Παιδίατρος (Κλινική)"),
        ("grafakou", "Δρ Όλγα Γραφάκου (Κλινική ΝΑΜΙΙ)"),
        ("other", "Άλλο - να γράψω εγώ"),
    ]

    doctor_choice = forms.ChoiceField(
        label="Ιατρός / Κλινική",
        choices=PROVIDER_CHOICES,
        initial="savvas",
    )
    other_doctor = forms.CharField(
        label="Άλλος ιατρός",
        required=False,
        max_length=160,
        widget=forms.TextInput(attrs={"placeholder": "Γράψε το όνομα του ιατρού"}),
    )
    other_clinic = forms.CharField(
        label="Κλινική / νοσοκομείο",
        required=False,
        max_length=180,
        widget=forms.TextInput(attrs={"placeholder": "Προαιρετικά, γράψε κλινική ή νοσοκομείο"}),
    )

    class Meta:
        model = MedicalAppointment
        fields = [
            "date",
            "time",
            "purpose",
            "reminder_days_before",
            "status",
            "notes",
        ]
        widgets = {
            "date": DateInput(),
            "time": TimeInput(format="%H:%M"),
            "reminder_days_before": forms.NumberInput(attrs={"min": "0", "max": "90", "step": "1"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.order_fields([
            "date",
            "time",
            "doctor_choice",
            "other_doctor",
            "other_clinic",
            "purpose",
            "reminder_days_before",
            "status",
            "notes",
        ])

        if self.instance and self.instance.pk:
            doctor = (self.instance.doctor or "").strip()
            clinic = (self.instance.clinic or "").strip()

            if doctor == "Δρ Σάββας Σάββα - Παιδίατρος" and clinic == "Κλινική":
                self.fields["doctor_choice"].initial = "savvas"
            elif doctor == "Δρ Όλγα Γραφάκου" and clinic == "Κλινική ΝΑΜΙΙ":
                self.fields["doctor_choice"].initial = "grafakou"
            else:
                self.fields["doctor_choice"].initial = "other"
                self.fields["other_doctor"].initial = doctor
                self.fields["other_clinic"].initial = clinic

    def clean(self):
        cleaned = super().clean()
        choice = cleaned.get("doctor_choice")

        if choice == "savvas":
            cleaned["_resolved_doctor"] = "Δρ Σάββας Σάββα - Παιδίατρος"
            cleaned["_resolved_clinic"] = "Κλινική"
        elif choice == "grafakou":
            cleaned["_resolved_doctor"] = "Δρ Όλγα Γραφάκου"
            cleaned["_resolved_clinic"] = "Κλινική ΝΑΜΙΙ"
        elif choice == "other":
            other_doctor = (cleaned.get("other_doctor") or "").strip()
            other_clinic = (cleaned.get("other_clinic") or "").strip()

            if not other_doctor:
                self.add_error("other_doctor", "Γράψε το όνομα του ιατρού.")
            cleaned["_resolved_doctor"] = other_doctor
            cleaned["_resolved_clinic"] = other_clinic

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.doctor = self.cleaned_data.get("_resolved_doctor", "")
        instance.clinic = self.cleaned_data.get("_resolved_clinic", "")

        if commit:
            instance.save()
            self.save_m2m()

        return instance



class ChildProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].disabled = True
        self.fields["birth_date"].help_text = "Κλειδωμένη ημερομηνία γέννησης: 27/06/2026."

        # Legacy generic target fields remain in the database only for backwards
        # compatibility. The UI now uses plan-specific targets exclusively.
        self.fields["target_with_maxijul_min_ml"].help_text = (
            "Συμπληρώνεται μόνο από συγκεκριμένη οδηγία της μεταβολικής ομάδας/παιδιάτρου."
        )
        self.fields["target_without_maxijul_min_ml"].help_text = (
            "Συμπληρώνεται μόνο αν έχει δοθεί συγκεκριμένος στόχος χωρίς Maxijul."
        )

    class Meta:
        model = ChildProfile
        fields = [
            "name",
            "full_name",
            "birth_date",
            "maxijul_plan_active",
            "planned_maxijul_scoops_per_feed",
            "target_with_maxijul_min_ml",
            "target_with_maxijul_max_ml",
            "target_without_maxijul_min_ml",
            "target_without_maxijul_max_ml",
            "feeding_target_note",
            "known_allergies",
            "maxijul_scoop_grams",
            "maxijul_kcal_per_100g",
            "maxijul_carbs_per_100g",
        ]
        widgets = {
            "birth_date": DateInput(),
            "planned_maxijul_scoops_per_feed": forms.NumberInput(
                attrs={"min": "0", "step": "0.25", "inputmode": "decimal"}
            ),
            "target_with_maxijul_min_ml": forms.NumberInput(
                attrs={"min": "0", "step": "1", "inputmode": "numeric"}
            ),
            "target_with_maxijul_max_ml": forms.NumberInput(
                attrs={"min": "0", "step": "1", "inputmode": "numeric"}
            ),
            "target_without_maxijul_min_ml": forms.NumberInput(
                attrs={"min": "0", "step": "1", "inputmode": "numeric"}
            ),
            "target_without_maxijul_max_ml": forms.NumberInput(
                attrs={"min": "0", "step": "1", "inputmode": "numeric"}
            ),
            "maxijul_scoop_grams": forms.NumberInput(
                attrs={"min": "0", "step": "0.01", "inputmode": "decimal"}
            ),
            "maxijul_kcal_per_100g": forms.NumberInput(
                attrs={"min": "0", "step": "0.1", "inputmode": "decimal"}
            ),
            "maxijul_carbs_per_100g": forms.NumberInput(
                attrs={"min": "0", "step": "0.1", "inputmode": "decimal"}
            ),
        }

    def clean(self):
        cleaned = super().clean()

        pairs = [
            (
                "target_with_maxijul_min_ml",
                "target_with_maxijul_max_ml",
            ),
            (
                "target_without_maxijul_min_ml",
                "target_without_maxijul_max_ml",
            ),
        ]

        for minimum_name, maximum_name in pairs:
            minimum = cleaned.get(minimum_name)
            maximum = cleaned.get(maximum_name)
            if minimum is not None and maximum is not None and minimum > maximum:
                self.add_error(
                    maximum_name,
                    "Το μέγιστο πρέπει να είναι ίσο ή μεγαλύτερο από το ελάχιστο.",
                )

        return cleaned
