from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("more/", views.more, name="more"),
    path("analytics/", views.analytics, name="analytics"),

    path("history/", views.history, name="history"),
    path("history/pdf/", views.history_pdf, name="history_pdf"),
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

    path("medications/", views.medication_list, name="medication_list"),
    path("medications/new/", views.medication_create, name="medication_create"),
    path("medications/<int:pk>/edit/", views.medication_edit, name="medication_edit"),
    path("medications/<int:pk>/delete/", views.medication_delete, name="medication_delete"),

    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/new/", views.appointment_create, name="appointment_create"),
    path("appointments/<int:pk>/edit/", views.appointment_edit, name="appointment_edit"),
    path("appointments/<int:pk>/delete/", views.appointment_delete, name="appointment_delete"),
]
