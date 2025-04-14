from django.urls import path
from . import views # Import views from the current directory (core app)

app_name = 'core' # Optional: Add app namespace

urlpatterns = [
    # path('', views.hello_world, name='hello'), # Remove or comment out old view
    path('', views.index_view, name='index'), # Add path for the new index view
]