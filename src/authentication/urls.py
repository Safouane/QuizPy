from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_page_view, name='login_page'),
    path('api/login/', views.login_view, name='api_login'),
    path('api/logout/', views.logout_view, name='api_logout'),
    path('api/status/', views.check_auth_status, name='api_auth_status'),
]