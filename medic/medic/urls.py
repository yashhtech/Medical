"""
URL configuration for Medical Clinic project.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from clinic.views import (
    home, contact, about, departments, insurance,
    cardiology, neurology, orthopaedics, booking,
    login, role_login, new_patient_register,
    patient_dashboard, payment_verify, cancel_appointment, download_invoice,
    custom_logout, doctor_logout, doctor_dashboard,
    admin_dashboard, admin_patients, edit_patient, delete_patient,
    admin_add_patient, admin_logout,
    admin_doctors, admin_add_doctor, save_doctor, edit_doctor, delete_doctor,
    admin_queries,
    newsletter_signup, contact_view,
    medical_reports, video_call, notifications, medical_progress, medical_health,
)

urlpatterns = [
    # Django built-in admin
    path('admin/', admin.site.urls),

    # ── Public Pages ──────────────────────────────────────────────────────
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('departments/', departments, name='departments'),
    path('insurance/', insurance, name='insurance'),
    path('contact/', contact, name='contact'),
    path('contact_view/', contact_view, name='contact_view'),
    path('newsletter_signup/', newsletter_signup, name='newsletter_signup'),

    # ── Department Detail Pages ───────────────────────────────────────────
    path('cardiology/', cardiology, name='cardiology'),
    path('neurology/', neurology, name='neurology'),
    path('orthopaedics/', orthopaedics, name='orthopaedics'),
    path('booking/', booking, name='booking'),

    # ── Authentication ────────────────────────────────────────────────────
    path('login/', login, name='login'),
    path('login/<str:role>/', role_login, name='role_login'),
    path('new_patient_register/', new_patient_register, name='new_patient_register'),
    path('logout/', custom_logout, name='logout_patient'),
    path('logout_doctor/', doctor_logout, name='logout_doctor'),

    # ── Patient Dashboard ─────────────────────────────────────────────────
    path('patient_dashboard/', patient_dashboard, name='patient_dashboard'),
    path('payment-verify/', payment_verify, name='payment_verify'),
    path('cancel-appointment/<int:id>/', cancel_appointment, name='cancel_appointment'),
    path('invoice/<int:appointment_id>/', download_invoice, name='download_invoice'),

    # Patient subpages
    path('patient/medical-reports/', medical_reports, name='medical_reports'),
    path('patient/video-call/', video_call, name='video_call'),
    path('patient/notifications/', notifications, name='notifications'),
    path('patient/progress/', medical_progress, name='medical_progress'),
    path('patient/health/', medical_health, name='medical_health'),

    # ── Doctor Dashboard ──────────────────────────────────────────────────
    path('doctor_dashboard/', doctor_dashboard, name='doctor_dashboard'),

    # ── Admin Portal ──────────────────────────────────────────────────────
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/patients/', admin_patients, name='admin_patients'),
    path('admin/patients/add/', admin_add_patient, name='admin_add_patient'),
    path('admin/patients/edit/<int:id>/', edit_patient, name='edit_patient'),
    path('admin/patients/delete/<int:id>/', delete_patient, name='delete_patient'),
    path('admin/logout/', admin_logout, name='admin_logout'),
    path('admin/queries/', admin_queries, name='admin_queries'),

    path('admin/doctors/', admin_doctors, name='admin_doctors'),
    path('admin/doctors/add/', admin_add_doctor, name='admin_add_doctor'),
    path('admin/doctors/save/', save_doctor, name='save_doctor'),
    path('admin/doctors/edit/<int:id>/', edit_doctor, name='edit_doctor'),
    path('admin/doctors/delete/<int:id>/', delete_doctor, name='delete_doctor'),

    # Legacy URL aliases for backward compatibility
    path('admin_patients/', admin_patients, name='admin_patients_legacy'),
    path('admin_add_patient/', admin_add_patient, name='admin_add_patient_legacy'),
    path('edit_patient/<int:id>/', edit_patient, name='edit_patient_legacy'),
    path('delete_patient/<int:id>/', delete_patient, name='delete_patient_legacy'),
    path('admin_logout/', admin_logout, name='admin_logout_legacy'),
    path('admin_doctors/', admin_doctors, name='admin_doctors_legacy'),
    path('admin_add_doctor/', admin_add_doctor, name='admin_add_doctor_legacy'),
    path('save_doctor/', save_doctor, name='save_doctor_legacy'),
    path('edit_doctor/<int:id>/', edit_doctor, name='edit_doctor_legacy'),
    path('delete_doctor/<int:id>/', delete_doctor, name='delete_doctor_legacy'),
]

# Serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)