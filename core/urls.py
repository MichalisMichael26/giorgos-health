from django.urls import path
from . import views, advanced_views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("more/", views.more, name="more"),
    path("profile/", views.child_profile_edit, name="child_profile_edit"),
    path("analytics/", views.analytics, name="analytics"),

    path("history/", views.history, name="history"),
    path("history/report/", views.history_report_preview, name="history_report_preview"),
    path("history/pdf/", views.history_pdf, name="history_pdf"),
    path("report/24h/", views.report_24h_preview, name="report_24h_preview"),
    path("report/24h/pdf/", views.report_24h_pdf, name="report_24h_pdf"),

    path("meals/", views.meal_list, name="meal_list"),
    path("meals/new/", views.meal_create, name="meal_create"),
    path("meals/<int:pk>/edit/", views.meal_edit, name="meal_edit"),
    path("meals/<int:pk>/delete/", views.meal_delete, name="meal_delete"),

    path("glucose/", views.glucose_list, name="glucose_list"),
    path("glucose/new/", views.glucose_create, name="glucose_create"),
    path("glucose/<int:pk>/edit/", views.glucose_edit, name="glucose_edit"),
    path("glucose/<int:pk>/delete/", views.glucose_delete, name="glucose_delete"),

    path("growth/", views.growth_list, name="growth_list"),
    path("growth/new/", views.growth_create, name="growth_create"),
    path("growth/<int:pk>/edit/", views.growth_edit, name="growth_edit"),
    path("growth/<int:pk>/delete/", views.growth_delete, name="growth_delete"),
    path("growth/percentiles/", advanced_views.growth_percentiles, name="growth_percentiles"),

    path("medications/", views.medication_list, name="medication_list"),
    path("medications/new/", views.medication_create, name="medication_create"),
    path("medications/<int:pk>/edit/", views.medication_edit, name="medication_edit"),
    path("medications/<int:pk>/delete/", views.medication_delete, name="medication_delete"),

    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/new/", views.appointment_create, name="appointment_create"),
    path("appointments/<int:pk>/edit/", views.appointment_edit, name="appointment_edit"),
    path("appointments/<int:pk>/delete/", views.appointment_delete, name="appointment_delete"),

    path("documents/", advanced_views.document_list, name="document_list"),
    path("documents/new/", advanced_views.document_create, name="document_create"),
    path("documents/<int:pk>/edit/", advanced_views.document_edit, name="document_edit"),
    path("documents/<int:pk>/view/", advanced_views.document_view, name="document_view"),
    path("documents/<int:pk>/download/", advanced_views.document_download, name="document_download"),
    path("documents/<int:pk>/delete/", advanced_views.document_delete, name="document_delete"),

    path("vaccines/", advanced_views.vaccine_list, name="vaccine_list"),
    path("vaccines/new/", advanced_views.vaccine_create, name="vaccine_create"),
    path("vaccines/<int:pk>/edit/", advanced_views.vaccine_edit, name="vaccine_edit"),
    path("vaccines/<int:pk>/delete/", advanced_views.vaccine_delete, name="vaccine_delete"),

    path("symptoms/", advanced_views.symptom_list, name="symptom_list"),
    path("symptoms/new/", advanced_views.symptom_create, name="symptom_create"),
    path("symptoms/<int:pk>/edit/", advanced_views.symptom_edit, name="symptom_edit"),
    path("symptoms/<int:pk>/delete/", advanced_views.symptom_delete, name="symptom_delete"),

    path("diapers/", advanced_views.diaper_list, name="diaper_list"),
    path("diapers/new/", advanced_views.diaper_create, name="diaper_create"),
    path("diapers/<int:pk>/edit/", advanced_views.diaper_edit, name="diaper_edit"),
    path("diapers/<int:pk>/delete/", advanced_views.diaper_delete, name="diaper_delete"),

    path("feeding-performance/", advanced_views.feeding_performance, name="feeding_performance"),
    path("doctor-view/", advanced_views.doctor_view, name="doctor_view"),
    path("emergency-card/", advanced_views.emergency_card, name="emergency_card"),
    path("emergency-card/edit/", advanced_views.emergency_edit, name="emergency_edit"),
    path("audit-log/", advanced_views.audit_log, name="audit_log"),

    path("exports/", advanced_views.export_center, name="export_center"),
    path("exports/excel/", advanced_views.export_excel, name="export_excel"),
    path("exports/zip/", advanced_views.export_zip, name="export_zip"),
    path("exports/pdf/", advanced_views.export_pdf, name="export_pdf"),
]
