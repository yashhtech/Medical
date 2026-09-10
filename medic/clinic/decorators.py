from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Patient, Doctor


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get("admin_logged_in"):
            messages.error(request, "Admin access required. Please log in.")
            return redirect("/login/?role=admin")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        patient_id = request.session.get("patient_id")
        if not patient_id:
            messages.error(request, "Patient access required. Please log in.")
            return redirect("/login/?role=patient")
        try:
            request.patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            request.session.flush()
            messages.error(request, "Session expired. Please log in again.")
            return redirect("/login/?role=patient")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        doctor_id = request.session.get("doctor_id")
        if not doctor_id:
            messages.error(request, "Doctor access required. Please log in.")
            return redirect("/login/?role=doctor")
        try:
            request.doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            request.session.flush()
            messages.error(request, "Session expired. Please log in again.")
            return redirect("/login/?role=doctor")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
