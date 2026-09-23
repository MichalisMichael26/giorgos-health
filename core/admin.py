from django.contrib import admin

from .models import (
    AuditLog,
    ChildProfile,
    DiaperEntry,
    GlucoseReading,
    GrowthMeasurement,
    MealEntry,
    MedicalAppointment,
    MedicalDocument,
    MedicationEntry,
    MedicationPlan,
    SymptomEntry,
    VaccineEntry,
    SafetyRule,
    ProductSafetyRecord,
    LabResult,
    HealthReminder,
    DoctorQuestion,
    UserAccessProfile,
    BackupRun,
)


@admin.register(MealEntry)
class MealEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "scheduled_time", "actual_time", "finished_time", "consumed_ml", "status")
    list_filter = ("date", "status")
    search_fields = ("formula", "supplement", "notes")


@admin.register(GlucoseReading)
class GlucoseReadingAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "value", "context")
    list_filter = ("date", "context")


@admin.register(GrowthMeasurement)
class GrowthMeasurementAdmin(admin.ModelAdmin):
    list_display = ("date", "weight_kg", "length_cm", "head_cm")


@admin.register(MedicationEntry)
class MedicationEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "name", "dose", "unit")
    list_filter = ("date", "unit")
    search_fields = ("name", "notes")


@admin.register(MedicationPlan)
class MedicationPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "dose",
        "unit",
        "frequency",
        "unit_confirmation_required",
        "active",
    )
    list_filter = ("active", "unit_confirmation_required", "unit")
    search_fields = ("name", "frequency", "notes")


@admin.register(MedicalAppointment)
class MedicalAppointmentAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "purpose", "doctor", "clinic", "status")
    list_filter = ("status", "date")
    search_fields = ("purpose", "doctor", "clinic", "notes")
    ordering = ("-date", "-time")


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name", "birth_date", "updated_at")
    readonly_fields = ("birth_date",)


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    list_display = ("date", "title", "category", "original_filename", "file_size")
    list_filter = ("category", "date")
    search_fields = ("title", "original_filename", "notes")
    exclude = ("data",)


@admin.register(VaccineEntry)
class VaccineEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "name", "dose_label", "next_date")
    list_filter = ("date",)
    search_fields = ("name", "dose_label", "notes")


@admin.register(SymptomEntry)
class SymptomEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "symptom", "severity", "relation_to_feed")
    list_filter = ("severity", "relation_to_feed", "date")
    search_fields = ("symptom", "notes")


@admin.register(DiaperEntry)
class DiaperEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "kind", "stool_color", "stool_consistency")
    list_filter = ("kind", "date")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "model_name", "object_repr")
    list_filter = ("action", "model_name")
    search_fields = ("object_repr", "object_id")
    readonly_fields = ("timestamp", "user", "action", "model_name", "object_id", "object_repr", "changes")



@admin.register(SafetyRule)
class SafetyRuleAdmin(admin.ModelAdmin):
    list_display = ("term", "applies_to", "guidance", "active", "updated_at")
    list_filter = ("applies_to", "guidance", "active")
    search_fields = ("term", "note")


@admin.register(ProductSafetyRecord)
class ProductSafetyRecordAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "decision", "confirmed_by", "reviewed_on")
    list_filter = ("kind", "decision")
    search_fields = ("name", "ingredients", "confirmed_by", "notes")



@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "test_name", "value", "unit", "laboratory")
    list_filter = ("date", "test_name")
    search_fields = ("test_name", "laboratory", "notes")


@admin.register(HealthReminder)
class HealthReminderAdmin(admin.ModelAdmin):
    list_display = (
        "due_at",
        "reminder_type",
        "title",
        "auto_generated",
        "notify_minutes_before",
        "repeat_if_incomplete_minutes",
        "push_notified_at",
        "active",
        "completed",
    )
    list_filter = ("reminder_type", "auto_generated", "active", "completed")


@admin.register(DoctorQuestion)
class DoctorQuestionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "question", "status", "appointment")
    list_filter = ("status",)


@admin.register(UserAccessProfile)
class UserAccessProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "role")
    list_filter = ("role",)


@admin.register(BackupRun)
class BackupRunAdmin(admin.ModelAdmin):
    list_display = ("created_at", "status", "destination", "size_bytes")
    list_filter = ("status",)
