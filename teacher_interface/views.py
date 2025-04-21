# src/teacher_interface/views.py
"""
Views for the Teacher Interface section of the QuizPy application.
Handles displaying dashboards, lists, forms for managing quizzes and questions,
and viewing results. Access is restricted to authenticated staff users.
"""

import traceback  # For logging errors
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required  # Standard Django decorator
from authentication.decorators import (
    teacher_required,
)  # Custom decorator checking is_staff
from core.json_storage import load_data  # Utility to load data from JSON

# --- Dashboard ---


@teacher_required  # Use the decorator that checks login AND is_staff, redirects to login if fails
def dashboard_view(request):
    """
    Renders the main dashboard page for logged-in teachers.
    Includes summary data like active quiz count and total question count.
    """
    active_quizzes_count = "Error"  # Default in case of error
    total_questions_count = "Error"  # Default in case of error
    recent_attempts_count = "N/A"  # Placeholder for future

    try:
        # Load data from JSON file using the core utility
        print("DEBUG [Dashboard View]: Loading data for summary...")
        data = load_data()  # Call the function from json_storage

        # Calculate Active Quizzes
        # Count quizzes where 'archived' is explicitly False or missing
        active_quizzes_count = sum(
            1 for quiz in data.get("quizzes", []) if not quiz.get("archived", False)
        )

        # Calculate Total Questions
        total_questions_count = len(data.get("questions", []))
        print(
            f"DEBUG [Dashboard View]: Found Counts - Active Quizzes: {active_quizzes_count}, Total Questions: {total_questions_count}"
        )

    except Exception as e:
        # Log the error if data loading/processing fails
        print(f"ERROR [Dashboard View]: Error loading data for dashboard summary: {e}")
        traceback.print_exc()
        # Keep default 'Error' values for display

    context = {
        "view_name": "dashboard",  # Optional: For highlighting active nav item
        "username": request.user.username,
        "active_quizzes_count": active_quizzes_count,
        "total_questions_count": total_questions_count,
        "recent_attempts_count": recent_attempts_count,
    }
    return render(request, "teacher_interface/dashboard.html", context)


# --- Quiz Management ---


@teacher_required
def quiz_list_view(request):
    """
    Renders the page that displays the list of quizzes.
    The actual quiz data is fetched asynchronously via JavaScript calling API-1.
    """
    print("DEBUG [Quiz List View]: Rendering quiz list page.")
    context = {"view_name": "quiz_list", "username": request.user.username}
    return render(request, "teacher_interface/quiz_list.html", context)


@teacher_required
def quiz_edit_view(request, quiz_id=None):
    """
    Renders the quiz creation/editing form page.
    - If quiz_id is None: Renders empty form for creating a new quiz.
    - If quiz_id is provided: Renders form for editing an existing quiz.
      Actual quiz data loading for editing is handled by JavaScript (fetchQuizDetails).
      Passes existing categories to the template for the modal filter dropdown.
    """
    is_editing = quiz_id is not None
    print(
        f"DEBUG [Quiz Edit View]: Rendering quiz edit form. Editing: {is_editing}, Quiz ID: {quiz_id}"
    )

    context = {
        "view_name": "quiz_edit",
        "quiz_id": quiz_id,  # Pass UUID object or None to template
        "form_title": "Edit Quiz" if is_editing else "Create New Quiz",
    }

    # Fetch existing categories to populate the "Add from Bank" modal filter
    try:
        print("DEBUG [Quiz Edit View]: Loading categories for modal filter...")
        all_data = load_data()
        # Use a set comprehension for uniqueness, handle potential None/empty categories
        categories = sorted(
            list(
                set(
                    q.get(
                        "category", ""
                    ).strip()  # Get category, default to empty, strip whitespace
                    for q in all_data.get("questions", [])
                    if q.get(
                        "category", ""
                    ).strip()  # Only include if category exists and is not just whitespace
                )
            )
        )
        # Add 'Uncategorized' if any questions truly lack a category or have it empty/None,
        # but only if 'Uncategorized' isn't already present from data.
        has_uncategorized_implicit = any(
            not q.get("category", "").strip() for q in all_data.get("questions", [])
        )
        if has_uncategorized_implicit and "Uncategorized" not in categories:
            categories.insert(0, "Uncategorized")  # Add at beginning

        print(f"DEBUG [Quiz Edit View]: Found categories: {categories}")
    except Exception as e:
        print(f"ERROR [Quiz Edit View]: Error loading categories for filter: {e}")
        traceback.print_exc()
        categories = []  # Default to empty list on error

    context["existing_categories"] = categories  # Add categories to context

    return render(request, "teacher_interface/quiz_edit_form.html", context)


# --- Question Management ---


@teacher_required
def question_bank_view(request):
    """
    Renders the Question Bank page.
    Questions are loaded asynchronously via JavaScript calling API-2.
    Passes existing categories for the filter dropdown.
    """
    print("DEBUG [Question Bank View]: Rendering question bank page.")
    context = {"view_name": "question_bank", "username": request.user.username}
    # Fetch existing categories to populate the filter dropdown
    try:
        print("DEBUG [Question Bank View]: Loading categories for filter...")
        all_data = load_data()
        categories = sorted(
            list(
                set(
                    q.get("category", "").strip()
                    for q in all_data.get("questions", [])
                    if q.get("category", "").strip()
                )
            )
        )
        has_uncategorized_implicit = any(
            not q.get("category", "").strip() for q in all_data.get("questions", [])
        )
        if has_uncategorized_implicit and "Uncategorized" not in categories:
            categories.insert(0, "Uncategorized")

        print(f"DEBUG [Question Bank View]: Found categories: {categories}")
    except Exception as e:
        print(f"ERROR [Question Bank View]: Error loading categories for filter: {e}")
        traceback.print_exc()
        categories = []

    context["existing_categories"] = categories  # Add categories to context

    return render(request, "teacher_interface/question_bank.html", context)


@teacher_required
def question_edit_view(request, question_id=None):
    """
    Renders the question creation/editing form page.
    - If question_id is None: Renders empty form for creating a new question.
    - If question_id is provided: Renders form for editing an existing question.
      Actual question data loading for editing is handled by JavaScript.
    """
    is_editing = question_id is not None
    print(
        f"DEBUG [Question Edit View]: Rendering question edit form. Editing: {is_editing}, Question ID: {question_id}"
    )

    # Get originating quiz_id from query param if present (used by JS on save)
    originating_quiz_id = request.GET.get("quiz_id", None)

    context = {
        "view_name": "question_edit",
        "question_id": question_id,  # Pass UUID object or None
        "originating_quiz_id": originating_quiz_id,  # Pass for potential JS use
        "form_title": "Edit Question" if is_editing else "Create New Question",
        # Optional: Pass existing categories for suggestion/datalist?
        # 'existing_categories': categories # (fetch categories like in bank view if needed)
    }
    return render(request, "teacher_interface/question_edit_form.html", context)


# --- Results Viewing ---


@teacher_required
def results_list_view(request):
    """
    Renders the main page for viewing quiz results.
    Passes a list of quizzes for the selection dropdown.
    Attempt data is loaded asynchronously via JavaScript calling API.
    """
    print("DEBUG [Results List View]: Rendering results list page.")
    quizzes_for_select = []
    try:
        print("DEBUG [Results List View]: Loading quiz list for dropdown...")
        all_data = load_data()
        # Get quizzes, potentially filter out archived or add status indicator?
        # For now, show all quizzes.
        quizzes_for_select = sorted(
            [
                {
                    "id": q.get("id"),
                    "title": q.get("title", "Untitled Quiz")
                    + (" (Archived)" if q.get("archived") else ""),
                }
                for q in all_data.get("quizzes", [])
                if q.get("id")  # Ensure quiz has an ID
            ],
            key=lambda x: x["title"],  # Sort by title
        )
        print(
            f"DEBUG [Results List View]: Found {len(quizzes_for_select)} quizzes for dropdown."
        )
    except Exception as e:
        print(f"ERROR [Results List View]: Error loading quiz list: {e}")
        traceback.print_exc()
        # Keep quizzes_for_select as empty list

    context = {
        "view_name": "results_list",
        "quizzes": quizzes_for_select,  # Pass the list of quizzes for the dropdown
    }
    return render(request, "teacher_interface/results_list.html", context)
