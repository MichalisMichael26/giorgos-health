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
    class Meta:
        model = MoodEntry
        fields = ("date", "time", "mood", "notes")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "mood": forms.RadioSelect,
            "notes": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Προαιρετικά: τι παρατήρησες, πριν/μετά τη σίτιση ή τον ρινογαστρικό;",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].input_formats = ["%Y-%m-%d"]
        self.fields["time"].input_formats = ["%H:%M", "%H:%M:%S"]


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
