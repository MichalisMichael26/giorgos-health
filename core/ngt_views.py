"""Parent-facing NG tube guide and auditable notes. Never prescribe or automate feeding."""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone

from .access import is_readonly_doctor
from .models import NasogastricTubeEvent, NasogastricTubePlan
from .views import get_child_profile


class NasogastricTubePlanForm(forms.ModelForm):
    class Meta:
        model = NasogastricTubePlan
        fields = [
            "status", "nostril", "tube_size", "external_mark_cm",
            "placed_on", "next_review_on", "trained_carers", "checking_instructions",
            "tube_feed_instructions", "flush_instructions", "medication_instructions",
            "backup_plan", "contact_instructions", "order_source",
        ]
        widgets = {
            "placed_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "next_review_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "trained_carers": forms.Textarea(attrs={"rows": 2}),
            "checking_instructions": forms.Textarea(attrs={"rows": 3}),
            "tube_feed_instructions": forms.Textarea(attrs={"rows": 3}),
            "flush_instructions": forms.Textarea(attrs={"rows": 2}),
            "medication_instructions": forms.Textarea(attrs={"rows": 2}),
            "backup_plan": forms.Textarea(attrs={"rows": 3}),
            "contact_instructions": forms.Textarea(attrs={"rows": 2}),
        }

    # A parent's description of the tube/status can be saved even if the
    # medical order source is not yet available. The UI must mark such plans
    # as unverified, never as clinician-approved instructions.


class NasogastricTubeEventForm(forms.ModelForm):
    class Meta:
        model = NasogastricTubeEvent
        fields = [
            "occurred_at", "event_type", "position_status",
            "gastric_ph", "external_mark_cm", "volume_ml", "notes",
        ]
        widgets = {
            "occurred_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "notes": forms.Textarea(attrs={"rows": 2}),
            "gastric_ph": forms.NumberInput(attrs={"step": "0.1", "min": "0", "max": "14"}),
            "external_mark_cm": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "volume_ml": forms.NumberInput(attrs={"min": "0", "max": "2000"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["occurred_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]
        if not self.is_bound:
            self.initial["occurred_at"] = timezone.localtime().strftime("%Y-%m-%dT%H:%M")

    def clean_gastric_ph(self):
        value = self.cleaned_data.get("gastric_ph")
        if value is not None and not (0 <= value <= 14):
            raise forms.ValidationError("Η τιμή pH πρέπει να είναι μεταξύ 0 και 14.")
        return value


@login_required
def nasogastric_tube(request):
    profile = get_child_profile()
    existing = NasogastricTubePlan.objects.filter(child=profile).first()
    plan = existing or NasogastricTubePlan(child=profile)
    can_edit = not is_readonly_doctor(request.user)
    plan_form = NasogastricTubePlanForm(instance=plan)
    event_form = NasogastricTubeEventForm()

    if request.method == "POST":
        if not can_edit:
            return HttpResponseForbidden("Οι ιατρικοί λογαριασμοί έχουν μόνο προβολή.")
        action = request.POST.get("action")
        if action == "save_plan":
            plan_form = NasogastricTubePlanForm(request.POST, instance=plan)
            if plan_form.is_valid():
                updated_plan = plan_form.save(commit=False)
                updated_plan.child = profile
                updated_plan.updated_by = request.user
                updated_plan.save()
                if updated_plan.order_source:
                    messages.success(request, "Το πλάνο ρινογαστρικού αποθηκεύτηκε στη βάση δεδομένων.")
                else:
                    messages.success(
                        request,
                        "Τα στοιχεία του ρινογαστρικού αποθηκεύτηκαν στη βάση ως μη επικυρωμένο προσχέδιο. "
                        "Δεν αποτελούν εγκεκριμένες ιατρικές οδηγίες.",
                    )
                return redirect("nasogastric_tube")
            messages.error(request, "Το πλάνο ΔΕΝ αποθηκεύτηκε. Διόρθωσε τα πεδία που σημειώνονται παρακάτω.")
        elif action == "add_event":
            event_form = NasogastricTubeEventForm(request.POST)
            if event_form.is_valid():
                event = event_form.save(commit=False)
                event.child = profile
                event.recorded_by = request.user
                event.save()
                messages.success(request, "Η καταγραφή αποθηκεύτηκε στη βάση δεδομένων και εμφανίζεται στο ιστορικό.")
                return redirect("nasogastric_tube")
            messages.error(request, "Η καταγραφή ΔΕΝ αποθηκεύτηκε. Διόρθωσε τα πεδία που σημειώνονται παρακάτω.")
        else:
            return HttpResponseBadRequest("Μη έγκυρη ενέργεια.")

    return render(request, "health/nasogastric_tube.html", {
        "plan": existing,
        "plan_form": plan_form,
        "event_form": event_form,
        "events": NasogastricTubeEvent.objects.filter(child=profile).select_related("recorded_by")[:30],
        "can_edit": can_edit,
    })
