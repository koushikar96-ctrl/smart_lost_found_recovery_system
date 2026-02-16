# items/urls.py
from django.urls import path
from . import views

app_name = "items"

urlpatterns = [
    path("", views.items_home, name="items_home"),
]
