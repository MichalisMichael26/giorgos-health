"""Standalone, parent-observed mood journal; unrelated to meal calculations."""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .access import is_readonly_doctor
from .models import MoodEntry


class MoodEntryForm(forms.ModelForm):
    moods = forms.MultipleChoiceField(
        label="Επίλεξε 1 έως 3 διαθέσεις",
        choices=MoodEntry.MOOD_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={"required": "Επίλεξε τουλάχιστον μία διάθεση."},
    )

    class Meta:
        model = MoodEntry
        # Preserve the original 'mood' field; the new multi-select drives it.
        fields = ("date", "time", "notes")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "notes": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Προαιρετικά: τι παρατήρησες, πριν/μετά τη σίτιση ή τον ρινογαστρικό;",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].input_formats = ["%Y-%m-%d"]
        self.fields["time"].input_formats = ["%H:%M", "%H:%M:%S"]
        if not self.is_bound and self.instance and self.instance.pk:
            self.initial["moods"] = [
                self.instance.mood, *(self.instance.additional_moods or [])
            ]

    def clean_moods(self):
        moods = self.cleaned_data["moods"]
        if len(moods) > 3:
            raise forms.ValidationError("Μπορείς να επιλέξεις το πολύ 3 διαθέσεις.")
        if len(set(moods)) != len(moods):
            raise forms.ValidationError("Κάθε διάθεση επιλέγεται μία μόνο φορά.")
        return moods

    def save(self, commit=True):
        entry = super().save(commit=False)
        moods = self.cleaned_data["moods"]
        entry.mood = moods[0]
        entry.additional_moods = moods[1:]
        if commit:
            entry.save()
            self.save_m2m()
        return entry

@login_required
def mood_list(request):
    paginator = Paginator(MoodEntry.objects.all(), 30)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "mood/list.html", {
        "entries": page_obj.object_list,
        "page_obj": page_obj,
    })


@login_required
def mood_create(request):
    if is_readonly_doctor(request.user):
        return HttpResponseForbidden("Μόνο προβολή για ιατρικούς λογαριασμούς.")
    local_now = timezone.localtime()
    form = MoodEntryForm(
        request.POST or None,
        initial={"date": local_now.date(), "time": local_now.strftime("%H:%M")},
    )
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.created_by = request.user
        entry.save()
        messages.success(request, "✅ Η διάθεση του Γιώργη αποθηκεύτηκε.")
        return redirect("mood_list")
    return render(request, "mood/form.html", {
        "form": form, "title": "Νέα καταγραφή διάθεσης",
    })


@login_required
def mood_edit(request, pk):
    if is_readonly_doctor(request.user):
        return HttpResponseForbidden("Μόνο προβολή για ιατρικούς λογαριασμούς.")
    entry = get_object_or_404(MoodEntry, pk=pk)
    form = MoodEntryForm(request.POST or None, instance=entry)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "✅ Η καταγραφή διάθεσης ενημερώθηκε.")
        return redirect("mood_list")
    return render(request, "mood/form.html", {
        "form": form, "title": "Επεξεργασία διάθεσης",
    })


@login_required
def mood_delete(request, pk):
    if is_readonly_doctor(request.user):
        return HttpResponseForbidden("Μόνο προβολή για ιατρικούς λογαριασμούς.")
    entry = get_object_or_404(MoodEntry, pk=pk)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Η καταγραφή διάθεσης διαγράφηκε.")
        return redirect("mood_list")
    return render(request, "mood/delete.html", {"entry": entry})
