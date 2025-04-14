from django.shortcuts import render
# src/core/views.py
from django.http import HttpResponse

def index_view(request):
    """Renders the main index/landing page."""
    return render(request, 'index.html')
