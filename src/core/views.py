from django.shortcuts import render
# src/core/views.py
from django.http import HttpResponse

def index(request):
    """A simple view to confirm the app is working."""
    return HttpResponse("Hello, QuizPy Backend (Django)!")
# Create your views here.
