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


class TimeInput(forms.TimeInput):
    input_type = "time"


class MealEntryForm(forms.ModelForm):
    same_as_scheduled = forms.BooleanField(
        required=False,
        initial=True,
        label="Πραγματική ώρα ίδια με την προγραμματισμένη",
    )

    class Meta:
        model = MealEntry
        fields = [
            "date",
            "scheduled_time",
            "actual_time",
            "offered_ml",
            "consumed_ml",
            "formula",
            "supplement",
            "status",
            "notes",
        ]
        labels = {
            "formula": "Formula (κουταλάκια)",
            "supplement": "Συμπλήρωμα (κουταλάκια)",
        }
        widgets = {
            "date": DateInput(),
            "scheduled_time": TimeInput(format="%H:%M"),
            "actual_time": TimeInput(format="%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "offered_ml": forms.NumberInput(attrs={"inputmode": "numeric", "min": "0", "step": "1"}),
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
            "offered_ml",
            "consumed_ml",
            "formula",
            "supplement",
            "status",
            "notes",
        ])

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
    class Meta:
        model = ChildProfile
        fields = [
            "name",
            "birth_date",
            "clinician_target_min_ml",
            "clinician_target_max_ml",
            "clinician_target_note",
        ]
        widgets = {
            "birth_date": DateInput(),
            "clinician_target_min_ml": forms.NumberInput(attrs={"min": "0", "step": "1", "inputmode": "numeric"}),
            "clinician_target_max_ml": forms.NumberInput(attrs={"min": "0", "step": "1", "inputmode": "numeric"}),
        }

    def clean(self):
        cleaned = super().clean()
        minimum = cleaned.get("clinician_target_min_ml")
        maximum = cleaned.get("clinician_target_max_ml")
        if minimum is not None and maximum is not None and minimum > maximum:
            self.add_error(
                "clinician_target_max_ml",
                "Το μέγιστο πρέπει να είναι ίσο ή μεγαλύτερο από το ελάχιστο.",
            )
        return cleaned
