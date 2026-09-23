from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .forms import DateInput, TimeInput
from .models import (
    DiaperEntry,
    DoctorQuestion,
    HealthReminder,
    LabResult,
    ProductSafetyRecord,
    SymptomEntry,
    UserAccessProfile,
)


MAX_IMAGE_SIZE = 6 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image(upload):
    suffix = Path(upload.name).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise forms.ValidationError("Επιτρέπονται JPG, JPEG, PNG ή WEBP.")
    if upload.size > MAX_IMAGE_SIZE:
        raise forms.ValidationError("Η φωτογραφία πρέπει να είναι έως 6 MB.")
    return upload


def save_photo_to_instance(instance, upload):
    if not upload:
        return

    raw = upload.read()
    instance.photo_name = Path(upload.name).name
    instance.photo_mime = upload.content_type or "image/jpeg"
    instance.photo_data = raw

    # Mobile photos can have very large pixel dimensions even when the file is
    # below the 6 MB upload limit. Store an optimized copy for faster database
    # reads, page rendering and photo display. If Pillow cannot decode the
    # image, keep the original bytes rather than losing the upload.
    try:
        with Image.open(BytesIO(raw)) as source:
            image = ImageOps.exif_transpose(source)
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            elif image.mode == "L":
                image = image.convert("RGB")

            output = BytesIO()
            image.save(
                output,
                format="JPEG",
                quality=82,
                optimize=True,
                progressive=True,
            )
            optimized = output.getvalue()

        if optimized and len(optimized) < len(raw):
            stem = Path(upload.name).stem or "photo"
            instance.photo_name = f"{stem}.jpg"
            instance.photo_mime = "image/jpeg"
            instance.photo_data = optimized
    except Exception:
        pass


class SymptomWithPhotoForm(forms.ModelForm):
    photo = forms.FileField(
        label="Φωτογραφία",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"}),
    )

    class Meta:
        model = SymptomEntry
        fields = ["date", "time", "symptom", "severity", "duration_minutes", "relation_to_feed", "notes"]
        widgets = {
            "date": DateInput(),
            "time": TimeInput(format="%H:%M"),
            "duration_minutes": forms.NumberInput(attrs={"min": "0", "step": "1"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_photo(self):
        upload = self.cleaned_data.get("photo")
        if upload:
            validate_image(upload)
        return upload

    def save_photo(self, instance, upload):
        save_photo_to_instance(instance, upload)


class DiaperWithPhotoForm(forms.ModelForm):
    photo = forms.FileField(
        label="Φωτογραφία",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"}),
    )
    stool_consistency = forms.ChoiceField(
        label="Σύσταση",
        required=False,
        choices=[
            ("", "---------"),
            ("Σχηματισμένη", "Σχηματισμένη"),
            ("Μαλακή", "Μαλακή"),
            ("Πολτώδης", "Πολτώδης"),
            ("Υδαρής / πολύ υδαρής", "Υδαρής / πολύ υδαρής («πορδοζούμι»)"),
        ],
    )

    class Meta:
        model = DiaperEntry
        fields = ["date", "time", "kind", "stool_color", "stool_consistency", "possible_diarrhea", "notes"]
        widgets = {
            "date": DateInput(),
            "time": TimeInput(format="%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["possible_diarrhea"].help_text = (
            "Τσέκαρέ το αν η κένωση σου φαίνεται πιθανή διάρροια. "
            "Είναι παρατήρηση καταγραφής και όχι ιατρική διάγνωση."
        )
        # Preserve any older free-text value if one already exists.
        if self.instance and self.instance.pk and self.instance.stool_consistency:
            current = self.instance.stool_consistency
            values = [value for value, _ in self.fields["stool_consistency"].choices]
            if current not in values:
                self.fields["stool_consistency"].choices = list(
                    self.fields["stool_consistency"].choices
                ) + [(current, current)]

    def clean_photo(self):
        upload = self.cleaned_data.get("photo")
        if upload:
            validate_image(upload)
        return upload

    def save_photo(self, instance, upload):
        save_photo_to_instance(instance, upload)


class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = [
            "date", "time", "test_name", "value", "unit",
            "reference_min", "reference_max", "laboratory", "notes"
        ]
        widgets = {
            "date": DateInput(),
            "time": TimeInput(format="%H:%M"),
            "value": forms.NumberInput(attrs={"step": "0.0001", "inputmode": "decimal"}),
            "reference_min": forms.NumberInput(attrs={"step": "0.0001", "inputmode": "decimal"}),
            "reference_max": forms.NumberInput(attrs={"step": "0.0001", "inputmode": "decimal"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class HealthReminderForm(forms.ModelForm):
    due_date = forms.DateField(label="Ημερομηνία", widget=DateInput())
    due_time = forms.TimeField(label="Ώρα", widget=TimeInput(format="%H:%M"))
    notify_minutes_before = forms.TypedChoiceField(
        label="Push ειδοποίηση",
        coerce=int,
        choices=[
            (0, "Στην ακριβή ώρα"),
            (5, "5 λεπτά πριν"),
            (10, "10 λεπτά πριν"),
            (11, "11 λεπτά πριν"),
            (12, "12 λεπτά πριν"),
            (15, "15 λεπτά πριν"),
            (30, "30 λεπτά πριν"),
            (60, "1 ώρα πριν"),
        ],
        initial=0,
    )
    repeat_if_incomplete_minutes = forms.TypedChoiceField(
        label="2η ειδοποίηση αν δεν ολοκληρωθεί",
        coerce=int,
        choices=[
            (0, "Όχι"),
            (5, "5 λεπτά μετά"),
            (10, "10 λεπτά μετά"),
            (15, "15 λεπτά μετά"),
            (30, "30 λεπτά μετά"),
            (60, "1 ώρα μετά"),
        ],
        initial=0,
    )

    class Meta:
        model = HealthReminder
        fields = [
            "reminder_type",
            "title",
            "notify_minutes_before",
            "repeat_if_incomplete_minutes",
            "notes",
            "active",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        if instance and instance.pk and instance.due_at:
            local = timezone.localtime(instance.due_at)
            self.fields["due_date"].initial = local.date()
            self.fields["due_time"].initial = local.time().replace(second=0, microsecond=0)
        self.order_fields([
            "reminder_type",
            "title",
            "due_date",
            "due_time",
            "notify_minutes_before",
            "repeat_if_incomplete_minutes",
            "notes",
            "active",
        ])


class DoctorQuestionForm(forms.ModelForm):
    class Meta:
        model = DoctorQuestion
        fields = ["question", "appointment"]
        widgets = {"question": forms.Textarea(attrs={"rows": 4})}


class DoctorQuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = DoctorQuestion
        fields = ["answer"]
        widgets = {"answer": forms.Textarea(attrs={"rows": 5, "placeholder": "Γράψε την απάντηση / οδηγία του γιατρού"})}


class ScannedProductForm(forms.ModelForm):
    label_photo = forms.FileField(
        label="Φωτογραφία ετικέτας",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"}),
    )

    class Meta:
        model = ProductSafetyRecord
        fields = ["kind", "name", "barcode", "decision", "ingredients", "confirmed_by", "reviewed_on", "notes"]
        widgets = {
            "reviewed_on": DateInput(),
            "ingredients": forms.Textarea(attrs={"rows": 7}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_label_photo(self):
        upload = self.cleaned_data.get("label_photo")
        if upload:
            validate_image(upload)
        return upload

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision") == "confirmed" and not (cleaned.get("confirmed_by") or "").strip():
            self.add_error("confirmed_by", "Γράψε ποιος επιβεβαίωσε το προϊόν/φάρμακο.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        upload = self.cleaned_data.get("label_photo")
        if upload:
            instance.label_photo_name = Path(upload.name).name
            instance.label_photo_mime = upload.content_type or "image/jpeg"
            instance.label_photo_data = upload.read()
        if commit:
            instance.save()
        return instance


class EmergencyShareForm(forms.Form):
    enabled = forms.BooleanField(
        label="Ενεργοποίηση Emergency QR",
        required=False,
        help_text="Όταν είναι ενεργό, όποιος έχει το QR/link μπορεί να δει μόνο την ειδική read-only emergency σελίδα.",
    )
    show_identity = forms.BooleanField(label="Να φαίνονται όνομα & ημερομηνία γέννησης", required=False)
    show_instructions = forms.BooleanField(label="Να φαίνονται βασικές ιατρικές οδηγίες", required=False)
    show_feeding = forms.BooleanField(label="Να φαίνεται το τρέχον πλάνο σίτισης", required=False)
    show_doctors = forms.BooleanField(label="Να φαίνονται οι θεράποντες ιατροί", required=False)
    show_phones = forms.BooleanField(label="Να φαίνονται τα τηλέφωνα", required=False)
    show_glucose = forms.BooleanField(label="Να φαίνεται η τελευταία καταχωρημένη γλυκόζη", required=False)


class CreateAccessUserForm(UserCreationForm):
    role = forms.ChoiceField(label="Ρόλος", choices=UserAccessProfile.ROLE_CHOICES)
    display_name = forms.CharField(label="Εμφανιζόμενο όνομα", max_length=120, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "role", "display_name", "password1", "password2")


class EditAccessUserForm(forms.Form):
    role = forms.ChoiceField(label="Ρόλος", choices=UserAccessProfile.ROLE_CHOICES)
    display_name = forms.CharField(label="Εμφανιζόμενο όνομα", max_length=120, required=False)
    is_active = forms.BooleanField(label="Ενεργός λογαριασμός", required=False)
