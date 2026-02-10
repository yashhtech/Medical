"""
URL configuration for medic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path , include
from clinic.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('newsletter_signup/',newsletter_signup, name='newsletter_signup'),
    path('contact/', contact, name='contact'),
    path('contact_view/',contact_view,name="contact_view"),
    path("about/", about, name="about"),
    path('departments/', departments, name='departments'),
    path('insurance/', insurance, name='insurance'),
    path('cardiology',cardiology,name='cardiology'),
    path('neurology',neurology,name='neurology'),
    path('orthopaedics',orthopaedics,name='orthopaedics'),
    path("booking/",booking, name="booking"),
    path("login/",login, name="login"),
    path("new_patient_register/", new_patient_register, name="new_patient_register"),
    path("login/<str:role>/",role_login, name="role_login"),
    path("patient_dashboard/",patient_dashboard, name="patient_dashboard"),
    path(
        "cancel-appointment/<int:id>/",
         cancel_appointment,
        name="cancel_appointment"
    ),
    path('logout_patient/', custom_logout, name='logout_patient'),
    path("doctor_dashboard/",doctor_dashboard, name="doctor_dashboard"),
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin_patients/", admin_patients, name="admin_patients"),

    path("edit_patient/<int:id>/", edit_patient, name="edit_patient"),
    path("delete_patient/<int:id>/", delete_patient, name="delete_patient"),
    path("admin_add_patient/",admin_add_patient,name='admin_add_patient'),
    path("admin_logout/",admin_logout, name="admin_logout"),
  

    # DOCTOR
    path("admin_doctors/",admin_doctors, name="admin_doctors"),
    path("admin_add_doctor/",admin_add_doctor, name="admin_add_doctor"),
    path("save_doctor/",save_doctor, name="save_doctor"),
    path("edit_doctor/<int:id>/",edit_doctor, name="edit_doctor"),
    path("delete_doctor/<int:id>/",delete_doctor, name="delete_doctor"),

    # # MASS MESSAGE
    # path("admin/messages/", views.mass_message, name="mass_message"),

    # # QUERIES
    # path("admin/queries/patient/", views.patient_queries, name="patient_queries"),
    # path("admin/queries/doctor/", views.doctor_queries, name="doctor_queries"),


    # urls.py

    path('patient/medical-reports/',medical_reports, name='medical_reports'),

    path('patient/video-call/',video_call, name='video_call'),
    path('patient/notifications/',notifications, name='notifications'),
    path('patient/progress/',medical_progress, name='medical_progress'),
    path('patient/health/',medical_health, name='medical_health'),


]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)