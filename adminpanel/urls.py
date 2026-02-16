from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('lost-items/', views.view_lost_items, name='lost_items'),
    path('found-items/', views.view_found_items, name='found_items'),
    path('matches/', views.matches_list, name='matches_list'),
    path('recovered-items/', views.recovered_items, name='recovered_items'),
    path('match-action/<str:match_id>/', views.match_action_form, name='match_action_form'),  # Updated
    path('logout/', views.admin_logout, name='admin_logout'),
]
