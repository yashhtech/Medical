from django.shortcuts import render, redirect, get_object_or_404
from .models import Patient,Contact,Doctor,Newsletter,Appointment, ChatMessage, ChatThread
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.core.mail import send_mail
from .utils import send_auto_reply
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Prefetch
import calendar
from datetime import date


def home(request):
    return render(request, 'Nav-tab/index.html')


def contact(request):
    return render(request, 'Nav-tab/contact.html')


def about(request):
    return render(request, "Nav-tab/about.html")

def departments(request):
    return render(request, "Nav-tab/departments.html")

def insurance(request):
    return render(request, 'Nav-tab/insurance.html') 

def cardiology(request):
    return render(request,'Departments/cardiology.html')

def neurology(request):
    return render(request,'Departments/neurology.html')

def orthopaedics(request):
    return render(request,'Departments/orthopaedics.html')

def booking(request):
    return render(request,'Appointment/booking.html')


def login(request):
    role = request.GET.get("role")

    # Save HOME only once
    if "login_entry" not in request.session:
        request.session["login_entry"] = "/"

    context = {
        "role": role,
        "login_entry": request.session.get("login_entry", "/"),
    }

    return render(request, "nav-tab/login.html", context)




def new_patient_register(request):
    if request.method == "POST":

        source = request.POST.get("source")  # admin ya None

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # ❌ password mismatch
        if password != confirm_password:
            messages.error(request, "Passwords do not match")

            if source == "admin":
                return redirect("admin_add_patient")
            else:
                return redirect("/login/?role=new_patient")

        # ❌ email already exists
        if Patient.objects.filter(email=request.POST.get("email")).exists():
            messages.error(request, "Email already registered")

            if source == "admin":
                return redirect("admin_add_patient")
            else:
                return redirect("/login/?role=new_patient")

        # ✅ save patient
        Patient.objects.create(
            salutation=request.POST.get("salutation"),
            name=request.POST.get("name"),
            gender=request.POST.get("gender"),
            age=request.POST.get("age"),
            email=request.POST.get("email"),
            mobile=request.POST.get("mobile"),
            address=request.POST.get("address"),
            image=request.FILES.get("image"),
            password=make_password(password),
        )

        # ✅ success redirect
        if source == "admin":
            messages.success(request, "Patient added successfully")
            return redirect("admin_patients")   # admin dashboard
        else:
            messages.success(request, "Registration successful! Please login.")
            return redirect("login")

    return redirect("login")



def role_login(request, role):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # ================= ADMIN LOGIN =================
        if role == "admin":
            if (
                email == settings.ADMIN_EMAIL
                and password == settings.ADMIN_PASSWORD
            ):
                request.session["admin_logged_in"] = True
                messages.success(request, "Admin login successful")
                return render(request,'admin/admin_dashboard.html')
            else:
                messages.error(request, "Invalid admin credentials")
                return redirect("/login/?role=admin")

        # ================= PATIENT LOGIN =================
        elif role == "patient":
            from .models import Patient
            from django.contrib.auth.hashers import check_password

            try:
                patient = Patient.objects.get(email=email)
                if check_password(password, patient.password):
                    request.session["patient_id"] = patient.id
                    messages.success(request, "Login successful")
                    return redirect("patient_dashboard")
                else:
                    messages.error(request, "Wrong password")

            except Patient.DoesNotExist:
                messages.error(request, "Email not registered")

        # ================= DOCTOR LOGIN =================
        elif role == "doctor":
            from .models import Doctor
            from django.contrib.auth.hashers import check_password

            try:
                doctor = Doctor.objects.get(email=email)
                if check_password(password, doctor.password):
                    request.session["doctor_id"] = doctor.id
                    messages.success(request, "Login successful")
                    return redirect("doctor_dashboard")
                else:
                    messages.error(request, "Wrong password")

            except Doctor.DoesNotExist:
                messages.error(request, "Email not registered")

        else:
            messages.error(request, "Invalid role")

    return redirect("login")



def admin_dashboard(request):
    if not request.session.get("admin_logged_in"):
        return redirect("login")

    return render(request, "admin/admin_dashboard.html", {
        "page": "dashboard"
    })


def admin_logout(request):
    request.session.flush()
    return redirect("login")


def admin_patients(request):
    if not request.session.get("admin_logged_in"):
        return redirect("login")

    patients = Patient.objects.all()

    return render(request, "admin/admin_dashboard.html", {
        "page": "patients",
        "patients": patients
    })

def delete_patient(request, id):
    if not request.session.get("admin_logged_in"):
        return redirect("login")

    Patient.objects.filter(id=id).delete()
    messages.success(request, "Patient deleted successfully")
    return redirect("admin_patients")



def edit_patient(request, id):
    if not request.session.get("admin_logged_in"):
        return redirect("login")

    patient = Patient.objects.get(id=id)

    if request.method == "POST":
        patient.name = request.POST.get("name")
        patient.age = request.POST.get("age")
        patient.mobile = request.POST.get("mobile")
        patient.address = request.POST.get("address")
        patient.save()

        messages.success(request, "Patient updated successfully")
        return redirect("admin_patients")

    return render(request, "admin/admin_dashboard.html", {
        "patient": patient ,
        "page" : "edit_patient"
    })


def admin_add_patient(request):
    return render(request, "admin/admin_dashboard.html", {
        "page": "add_patient"
    })


def admin_doctors(request):
    doctors = Doctor.objects.all()
    return render(request, "admin/admin_dashboard.html", {
        "page": "doctors",
        "doctors": doctors
    })


def admin_add_doctor(request):
    return render(request, "admin/admin_dashboard.html", {
        "page": "add_doctor"
    })

def save_doctor(request):
    if request.method == "POST":

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        email = request.POST.get("email")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("admin_add_doctor")

        # Save doctor
        Doctor.objects.create(
            name=request.POST.get("name"),
            specialization=request.POST.get("specialization"),
            email=email,
            mobile=request.POST.get("mobile"),
            experience=request.POST.get("experience"),
            address=request.POST.get("address"),
            image=request.FILES.get("image"),
            document=request.FILES.get("document"),
            password=make_password(password),
        )

        # EMAIL CONTENT
        subject = "Medical Clinic | Doctor Login Details"
        message = f"""
Hello Doctor,

Welcome to Medical Clinic.

Your account has been created successfully.

Login Details:
Email: {email}
Password: {password}

Please login to the Medical Clinic portal using the above credentials.

Regards,
Medical Clinic Team
"""

        # SEND EMAIL using utils
        send_auto_reply(
            email=email,
            subject=subject,
            message=message
        )

        messages.success(request, "Doctor added successfully & email sent")
        return redirect("admin_doctors")



def edit_doctor(request, id):
    doctor = Doctor.objects.get(id=id)

    if request.method == "POST":

        doctor.name = request.POST.get("name")
        doctor.specialization = request.POST.get("specialization")
        doctor.mobile = request.POST.get("mobile")
        doctor.experience = request.POST.get("experience")
        doctor.address = request.POST.get("address")

        if request.FILES.get("image"):
            doctor.image = request.FILES.get("image")

        if request.FILES.get("document"):
            doctor.document = request.FILES.get("document")

        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        if password:
            if password != confirm:
                messages.error(request, "Passwords do not match")
                return redirect("edit_doctor", id=id)
            doctor.password = make_password(password)

        doctor.save()
        messages.success(request, "Doctor updated successfully")
        return redirect("admin_doctors")

    return render(request, "admin/admin_dashboard.html", {
        "page": "edit_doctor",
        "doctor": doctor
    })



def delete_doctor(request, id):
    Doctor.objects.get(id=id).delete()
    messages.success(request, "Doctor deleted successfully")
    return redirect("admin_doctors")



def newsletter_signup(request):
    if request.method == "POST":
        email = request.POST.get('email')

        send_auto_reply(
            email=email,
            subject="Thanks for Subscribing!",
            message="Hello 👋\n\n"
                "Thank you for subscribing to our newsletter.\n"
                "We’re glad to have you with us!\n\n"
                "Regards,\n"
                "Medical-Clinic Team"
        )

        return render(request, 'Nav-tab/index.html')
    


def contact_view(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        message = request.POST.get('message')

        # 1️⃣ SAVE INTO DATABASE
        contact = Contact.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            mobile=mobile,
            message=message
        )

        # 2️⃣ SEND AUTO EMAIL
        send_auto_reply ( 

            email=email,
            subject="Thanks for contacting us",
            message=(
            f"Hello {first_name},\n\n"
            "Thank you for contacting us.\n"
            "We have received your message and will get back to you shortly.\n\n"
            "Regards,\n"
            "Support Team" 
             )
        )

        return render(request, 'Nav-tab/contact.html')

    return render(request, 'Nav-tab/contact.html')


from django.contrib.auth import logout

def custom_logout(request):
    logout(request)
    return redirect('home')

#=======================PATIENT DASHBOARD =======================

from datetime import date
import calendar
from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from .models import Patient, Doctor, Appointment, ChatThread, ChatMessage
from .utils import send_auto_reply  # your email function

def patient_dashboard(request):
    # ================= SESSION CHECK =================
    patient_id = request.session.get("patient_id")
    if not patient_id:
        return redirect("login")

    patient = Patient.objects.get(id=patient_id)

    # ================= URL PARAMS =================
    page = request.GET.get("page", "dashboard")
    appointment_id = request.GET.get("appointment_id")
    specialization: str | None = request.GET.get("specialization")
    query = request.GET.get("q", "")
    doctor_id_raw = request.GET.get("doctor_id")
    doctor_id: int | None = int(doctor_id_raw) if doctor_id_raw else None
    open_chat_id_raw = request.GET.get("open_chat_id")
    open_chat_id: int | None = int(open_chat_id_raw) if open_chat_id_raw else None

    # ================= DEFAULTS =================
    section = page
    doctors = Doctor.objects.none()
    doctor = None
    selected_date = None
    selected_time = None

    # For appointments page
    upcoming_appointments = []
    past_appointments = []
    selected_appointment = None
    chat_messages = None

    # ================= COMMON DATA =================
    today = date.today()
    time_slots = ["12:00 am", "12:30 am", "1:00 am", "1:30 am",
                  "2:00 am", "2:30 am", "3:00 am", "3:30 am",
                  "4:00 am", "4:30 am"]

    # ================= CONTEXT INITIALIZATION =================
    context = {
        "patient": patient,
        "section": section,
        "query": query,
        "selected_specialization": specialization,
        "doctors": doctors,
        "doctor": doctor,
        "selected_date": selected_date,
        "selected_time": selected_time,
        "upcoming_appointments": upcoming_appointments,
        "past_appointments": past_appointments,
        "selected_appointment": selected_appointment,
        "chat_messages": chat_messages,
        "open_chat_id": open_chat_id,
    }

    # =================================================
    # 1️⃣ DASHBOARD
    # =================================================
    if page == "dashboard":
        return render(request, "dashboard/patient_dashboard.html", context)

    # =================================================
    # 2️⃣ BOOK APPOINTMENT (DOCTOR LIST)
    # =================================================
    if page == "book":
        doctors = Doctor.objects.all()
        if query:
            doctors = doctors.filter(
                Q(name__icontains=query) |
                Q(specialization__icontains=query) |
                Q(qualification__icontains=query) |
                Q(bio__icontains=query) |
                Q(experience__icontains=query)
            ).distinct()

        # Calendar defaults
        today = date.today()
        month = int(request.GET.get("month", today.month))
        year = int(request.GET.get("year", today.year))

        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        cal = calendar.Calendar(calendar.SUNDAY)
        month_days = cal.monthdayscalendar(year, month)

        # Default time slots
        time_slots = [
            "12:00 am", "12:30 am",
            "1:00 am", "1:30 am",
            "2:00 am", "2:30 am",
            "3:00 am", "3:30 am",
            "4:00 am", "4:30 am",
        ]

        context.update({
            "section": "book",
            "doctors": doctors,
            "query": query,
            "month": month,
            "year": year,
            "month_name": calendar.month_name[month],
            "month_days": month_days,
            "time_slots": time_slots,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # =================================================
    # 3️⃣ APPOINTMENTS
    # =================================================
    if page == "appointments":
         upcoming_appointments = Appointment.objects.filter(
             patient=patient,
             date__gte=today,
             status="Confirmed"
         ).select_related("doctor").order_by("date", "time")

         past_appointments = Appointment.objects.filter(
             patient=patient
         ).exclude(
           date__gte=today,
           status="Confirmed"
         ).select_related("doctor").order_by("-date", "-time")

    # No chat logic here at all

         context.update({
           "section": "appointments",
           "upcoming_appointments": upcoming_appointments,
           "past_appointments": past_appointments,
         })
         return render(request, "dashboard/patient_dashboard.html", context)
    

    # ================= PRESCRIPTION QUERIES =================
    if page == "p_queries":
        appointments = (
            Appointment.objects
            .filter(patient=patient, status="Confirmed")
            .select_related("doctor")
        )

        context["appointments"] = appointments
        context.update({
         "section": "p_queries",
         "appointments": appointments
         })

        return render(request, "dashboard/patient_dashboard.html", context)

    # ================= CHAT =================
    if page == "chat" and appointment_id:
        appointment = Appointment.objects.get(
            id=appointment_id, patient=patient
        )

        thread, _ = ChatThread.objects.get_or_create(
            appointment=appointment
        )

        if request.method == "POST":
            text = request.POST.get("message")
            if text:
                ChatMessage.objects.create(
                    thread=thread,
                    sender="patient",
                    message=text
                )
            return redirect(f"/patient_dashboard/?page=chat&appointment_id={appointment.id}")

        context.update({
            "appointment": appointment,
            "doctor": appointment.doctor,
            "messages": thread.messages.all()
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # =================================================
    # 4️⃣ SPECIALIZATION FILTER
    # =================================================
    if specialization:
        doctors = Doctor.objects.filter(specialization=specialization)
        context.update({
            "section": "specialization",
            "doctors": doctors,
            "selected_specialization": specialization,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # =================================================
    # 5️⃣ SCHEDULE PAGE
    # =================================================
    if page == "schedule" and doctor_id:
        doctor = Doctor.objects.get(id=doctor_id)
        today = date.today()
        month = int(request.GET.get("month", today.month))
        year = int(request.GET.get("year", today.year))

        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        cal = calendar.Calendar(calendar.SUNDAY)
        month_days = cal.monthdayscalendar(year, month)

        selected_date = request.POST.get("date") or request.GET.get("date")
        selected_time = request.POST.get("time")

        time_slots = [
            "12:00 am", "12:30 am",
            "1:00 am", "1:30 am",
            "2:00 am", "2:30 am",
            "3:00 am", "3:30 am",
            "4:00 am", "4:30 am",
        ]

        context.update({
            "section": "schedule",
            "doctor": doctor,
            "month": month,
            "year": year,
            "month_name": calendar.month_name[month],
            "month_days": month_days,
            "time_slots": time_slots,
            "selected_date": selected_date,
            "selected_time": selected_time,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # =================================================
    # 6️⃣ BOOKING CONFIRMATION
    # =================================================
    if page == "booking" and doctor_id:
        doctor = Doctor.objects.get(id=doctor_id)
        selected_date = request.GET.get("date")
        selected_time = request.GET.get("time")

        if request.method == "POST":
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=selected_date,
                time=selected_time,
                first_name=request.POST.get("first_name"),
                last_name=request.POST.get("last_name"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone"),
                message=request.POST.get("text"),
                amount=300,
                status="Confirmed"
            )
            ChatThread.objects.create(appointment=appointment)

            send_auto_reply(
                email=patient.email,
                subject="Appointment Confirmed - Medical Clinic",
                message=f"""
                Hello {patient.name},

                Your appointment has been confirmed.

                Doctor: {doctor.name}
                Date: {selected_date}
                Time: {selected_time}

                Thank you!
                Medical Clinic
                """
            )

            send_auto_reply(
                email=doctor.email,
                subject="📅 New Appointment Booked",
                message=f"""
                Hello Dr. {doctor.name},

                A new appointment has been booked.

                Patient Name: {appointment.first_name} {appointment.last_name}
                Patient Email: {appointment.email}
                Phone: {appointment.phone}

                Date: {appointment.date}
                Time: {appointment.time}

                Patient Message:
                {appointment.message}

                Regards,
                Medical Clinic System
                """
            )

            messages.success(request, "Appointment booked successfully ✅")
            return redirect("/patient_dashboard/?page=appointments")

        context.update({
            "section": "booking",
            "doctor": doctor,
            "selected_date": selected_date,
            "selected_time": selected_time,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # =================================================
    # 7️⃣ FALLBACK
    # =================================================
    return render(request, "dashboard/patient_dashboard.html", context)



def cancel_appointment(request, id):
    patient_id = request.session.get("patient_id")
    if not patient_id:
        return redirect("login")

    appointment = get_object_or_404(
        Appointment,
        id=id,
        patient_id=patient_id
    )

    appointment.status = "Cancelled"
    appointment.save()

    messages.success(request, "Appointment cancelled")

    return redirect("/patient_dashboard/?page=appointments")





def medical_reports(request):
    patient = Patient.objects.get(user=request.user)
    return render(request, 'dashboard/patient_dashboard.html', {
        'patient': patient,
        'section': 'reports'
    })






def video_call(request):
    patient = Patient.objects.get(user=request.user)
    return render(request, 'dashboard/patient_dashboard.html', {
        'patient': patient,
        'section': 'video'
    })


def notifications(request):
    patient = Patient.objects.get(user=request.user)
    return render(request, 'dashboard/patient_dashboard.html', {
        'patient': patient,
        'section': 'notifications'
    })


def medical_progress(request):
    patient = Patient.objects.get(user=request.user)
    return render(request, 'dashboard/patient_dashboard.html', {
        'patient': patient,
        'section': 'progress'
    })


def medical_health(request):
    patient = Patient.objects.get(user=request.user)
    return render(request, 'dashboard/patient_dashboard.html', {
        'patient': patient,
        'section': 'health'
    })



def chat_room(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # security
    if request.session.get("patient_id"):
        if appointment.patient.id != request.session["patient_id"]:
            return redirect("patient_dashboard")
        sender = "patient"

    elif request.session.get("doctor_id"):
        if appointment.doctor.id != request.session["doctor_id"]:
            return redirect("doctor_dashboard")
        sender = "doctor"

    else:
        return redirect("login")

    thread = appointment.chat
    messages = thread.messages.order_by("created_at")

    if request.method == "POST":
        ChatMessage.objects.create(
            thread=thread,
            sender=sender,
            message=request.POST.get("message")
        )
        return redirect("chat_room", appointment_id=appointment.id)

    return render(request, "chat/chat_room.html", {
        "appointment": appointment,
        "messages": messages,
        "sender": sender
    })




from clinic.models import Appointment

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Doctor, Appointment, ChatThread, ChatMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages

def doctor_dashboard(request):
    if not request.session.get("doctor_id"):
        return redirect("login")
     # ================= SKIP PROFILE =================
    if request.GET.get("skip") == "true":
       request.session["skip_profile"] = True


    doctor = get_object_or_404(Doctor, id=request.session["doctor_id"])

    page = request.GET.get("page", "appointments")
    open_chat_id = request.GET.get("open_chat_id")
    

    # ================= APPOINTMENTS =================
    appointments = Appointment.objects.filter(
        doctor=doctor,
        status="Confirmed"
    ).select_related("patient").order_by("-date", "-time")

    chat_appointment = None
    messages_list = []

    # ================= OPEN CHAT =================
    if open_chat_id:
        chat_appointment = get_object_or_404(
            Appointment,
            id=open_chat_id,
            doctor=doctor
        )

        thread, _ = ChatThread.objects.get_or_create(
            appointment=chat_appointment,
            is_active=True
        )

        messages_list = thread.messages.all().order_by("created_at")

    # ================= SEND MESSAGE =================
    if request.method == "POST" and "send_message" in request.POST:
        appointment_id = request.POST.get("appointment_id")
        text = request.POST.get("message")

        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            doctor=doctor
        )

        thread, _ = ChatThread.objects.get_or_create(
            appointment=appointment,
            is_active=True
        )

        ChatMessage.objects.create(
            thread=thread,
            sender="doctor",
            message=text
        )

        return redirect(
            reverse("doctor_dashboard")
            + f"?page=prescriptions&open_chat_id={appointment.id}"
        )

    # ================= END CHAT =================
    if request.method == "POST" and "end_chat" in request.POST:
        appointment_id = request.POST.get("appointment_id")

        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            doctor=doctor
        )

        ChatThread.objects.filter(
            appointment=appointment,
            is_active=True
        ).delete()   # 🔥 poora chat clear

        messages.success(request, "Chat ended and cleared successfully")

        return redirect(
            reverse("doctor_dashboard") + "?page=prescriptions"
        )

    return render(request, "dashboard/doctor_dashboard.html", {
        "doctor": doctor,
        "page": page,
        "appointments": appointments,
        "open_chat_id": int(open_chat_id) if open_chat_id else None,
        "chat_appointment": chat_appointment,
        "messages": messages_list
    })
 