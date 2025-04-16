"""
URL configuration for quizpy_config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include # Make sure include is imported

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('', include('core.urls')), # Include core app's URLs at the root
    path('', include('quiz.urls')),
    path('', include('teacher_interface.urls')), # includes '/teacher/dashboard/'
    path('', include('student_interface.urls')), # Add student UI urls (includes /quiz/start/)

    # --- Refined URL Structure Suggestion ---
    # path('admin/', admin.site.urls),
    # path('auth/', include('authentication.urls')), # Login/logout specific
    # path('teacher/', include('teacher_interface.urls')), # Teacher UI pages under /teacher/
    # path('student/', include('student_interface.urls')), # Student UI pages under /student/ (e.g., /student/start/)
    # path('quiz/', include('quiz.urls')), # Quiz taking flow under /quiz/ (e.g., /quiz/take/<id>) - Requires moving API?
    # path('api/', include('quiz.api_urls')), # Separate API urls under /api/
    # path('', include('core.urls')), # Homepage etc.
    # --- Decide on final URL structure based on clarity ---
]