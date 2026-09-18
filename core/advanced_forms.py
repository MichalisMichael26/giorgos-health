from pathlib import Path

from django import forms

from .forms import DateInput, TimeInput
from .models import ChildProfile, DiaperEntry, SymptomEntry, VaccineEntry, MedicalDocument, SafetyRule, ProductSafetyRecord


ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


class MedicalDocumentForm(forms.Form):
    date = forms.DateField(label="Ημερομηνία εγγράφου", widget=DateInput())
    category = forms.ChoiceField(label="Κατηγορία", choices=MedicalDocument.CATEGORY_CHOICES)
    title = forms.CharField(label="Τίτλος", max_length=220)
    upload = forms.FileField(
        label="Αρχείο",
        help_text="PDF, JPG ή PNG έως 10 MB. Το αρχείο αποθηκεύεται στη βάση δεδομένων.",
    )
    notes = forms.CharField(label="Σημειώσεις", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def clean_upload(self):
        upload = self.cleaned_data["upload"]
        suffix = Path(upload.name).suffix.lower()
        if suffix not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise forms.ValidationError("Επιτρέπονται μόνο PDF, JPG, JPEG και PNG.")
        if upload.size > MAX_DOCUMENT_SIZE:
            raise forms.ValidationError("Το αρχείο πρέπει να είναι έως 10 MB.")
        return upload


class MedicalDocumentMetadataForm(forms.ModelForm):
    class Meta:
        model = MedicalDocument
        fields = ["date", "category", "title", "notes"]
        widgets = {
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class VaccineEntryForm(forms.ModelForm):
    class Meta:
        model = VaccineEntry
        fields = ["date", "name", "dose_label", "next_date", "reminder_days_before", "notes"]
        widgets = {
            "date": DateInput(),
            "next_date": DateInput(),
            "reminder_days_before": forms.NumberInput(attrs={"min": "0", "max": "90", "step": "1"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class SymptomEntryForm(forms.ModelForm):
    class Meta:
        model = SymptomEntry
        fields = ["date", "time", "symptom", "severity", "duration_minutes", "relation_to_feed", "notes"]
        widgets = {
            "date": DateInput(),
            "time": TimeInput(format="%H:%M"),
            "duration_minutes": forms.NumberInput(attrs={"min": "0", "step": "1", "inputmode": "numeric"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class DiaperEntryForm(forms.ModelForm):
    class Meta:
        model = DiaperEntry
        fields = ["date", "time", "kind", "stool_color", "stool_consistency", "notes"]
        widgets = {
            "date": DateInput(),
            "time": TimeInput(format="%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class EmergencyProfileForm(forms.ModelForm):
    class Meta:
        model = ChildProfile
        fields = [
            "full_name",
            "birth_date",
            "emergency_instructions",
            "treating_doctors",
            "emergency_contacts",
            "current_feeding_plan",
        ]
        widgets = {
            "birth_date": DateInput(),
            "emergency_instructions": forms.Textarea(attrs={"rows": 5}),
            "treating_doctors": forms.Textarea(attrs={"rows": 4}),
            "emergency_contacts": forms.Textarea(attrs={"rows": 4}),
            "current_feeding_plan": forms.Textarea(attrs={"rows": 5}),
        }



class ProductCheckerForm(forms.Form):
    KIND_CHOICES = [
        ("food", "Τρόφιμο / ρόφημα"),
        ("medicine", "Φάρμακο / σκεύασμα"),
    ]

    kind = forms.ChoiceField(label="Τύπος", choices=KIND_CHOICES)
    name = forms.CharField(
        label="Ονομασία",
        max_length=220,
        widget=forms.TextInput(attrs={"placeholder": "Π.χ. όνομα προϊόντος ή φαρμάκου"}),
    )
    ingredients = forms.CharField(
        label="Συστατικά / έκδοχα",
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 6,
            "placeholder": "Αντέγραψε εδώ τα συστατικά από την ετικέτα ή τα έκδοχα από το φύλλο οδηγιών.",
        }),
        help_text="Ο αυτόματος έλεγχος γίνεται μόνο πάνω στους κανόνες που έχετε καταχωρήσει.",
    )


class SafetyRuleForm(forms.ModelForm):
    class Meta:
        model = SafetyRule
        fields = ["term", "applies_to", "guidance", "note", "active"]


class ProductSafetyRecordForm(forms.ModelForm):
    class Meta:
        model = ProductSafetyRecord
        fields = [
            "kind",
            "name",
            "decision",
            "ingredients",
            "confirmed_by",
            "reviewed_on",
            "notes",
        ]
        widgets = {
            "reviewed_on": DateInput(),
            "ingredients": forms.Textarea(attrs={"rows": 5}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision") == "confirmed" and not (cleaned.get("confirmed_by") or "").strip():
            self.add_error(
                "confirmed_by",
                "Για επιβεβαιωμένο προϊόν/φάρμακο γράψε ποιος το επιβεβαίωσε.",
            )
        return cleaned
