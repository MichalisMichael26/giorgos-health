from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("history/", views.history, name="history"),
    path("history/pdf/", views.history_pdf, name="history_pdf"),

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
]
