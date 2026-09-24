from django.urls import path
from . import views, advanced_views, mega_views, push_views, native_alarm_views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("more/", views.more, name="more"),
    path("health/", views.more, name="health_hub"),
    path("health/allergies/", views.allergies_view, name="allergies_view"),
    path("profile/", views.child_profile_edit, name="child_profile_edit"),
    path(
        "feeding-schedule/settings/",
        views.feeding_schedule_settings,
        name="feeding_schedule_settings",
    ),
    path("analytics/", views.analytics, name="analytics"),

    path("history/", views.history, name="history"),
    path("history/report/", views.history_report_preview, name="history_report_preview"),
    path("history/pdf/", views.history_pdf, name="history_pdf"),
    path("report/48h/print/", views.report_48h_print, name="report_48h_print"),
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
    path(
        "medications/plan/<int:pk>/log-now/",
        views.medication_plan_log_now,
        name="medication_plan_log_now",
    ),
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
    path("diapers/<int:pk>/view/", advanced_views.diaper_detail, name="diaper_detail"),
    path("diapers/new/", advanced_views.diaper_create, name="diaper_create"),
    path("diapers/<int:pk>/edit/", advanced_views.diaper_edit, name="diaper_edit"),
    path("diapers/<int:pk>/delete/", advanced_views.diaper_delete, name="diaper_delete"),

    path("feeding-performance/", advanced_views.feeding_performance, name="feeding_performance"),
    path("doctor-view/", advanced_views.doctor_view, name="doctor_view"),
    path("emergency-card/", advanced_views.emergency_card, name="emergency_card"),
    path("emergency-card/edit/", advanced_views.emergency_edit, name="emergency_edit"),
    path("audit-log/", advanced_views.audit_log, name="audit_log"),

    path("checker/", advanced_views.safety_checker, name="safety_checker"),
    path("checker/rules/", advanced_views.safety_rule_list, name="safety_rule_list"),
    path("checker/rules/new/", advanced_views.safety_rule_create, name="safety_rule_create"),
    path("checker/rules/<int:pk>/edit/", advanced_views.safety_rule_edit, name="safety_rule_edit"),
    path("checker/rules/<int:pk>/delete/", advanced_views.safety_rule_delete, name="safety_rule_delete"),
    path("checker/records/new/", advanced_views.product_record_create, name="product_record_create"),
    path("checker/records/<int:pk>/edit/", advanced_views.product_record_edit, name="product_record_edit"),
    path("checker/records/<int:pk>/delete/", advanced_views.product_record_delete, name="product_record_delete"),


    # Mobile scanner / evaluated products
    path("scanner/", mega_views.product_scanner, name="product_scanner"),
    path("scanner/check/", mega_views.scanner_check, name="scanner_check"),
    path("scanner/barcode/<str:code>/", mega_views.barcode_lookup, name="barcode_lookup"),
    path(
        "scanner/barcode/<str:code>/ingredients-image/",
        mega_views.barcode_ingredients_image,
        name="barcode_ingredients_image",
    ),
    path("products/reviewed/", mega_views.reviewed_products, name="reviewed_products"),
    path("products/<int:pk>/label-photo/", mega_views.product_label_photo, name="product_label_photo"),

    # Structured laboratory results
    path("labs/", mega_views.lab_list, name="lab_list"),
    path("labs/new/", mega_views.lab_create, name="lab_create"),
    path("labs/<int:pk>/edit/", mega_views.lab_edit, name="lab_edit"),
    path("labs/<int:pk>/delete/", mega_views.lab_delete, name="lab_delete"),
    path("labs/chart/", mega_views.lab_chart, name="lab_chart"),

    # Native Android alarm companion
    path("native/alarm-schedule/", native_alarm_views.native_alarm_schedule, name="native_alarm_schedule"),

    # Mobile push notifications
    path("service-worker.js", push_views.service_worker, name="service_worker"),
    path("push/config/", push_views.push_public_config, name="push_public_config"),
    path("push/subscribe/", push_views.push_subscribe, name="push_subscribe"),
    path("push/unsubscribe/", push_views.push_unsubscribe, name="push_unsubscribe"),
    path("push/test/", push_views.push_test, name="push_test"),

    # Reminders
    path("reminders/", mega_views.reminder_list, name="reminder_list"),
    path("reminders/new/", mega_views.reminder_create, name="reminder_create"),
    path("reminders/<int:pk>/edit/", mega_views.reminder_edit, name="reminder_edit"),
    path("reminders/<int:pk>/done/", mega_views.reminder_done, name="reminder_done"),
    path("reminders/<int:pk>/delete/", mega_views.reminder_delete, name="reminder_delete"),

    # Photos
    path("symptoms/<int:pk>/photo/", mega_views.symptom_photo, name="symptom_photo"),
    path("diapers/<int:pk>/photo/", mega_views.diaper_photo, name="diaper_photo"),

    # Questions / doctor visit
    path("doctor-questions/", mega_views.doctor_questions, name="doctor_questions"),
    path("doctor-questions/new/", mega_views.doctor_question_create, name="doctor_question_create"),
    path("doctor-questions/<int:pk>/answer/", mega_views.doctor_question_answer, name="doctor_question_answer"),
    path("doctor-questions/<int:pk>/delete/", mega_views.doctor_question_delete, name="doctor_question_delete"),
    path("doctor-visit/", mega_views.doctor_visit, name="doctor_visit"),

    # Hospital mode
    path("hospital/", mega_views.hospital_mode, name="hospital_mode"),

    # Emergency QR
    path("emergency-card/share/settings/", mega_views.emergency_share_settings, name="emergency_share_settings"),
    path("emergency-card/share/rotate/", mega_views.emergency_share_rotate, name="emergency_share_rotate"),
    path("e/<uuid:token>/", mega_views.emergency_public, name="emergency_public"),

    # Global search
    path("search/", mega_views.global_search, name="global_search"),

    # Daily summary
    path("summary/daily/", mega_views.daily_summary, name="daily_summary"),
    path("summary/daily/pdf/", mega_views.daily_summary_pdf, name="daily_summary_pdf"),

    # User roles
    path("users/access/", mega_views.user_access_list, name="user_access_list"),
    path("users/access-log/", mega_views.user_access_log, name="user_access_log"),
    path("users/access/new/", mega_views.user_access_create, name="user_access_create"),
    path("users/access/<int:pk>/edit/", mega_views.user_access_edit, name="user_access_edit"),

    # Cloud backup status / manual run
    path("backup/status/", mega_views.backup_status, name="backup_status"),
    path("backup/cloud-now/", mega_views.cloud_backup_now, name="cloud_backup_now"),

    path("exports/", advanced_views.export_center, name="export_center"),
    path("exports/excel/", advanced_views.export_excel, name="export_excel"),
    path("exports/zip/", advanced_views.export_zip, name="export_zip"),
    path("exports/pdf/", advanced_views.export_pdf, name="export_pdf"),
]
