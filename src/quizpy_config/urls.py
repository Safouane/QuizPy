# quizpy_config/urls.py
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# Import dynamically calculated media settings from views
try:
    from quiz.views import MEDIA_URL_ROOT, MEDIA_ROOT_DIR
except ImportError:
    MEDIA_URL_ROOT, MEDIA_ROOT_DIR = None, None

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("authentication.urls")),
    path("teacher/", include("teacher_interface.urls")),
    path("", include("quiz.urls")),  # Includes non-media API endpoints
    path("", include("core.urls")),
    path("", include("student_interface.urls")),
]

# --- Add Media serving for DEVELOPMENT ONLY ---
if settings.DEBUG and MEDIA_URL_ROOT and MEDIA_ROOT_DIR:
    print(
        f"DEBUG [Urls]: Adding media static route: URL='{MEDIA_URL_ROOT}', Root='{MEDIA_ROOT_DIR}'"
    )
    urlpatterns += static(MEDIA_URL_ROOT, document_root=MEDIA_ROOT_DIR)
# --- Refined URL Structure Suggestion ---
# path('admin/', admin.site.urls),
# path('auth/', include('authentication.urls')), # Login/logout specific
# path('teacher/', include('teacher_interface.urls')), # Teacher UI pages under /teacher/
# path('student/', include('student_interface.urls')), # Student UI pages under /student/ (e.g., /student/start/)
# path('quiz/', include('quiz.urls')), # Quiz taking flow under /quiz/ (e.g., /quiz/take/<id>) - Requires moving API?
# path('api/', include('quiz.api_urls')), # Separate API urls under /api/
# path('', include('core.urls')), # Homepage etc.
# --- Decide on final URL structure based on clarity ---
