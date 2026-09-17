from django.contrib import admin
from .models import GlucoseReading, GrowthMeasurement, MealEntry


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
