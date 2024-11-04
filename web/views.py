from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "web/login.html")


@ensure_csrf_cookie
def register_view(request):
    """Render registration page"""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "web/signup.html")


@login_required
def dashboard_view(request):
    """Render dashboard page"""
    return render(request, "web/dashboard.html")
