# src/core/urls.py
from django.urls import path
from . import views # Import views from the current directory

app_name = 'core' # Namespace for URL reversing (optional but good practice)

urlpatterns = [
    # Map the root URL of this app ('') to the index view
    path('', views.index, name='index'),
]