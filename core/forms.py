from django import forms
from .models import (
    GlucoseReading,
    GrowthMeasurement,
    MealEntry,
    MedicationEntry,
    MedicalAppointment,
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
    class Meta:
        model = MedicalAppointment
        fields = [
            "date",
            "time",
            "doctor",
            "clinic",
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
