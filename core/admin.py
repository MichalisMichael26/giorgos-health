from django.contrib import admin
from .models import (
    GlucoseReading,
    GrowthMeasurement,
    MealEntry,
    MedicationEntry,
    MedicalAppointment,
)


@admin.register(MealEntry)
class MealEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "scheduled_time", "actual_time", "consumed_ml", "status")
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


@admin.register(MedicalAppointment)
class MedicalAppointmentAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "purpose", "doctor", "clinic", "status")
    list_filter = ("status", "date")
    search_fields = ("purpose", "doctor", "clinic", "notes")
