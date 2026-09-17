from django import forms
from .models import GlucoseReading, GrowthMeasurement, MealEntry


class DateInput(forms.DateInput):
    input_type = "date"


class TimeInput(forms.TimeInput):
    input_type = "time"


class MealEntryForm(forms.ModelForm):
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
        widgets = {
            "date": DateInput(),
            "scheduled_time": TimeInput(format="%H:%M"),
            "actual_time": TimeInput(format="%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


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
