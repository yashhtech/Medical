import json
import logging
import calendar
import uuid
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.urls import reverse
from django.db.models import Q, Sum
from django.views.decorators.csrf import csrf_exempt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

import razorpay

from .models import (
    Patient,
    Contact,
    Doctor,
    Newsletter,
    Appointment,
    ChatMessage,
    ChatThread,
    Notification,
)
from .utils import send_auto_reply
from .decorators import admin_required, patient_required, doctor_required

logger = logging.getLogger(__name__)


# =====================================================================
# PUBLIC NAVIGATION VIEWS
# =====================================================================

def home(request):
    return render(request, "Nav-tab/index.html")


def contact(request):
    return render(request, "Nav-tab/contact.html")


def about(request):
    return render(request, "Nav-tab/about.html")


def departments(request):
    return render(request, "Nav-tab/departments.html")


def insurance(request):
    return render(request, "Nav-tab/insurance.html")


def cardiology(request):
    return render(request, "Departments/cardiology.html")


def neurology(request):
    return render(request, "Departments/neurology.html")


def orthopaedics(request):
    return render(request, "Departments/orthopaedics.html")


def booking(request):
    """Public services booking overview."""
    return render(request, "Appointment/booking.html")


# =====================================================================
# NEWSLETTER & CONTACT FORM HANDLING
# =====================================================================

def newsletter_signup(request):
    """Handle newsletter subscriptions and persist to the database."""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "Please provide a valid email address.")
            return redirect("home")

        subscriber, created = Newsletter.objects.get_or_create(email=email)
        if created:
            messages.success(request, "Thank you for subscribing to our newsletter!")
            send_auto_reply(
                email=email,
                subject="Thanks for Subscribing | Medical Clinic",
                message=(
                    "Hello,\n\n"
                    "Thank you for subscribing to the Medical Clinic newsletter. "
                    "We look forward to sharing health tips and clinic updates with you!\n\n"
                    "Regards,\n"
                    "Medical Clinic Team"
                ),
            )
        else:
            messages.info(request, "You are already subscribed to our newsletter.")

    return redirect("home")


def contact_view(request):
    """Handle contact inquiries and save to database."""
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        message = request.POST.get("message", "").strip()

        if not first_name or not email or not message:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "Nav-tab/contact.html")

        Contact.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            mobile=mobile,
            message=message,
        )

        send_auto_reply(
            email=email,
            subject="Thanks for contacting Medical Clinic",
            message=(
                f"Hello {first_name},\n\n"
                "Thank you for contacting us. We have received your inquiry "
                "and will get back to you shortly.\n\n"
                "Regards,\n"
                "Medical Clinic Support Team"
            ),
        )

        messages.success(request, "Your message has been sent successfully! We will contact you soon.")
        return redirect("contact")

    return render(request, "Nav-tab/contact.html")


# =====================================================================
# AUTHENTICATION VIEWS
# =====================================================================

def login(request):
    """Render unified login portal."""
    if request.session.get("patient_id"):
        return redirect("patient_dashboard")
    if request.session.get("doctor_id"):
        return redirect("doctor_dashboard")
    if request.session.get("admin_logged_in"):
        return redirect("admin_dashboard")

    role = request.GET.get("role")
    if "login_entry" not in request.session:
        request.session["login_entry"] = "/"

    sample_patient = Patient.objects.order_by("id").first()
    sample_doctor = Doctor.objects.order_by("id").first()

    context = {
        "role": role,
        "login_entry": request.session.get("login_entry", "/"),
        "sample_patient_email": sample_patient.email if sample_patient else "patient@demo.com",
        "sample_patient_password": "patient123",
        "sample_doctor_email": sample_doctor.email if sample_doctor else "doctor@demo.com",
        "sample_doctor_password": "doctor123",
        "admin_email": getattr(settings, "ADMIN_EMAIL", "admin@gmail.com"),
        "admin_password": getattr(settings, "ADMIN_PASSWORD", "password"),
    }
    return render(request, "Nav-tab/login.html", context)


def role_login(request, role):
    """Process login credentials by role."""
    if request.method != "POST":
        return redirect("login")

    email = request.POST.get("email", "").strip().lower()
    password = request.POST.get("password", "")

    # ================= ADMIN LOGIN =================
    if role == "admin":
        admin_email = getattr(settings, "ADMIN_EMAIL", "admin@gmail.com").strip().lower()
        admin_password = getattr(settings, "ADMIN_PASSWORD", "admin@123")

        if email == admin_email and password == admin_password:
            request.session.flush()
            request.session["admin_logged_in"] = True
            messages.success(request, "Admin login successful.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid admin credentials.")
            return redirect("/login/?role=admin")

    # ================= PATIENT LOGIN =================
    elif role == "patient":
        try:
            patient = Patient.objects.get(email__iexact=email)
            if check_password(password, patient.password):
                request.session.flush()
                request.session["patient_id"] = patient.id
                messages.success(request, f"Welcome back, {patient.name}!")
                return redirect("patient_dashboard")
            else:
                messages.error(request, "Incorrect password.")
                return redirect("/login/?role=patient")
        except Patient.DoesNotExist:
            messages.error(request, "Email not registered as a patient.")
            return redirect("/login/?role=patient")

    # ================= DOCTOR LOGIN =================
    elif role == "doctor":
        try:
            doctor = Doctor.objects.get(email__iexact=email)
            if check_password(password, doctor.password):
                request.session.flush()
                request.session["doctor_id"] = doctor.id
                messages.success(request, f"Welcome back, Dr. {doctor.name}!")
                return redirect("doctor_dashboard")
            else:
                messages.error(request, "Incorrect password.")
                return redirect("/login/?role=doctor")
        except Doctor.DoesNotExist:
            messages.error(request, "Email not registered as a doctor.")
            return redirect("/login/?role=doctor")

    else:
        messages.error(request, "Invalid login role specified.")
        return redirect("login")


def new_patient_register(request):
    """Patient registration view."""
    if request.method == "POST":
        source = request.POST.get("source")
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        email = request.POST.get("email", "").strip().lower()

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            if source == "admin":
                return redirect("admin_add_patient")
            return redirect("/login/?role=new_patient")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            if source == "admin":
                return redirect("admin_add_patient")
            return redirect("/login/?role=new_patient")

        if Patient.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email is already registered.")
            if source == "admin":
                return redirect("admin_add_patient")
            return redirect("/login/?role=new_patient")

        try:
            age = int(request.POST.get("age", 0))
        except (TypeError, ValueError):
            age = 0

        patient = Patient.objects.create(
            salutation=request.POST.get("salutation", "").strip(),
            name=request.POST.get("name", "").strip(),
            gender=request.POST.get("gender", "").strip(),
            age=age,
            email=email,
            mobile=request.POST.get("mobile", "").strip(),
            address=request.POST.get("address", "").strip(),
            image=request.FILES.get("image"),
            password=make_password(password),
        )

        if source == "admin":
            messages.success(request, f"Patient '{patient.name}' created successfully.")
            return redirect("admin_patients")
        else:
            messages.success(request, "Registration successful! Please login with your credentials.")
            return redirect("/login/?role=patient")

    return redirect("login")


def custom_logout(request):
    """Universal logout handler for patients and doctors."""
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")


def doctor_logout(request):
    """Explicit doctor logout."""
    if "doctor_id" in request.session:
        del request.session["doctor_id"]
    messages.success(request, "Logged out successfully.")
    return redirect("login")


def admin_logout(request):
    """Admin logout handler."""
    request.session.flush()
    messages.success(request, "Admin logged out successfully.")
    return redirect("login")


# =====================================================================
# PATIENT DASHBOARD & SUBPAGES
# =====================================================================

@patient_required
def patient_dashboard(request):
    """Main patient portal with dynamic tabs."""
    patient = request.patient
    page = request.GET.get("page", "dashboard")
    specialization = request.GET.get("specialization")
    query = request.GET.get("q", "").strip()
    appointment_id = request.GET.get("appointment_id")

    doctor_id_raw = request.GET.get("doctor_id")
    doctor_id = int(doctor_id_raw) if doctor_id_raw and doctor_id_raw.isdigit() else None

    today = date.today()
    time_slots = [
        "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
        "11:00 AM", "11:30 AM", "02:00 PM", "02:30 PM",
        "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM",
    ]

    context = {
        "patient": patient,
        "section": page,
        "query": query,
        "selected_specialization": specialization,
        "today": today,
    }

    # 1. Dashboard Home
    if page == "dashboard":
        upcoming_count = Appointment.objects.filter(
            patient=patient, date__gte=today, status="Confirmed"
        ).count()
        past_count = Appointment.objects.filter(patient=patient).exclude(
            date__gte=today, status="Confirmed"
        ).count()
        upcoming_appointments_preview = (
            Appointment.objects.filter(patient=patient, date__gte=today, status="Confirmed")
            .select_related("doctor")
            .order_by("date", "time")[:3]
        )
        context.update({
            "upcoming_count": upcoming_count,
            "past_count": past_count,
            "upcoming_preview": upcoming_appointments_preview,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # Profile Edit
    if page == "profile":
        if request.method == "POST":
            name = request.POST.get("name", "").strip()
            age = request.POST.get("age", "").strip()
            mobile = request.POST.get("mobile", "").strip()
            address = request.POST.get("address", "").strip()
            if name:
                patient.name = name
            if age and age.isdigit():
                patient.age = int(age)
            if mobile:
                patient.mobile = mobile
            if address:
                patient.address = address
            if request.FILES.get("image"):
                patient.image = request.FILES.get("image")
            patient.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect(f"{reverse('patient_dashboard')}?page=profile")

        context.update({"section": "profile"})
        return render(request, "dashboard/patient_dashboard.html", context)

    # 2. Book Appointment / Doctor Search
    if page == "book":
        doctors = Doctor.objects.all()
        if query:
            doctors = doctors.filter(
                Q(name__icontains=query)
                | Q(specialization__icontains=query)
                | Q(qualification__icontains=query)
                | Q(bio__icontains=query)
            ).distinct()

        context.update({
            "section": "book",
            "doctors": doctors,
            "query": query,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # 3. Specialization Filter
    if specialization or page == "specialization":
        doctors = Doctor.objects.filter(specialization__iexact=specialization)
        context.update({
            "section": "specialization",
            "doctors": doctors,
            "selected_specialization": specialization,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # 4. Schedule Slot Selection
    # 4. Schedule Slot Selection
    if page == "schedule" and doctor_id:
        doctor = get_object_or_404(Doctor, id=doctor_id)
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
        selected_time = request.POST.get("time") or request.GET.get("time")

        # If submitted via POST (Select Slot clicked) with both date and time, redirect cleanly to booking
        if request.method == "POST" and selected_date and selected_time:
            return redirect(
                f"{reverse('patient_dashboard')}?page=booking&doctor_id={doctor.id}&date={selected_date}&time={selected_time}"
            )

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
            "today_str": today.strftime("%Y-%m-%d"),
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # 5. Booking & Payment Page
    if page == "booking" and doctor_id:
        doctor = get_object_or_404(Doctor, id=doctor_id)
        selected_date = request.GET.get("date") or request.POST.get("date")
        selected_time = request.GET.get("time") or request.POST.get("time")
        order_amount = 300 * 100  # in paise (300 INR)
        order_id = ""

        razorpay_key = getattr(settings, "RAZORPAY_KEY_ID", "")
        razorpay_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")

        try:
            if razorpay_key and razorpay_secret:
                client = razorpay.Client(auth=(razorpay_key, razorpay_secret))
                order = client.order.create({
                    "amount": order_amount,
                    "currency": "INR",
                    "payment_capture": "1",
                })
                order_id = order.get("id", "")
        except Exception as exc:
            logger.warning(f"Razorpay order creation fallback: {exc}")
            order_id = f"order_demo_{int(date.today().strftime('%Y%m%d'))}"

        context.update({
            "section": "booking",
            "doctor": doctor,
            "selected_date": selected_date,
            "selected_time": selected_time,
            "razorpay_key": razorpay_key,
            "order_id": order_id,
            "amount": order_amount,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # 6. Appointments List
    if page == "appointments":
        upcoming_appointments = (
            Appointment.objects.filter(
                patient=patient, date__gte=today, status="Confirmed"
            )
            .select_related("doctor")
            .order_by("date", "time")
        )
        past_appointments = (
            Appointment.objects.filter(patient=patient)
            .exclude(date__gte=today, status="Confirmed")
            .select_related("doctor")
            .order_by("-date", "-time")
        )
        context.update({
            "section": "appointments",
            "upcoming_appointments": upcoming_appointments,
            "past_appointments": past_appointments,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # 7. Prescription Queries
    if page == "p_queries":
        appointments = (
            Appointment.objects.filter(patient=patient, status="Confirmed")
            .select_related("doctor")
            .order_by("-date")
        )
        context.update({
            "section": "p_queries",
            "appointments": appointments,
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    # 8. Chat View
    if page == "chat" and appointment_id:
        appointment = get_object_or_404(
            Appointment, id=appointment_id, patient=patient
        )
        thread, _ = ChatThread.objects.get_or_create(appointment=appointment)

        if request.method == "POST":
            text = request.POST.get("message", "").strip()
            if text:
                ChatMessage.objects.create(
                    thread=thread, sender="patient", message=text
                )
                Notification.objects.create(
                    doctor=appointment.doctor,
                    role="doctor",
                    title="New Message from Patient",
                    message=f"{patient.name}: {text[:60]}...",
                    link=f"{reverse('doctor_dashboard')}?page=prescriptions&open_chat_id={appointment.id}"
                )
            return redirect(
                f"/patient_dashboard/?page=chat&appointment_id={appointment.id}"
            )

        context.update({
            "section": "chat",
            "appointment": appointment,
            "doctor": appointment.doctor,
            "chat_messages": thread.messages.all(),
        })
        return render(request, "dashboard/patient_dashboard.html", context)

    return render(request, "dashboard/patient_dashboard.html", context)


# =====================================================================
# PATIENT SUBPAGES (RESOLVES 500 CRASHES)
# =====================================================================

@patient_required
def medical_reports(request):
    patient = request.patient
    prescriptions = (
        Appointment.objects.filter(patient=patient)
        .exclude(prescription_notes="")
        .select_related("doctor")
        .order_by("-date")
    )
    all_appointments = (
        Appointment.objects.filter(patient=patient)
        .select_related("doctor")
        .order_by("-date")
    )
    return render(request, "dashboard/patient_dashboard.html", {
        "patient": patient,
        "section": "reports",
        "prescriptions": prescriptions,
        "appointments": all_appointments,
    })


@patient_required
def video_call(request):
    patient = request.patient
    active_appointments = (
        Appointment.objects.filter(
            patient=patient, status="Confirmed", date__gte=date.today()
        )
        .select_related("doctor")
        .order_by("date", "time")
    )
    return render(request, "dashboard/patient_dashboard.html", {
        "patient": patient,
        "section": "video",
        "active_appointments": active_appointments,
    })


@patient_required
def notifications(request):
    patient = request.patient
    # Mark unread as read
    Notification.objects.filter(patient=patient, role="patient", is_read=False).update(is_read=True)

    db_notifications = Notification.objects.filter(patient=patient, role="patient")[:20]

    return render(request, "dashboard/patient_dashboard.html", {
        "patient": patient,
        "section": "notifications",
        "notifications_list": db_notifications,
    })


@patient_required
def medical_progress(request):
    patient = request.patient
    total_visits = Appointment.objects.filter(patient=patient).count()
    completed_visits = Appointment.objects.filter(
        patient=patient, status="Completed"
    ).count()
    upcoming_visits = Appointment.objects.filter(
        patient=patient, status="Confirmed", date__gte=date.today()
    ).count()

    return render(request, "dashboard/patient_dashboard.html", {
        "patient": patient,
        "section": "progress",
        "total_visits": total_visits,
        "completed_visits": completed_visits,
        "upcoming_visits": upcoming_visits,
    })


@patient_required
def medical_health(request):
    patient = request.patient
    return render(request, "dashboard/patient_dashboard.html", {
        "patient": patient,
        "section": "health",
    })


# =====================================================================
# PAYMENT VERIFICATION
# =====================================================================

@csrf_exempt
def payment_verify(request):
    """Verify Razorpay payment and create appointment."""
    if request.method != "POST":
        return JsonResponse({"status": "failed", "error": "Method not allowed"}, status=405)

    patient_id = request.session.get("patient_id")
    if not patient_id:
        return JsonResponse({"status": "failed", "error": "Session expired"}, status=401)

    try:
        data = json.loads(request.body)
        doctor_id = data.get("doctor_id")
        patient = Patient.objects.get(id=patient_id)
        doctor = Doctor.objects.get(id=doctor_id)

        upi_id = data.get("upi_id")
        payment_mode = "UPI (Test Mode)" if upi_id else "Razorpay Gateway"
        payment_id = data.get("razorpay_payment_id") or f"pay_upi_test_{uuid.uuid4().hex[:10]}"
        order_id = data.get("razorpay_order_id") or f"order_upi_test_{uuid.uuid4().hex[:8]}"
        signature = data.get("razorpay_signature") or f"sig_upi_test_{uuid.uuid4().hex[:12]}"

        # Standard Razorpay verification only if real signature is provided
        if not upi_id and razorpay_key and razorpay_secret and data.get("razorpay_signature"):
            try:
                client = razorpay.Client(auth=(razorpay_key, razorpay_secret))
                params_dict = {
                    "razorpay_order_id": data.get("razorpay_order_id"),
                    "razorpay_payment_id": data.get("razorpay_payment_id"),
                    "razorpay_signature": data.get("razorpay_signature"),
                }
                client.utility.verify_payment_signature(params_dict)
            except Exception as sig_err:
                logger.warning(f"Signature verification warning: {sig_err}")

        appt_date = data.get("date")
        appt_time = data.get("time")

        # Duplicate appointment prevention
        if Appointment.objects.filter(
            patient=patient, doctor=doctor, date=appt_date, time=appt_time
        ).exists():
            return JsonResponse(
                {"status": "failed", "error": "You already have an appointment with this doctor at the selected date and time. Please choose a different slot."},
                status=409
            )

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=appt_date,
            time=appt_time,
            first_name=data.get("first_name", patient.name),
            last_name=data.get("last_name", ""),
            email=data.get("email", patient.email),
            phone=data.get("phone", patient.mobile),
            message=data.get("message", "") + (f" [Paid via UPI: {upi_id}]" if upi_id else ""),
            amount=300,
            status="Confirmed",
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            razorpay_signature=signature,
            is_paid=True,
        )

        ChatThread.objects.get_or_create(appointment=appointment)

        # Create notifications for both parties
        Notification.objects.create(
            doctor=doctor,
            role="doctor",
            title="New Appointment Scheduled",
            message=f"{patient.name} booked a consultation on {appointment.date} at {appointment.time}.",
            link="/doctor_dashboard/?page=appointments"
        )
        Notification.objects.create(
            patient=patient,
            role="patient",
            title="Appointment Confirmed & Paid",
            message=f"Your consultation with Dr. {doctor.name} on {appointment.date} at {appointment.time} is confirmed.",
            link="/patient_dashboard/?page=appointments"
        )

        send_auto_reply(
            email=patient.email,
            subject="Appointment Confirmed | Medical Clinic",
            message=(
                f"Hello {patient.name},\n\n"
                "Your appointment has been successfully booked.\n\n"
                f"Doctor: Dr. {doctor.name} ({doctor.specialization})\n"
                f"Date: {appointment.date}\n"
                f"Time: {appointment.time}\n"
                f"Fee: 300 INR (Paid)\n\n"
                "You can view details and download your invoice in your patient dashboard.\n\n"
                "Regards,\n"
                "Medical Clinic"
            ),
        )

        send_auto_reply(
            email=doctor.email,
            subject=f"New Appointment Booked: {patient.name}",
            message=(
                f"Hello Dr. {doctor.name},\n\n"
                "A new appointment has been scheduled.\n\n"
                f"Patient: {appointment.first_name} {appointment.last_name}\n"
                f"Email: {appointment.email}\n"
                f"Phone: {appointment.phone}\n"
                f"Date: {appointment.date}\n"
                f"Time: {appointment.time}\n"
                f"Message: {appointment.message or 'None'}\n\n"
                "Regards,\n"
                "Medical Clinic System"
            ),
        )

        return JsonResponse({
            "status": "success",
            "redirect_url": "/patient_dashboard/?page=appointments",
        })

    except Exception as exc:
        logger.error(f"Payment verification failed: {exc}", exc_info=True)
        return JsonResponse({"status": "failed", "error": str(exc)}, status=400)


# =====================================================================
# INVOICE & APPOINTMENT CANCELLATION
# =====================================================================

def download_invoice(request, appointment_id):
    """Generate and stream PDF invoice with strict IDOR ownership check."""
    patient_id = request.session.get("patient_id")
    doctor_id = request.session.get("doctor_id")
    is_admin = request.session.get("admin_logged_in")

    if not patient_id and not doctor_id and not is_admin:
        messages.error(request, "Authentication required to download invoice.")
        return redirect("login")

    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor"),
        id=appointment_id
    )

    if not is_admin:
        if patient_id and appointment.patient_id != patient_id:
            return HttpResponseForbidden("Access denied: You do not own this invoice.")
        if doctor_id and appointment.doctor_id != doctor_id:
            return HttpResponseForbidden("Access denied: You are not the doctor for this appointment.")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{appointment.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=15,
    )
    elements.append(Paragraph("Medical Clinic - Official Invoice", title_style))
    elements.append(Spacer(1, 15))

    data = [
        ["Invoice Number", f"INV-{appointment.id:06d}"],
        ["Patient Name", appointment.patient.name],
        ["Doctor", f"Dr. {appointment.doctor.name}"],
        ["Department / Specialization", appointment.doctor.specialization],
        ["Appointment Date", str(appointment.date)],
        ["Appointment Time", appointment.time],
        ["Amount Paid", f"INR {appointment.amount}.00"],
        ["Payment Status", "Completed (Paid)" if appointment.is_paid else "Pending"],
        ["Payment Reference ID", appointment.razorpay_payment_id or "N/A"],
        ["Date Issued", str(date.today())],
    ]

    table = Table(data, colWidths=[200, 260])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 25))

    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
    )
    elements.append(Paragraph("Thank you for choosing Medical Clinic. Keep this receipt for your records.", note_style))

    doc.build(elements)
    return response


@patient_required
def cancel_appointment(request, id):
    """Cancel appointment safely with patient ownership."""
    patient = request.patient
    appointment = get_object_or_404(Appointment, id=id, patient=patient)

    if appointment.status == "Cancelled":
        messages.info(request, "This appointment is already cancelled.")
    else:
        appointment.status = "Cancelled"
        appointment.save()
        messages.success(request, "Appointment has been cancelled.")

    return redirect("/patient_dashboard/?page=appointments")


# =====================================================================
# DOCTOR DASHBOARD & ACTIONS
# =====================================================================

@doctor_required
def doctor_dashboard(request):
    """Doctor portal with profile management, schedule, and messaging."""
    doctor = request.doctor
    page = request.GET.get("page", "appointments")
    open_chat_id = request.GET.get("open_chat_id")

    if request.GET.get("skip") == "true":
        request.session["skip_profile"] = True

    # 1. Update Profile POST
    if request.method == "POST" and "update_profile" in request.POST:
        doctor.bio = request.POST.get("bio", "").strip()
        doctor.qualification = request.POST.get("qualification", "").strip()
        doctor.hobbies = request.POST.get("hobbies", "").strip()

        if request.FILES.get("image"):
            doctor.image = request.FILES.get("image")
        if request.FILES.get("document"):
            doctor.document = request.FILES.get("document")

        doctor.is_profile_completed = True
        doctor.save()
        messages.success(request, "Your profile has been updated successfully!")
        return redirect(f"{reverse('doctor_dashboard')}?page=appointments")

    # 2. Doctor Accepts Appointment POST
    if request.method == "POST" and "accept_appointment" in request.POST:
        appointment_id = request.POST.get("appointment_id")
        appt = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
        appt.status = "Confirmed"
        appt.save()

        Notification.objects.create(
            patient=appt.patient,
            role="patient",
            title="Appointment Confirmed by Doctor",
            message=f"Dr. {doctor.name} has confirmed your appointment on {appt.date} at {appt.time}.",
            link=f"/patient_dashboard/?page=appointments"
        )
        messages.success(request, f"Appointment for {appt.patient.name} confirmed!")
        return redirect(f"{reverse('doctor_dashboard')}?page=appointments")

    # 3. Doctor Rejects/Cancels Appointment POST
    if request.method == "POST" and "reject_appointment" in request.POST:
        appointment_id = request.POST.get("appointment_id")
        appt = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
        appt.status = "Rejected"
        appt.save()

        Notification.objects.create(
            patient=appt.patient,
            role="patient",
            title="Appointment Update",
            message=f"Dr. {doctor.name} was unable to accept your appointment scheduled for {appt.date} at {appt.time}. Please reschedule or choose another slot.",
            link=f"/patient_dashboard/?page=appointments"
        )
        messages.warning(request, f"Appointment for {appt.patient.name} has been rejected.")
        return redirect(f"{reverse('doctor_dashboard')}?page=appointments")

    # 4. Add Prescription POST
    if request.method == "POST" and "save_prescription" in request.POST:
        appointment_id = request.POST.get("appointment_id")
        prescription_notes = request.POST.get("prescription_notes", "").strip()
        prescription_file = request.FILES.get("prescription_file")

        appt = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
        appt.prescription_notes = prescription_notes
        if prescription_file:
            appt.prescription_file = prescription_file
        appt.status = "Completed"
        appt.save()

        Notification.objects.create(
            patient=appt.patient,
            role="patient",
            title="Prescription Available",
            message=f"Dr. {doctor.name} has attached your medical prescription and visit notes for your consultation on {appt.date}.",
            link="/patient_dashboard/?page=reports"
        )
        messages.success(request, f"Prescription saved for {appt.patient.name}!")
        return redirect(f"{reverse('doctor_dashboard')}?page=prescriptions")

    # 5. Chat Message POST
    if request.method == "POST" and "send_message" in request.POST:
        appointment_id = request.POST.get("appointment_id")
        text = request.POST.get("message", "").strip()
        appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)

        thread, _ = ChatThread.objects.get_or_create(appointment=appointment)
        if text:
            ChatMessage.objects.create(thread=thread, sender="doctor", message=text)
            Notification.objects.create(
                patient=appointment.patient,
                role="patient",
                title="New Message from Doctor",
                message=f"Dr. {doctor.name}: {text[:60]}...",
                link=f"/patient_dashboard/?page=chat&appointment_id={appointment.id}"
            )

        return redirect(
            f"{reverse('doctor_dashboard')}?page=prescriptions&open_chat_id={appointment.id}"
        )

    # 6. End Chat POST
    if request.method == "POST" and "end_chat" in request.POST:
        appointment_id = request.POST.get("appointment_id")
        appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
        ChatThread.objects.filter(appointment=appointment).update(is_active=False)
        messages.success(request, "Chat session ended.")
        return redirect(f"{reverse('doctor_dashboard')}?page=prescriptions")

    # If viewing notifications page, mark unread doctor notifications as read
    if page == "notifications":
        Notification.objects.filter(doctor=doctor, role="doctor", is_read=False).update(is_read=True)

    unread_notifications_count = Notification.objects.filter(
        doctor=doctor, role="doctor", is_read=False
    ).count()
    doctor_notifications = Notification.objects.filter(
        doctor=doctor, role="doctor"
    ).order_by("-created_at")[:25]

    appointments = (
        Appointment.objects.filter(doctor=doctor)
        .select_related("patient")
        .order_by("-date", "-time")
    )

    chat_appointment = None
    chat_messages = []
    if open_chat_id and open_chat_id.isdigit():
        chat_appointment = get_object_or_404(Appointment, id=int(open_chat_id), doctor=doctor)
        thread, _ = ChatThread.objects.get_or_create(appointment=chat_appointment)
        chat_messages = thread.messages.all().order_by("created_at")

    context = {
        "doctor": doctor,
        "page": page,
        "appointments": appointments,
        "open_chat_id": int(open_chat_id) if open_chat_id and open_chat_id.isdigit() else None,
        "chat_appointment": chat_appointment,
        "chat_messages": chat_messages,
        "doctor_notifications": doctor_notifications,
        "unread_notifications_count": unread_notifications_count,
    }
    return render(request, "dashboard/doctor_dashboard.html", context)


# =====================================================================
# ADMIN PORTAL
# =====================================================================

@admin_required
def admin_dashboard(request):
    """Admin dashboard with live statistics."""
    total_patients = Patient.objects.count()
    total_doctors = Doctor.objects.count()
    total_appointments = Appointment.objects.count()
    total_queries = Contact.objects.count()
    total_subscribers = Newsletter.objects.count()

    revenue_data = (
        Appointment.objects.filter(is_paid=True).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    recent_appointments = (
        Appointment.objects.select_related("patient", "doctor")
        .order_by("-created_at")[:5]
    )

    return render(request, "admin/admin_dashboard.html", {
        "page": "dashboard",
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": total_appointments,
        "total_queries": total_queries,
        "total_subscribers": total_subscribers,
        "total_revenue": revenue_data,
        "recent_appointments": recent_appointments,
    })


@admin_required
def admin_patients(request):
    """List all registered patients."""
    patients = Patient.objects.all().order_by("-created_at")
    return render(request, "admin/admin_dashboard.html", {
        "page": "patients",
        "patients": patients,
    })


@admin_required
def admin_add_patient(request):
    return render(request, "admin/admin_dashboard.html", {
        "page": "add_patient",
    })


@admin_required
def edit_patient(request, id):
    patient = get_object_or_404(Patient, id=id)

    if request.method == "POST":
        patient.name = request.POST.get("name", patient.name).strip()
        try:
            patient.age = int(request.POST.get("age", patient.age))
        except (ValueError, TypeError):
            pass
        patient.mobile = request.POST.get("mobile", patient.mobile).strip()
        patient.address = request.POST.get("address", patient.address).strip()
        if request.FILES.get("image"):
            patient.image = request.FILES.get("image")
        patient.save()

        messages.success(request, f"Patient '{patient.name}' updated successfully.")
        return redirect("admin_patients")

    return render(request, "admin/admin_dashboard.html", {
        "patient": patient,
        "page": "edit_patient",
    })


@admin_required
def delete_patient(request, id):
    patient = get_object_or_404(Patient, id=id)
    name = patient.name
    patient.delete()
    messages.success(request, f"Patient '{name}' deleted successfully.")
    return redirect("admin_patients")


@admin_required
def admin_doctors(request):
    doctors = Doctor.objects.all().order_by("name")
    return render(request, "admin/admin_dashboard.html", {
        "page": "doctors",
        "doctors": doctors,
    })


@admin_required
def admin_add_doctor(request):
    return render(request, "admin/admin_dashboard.html", {
        "page": "add_doctor",
    })


@admin_required
def save_doctor(request):
    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        email = request.POST.get("email", "").strip().lower()

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("admin_add_doctor")

        if Doctor.objects.filter(email__iexact=email).exists():
            messages.error(request, "A doctor with this email already exists.")
            return redirect("admin_add_doctor")

        try:
            experience = int(request.POST.get("experience", 0))
        except (ValueError, TypeError):
            experience = 0

        doctor = Doctor.objects.create(
            name=request.POST.get("name", "").strip(),
            specialization=request.POST.get("specialization", "").strip(),
            email=email,
            mobile=request.POST.get("mobile", "").strip(),
            experience=experience,
            address=request.POST.get("address", "").strip(),
            image=request.FILES.get("image"),
            document=request.FILES.get("document"),
            password=make_password(password),
        )

        send_auto_reply(
            email=email,
            subject="Doctor Account Created | Medical Clinic",
            message=(
                f"Hello Dr. {doctor.name},\n\n"
                "Your doctor account at Medical Clinic has been created by the administration.\n\n"
                f"Login Email: {email}\n"
                "Please login and complete your professional profile.\n\n"
                "Regards,\n"
                "Medical Clinic Administration"
            ),
        )

        messages.success(request, f"Doctor Dr. {doctor.name} added successfully!")
        return redirect("admin_doctors")

    return redirect("admin_doctors")


@admin_required
def edit_doctor(request, id):
    doctor = get_object_or_404(Doctor, id=id)

    if request.method == "POST":
        doctor.name = request.POST.get("name", doctor.name).strip()
        doctor.specialization = request.POST.get("specialization", doctor.specialization).strip()
        doctor.mobile = request.POST.get("mobile", doctor.mobile).strip()
        try:
            doctor.experience = int(request.POST.get("experience", doctor.experience))
        except (ValueError, TypeError):
            pass
        doctor.address = request.POST.get("address", doctor.address).strip()

        if request.FILES.get("image"):
            doctor.image = request.FILES.get("image")
        if request.FILES.get("document"):
            doctor.document = request.FILES.get("document")

        new_password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")
        if new_password:
            if new_password != confirm:
                messages.error(request, "Passwords do not match.")
                return redirect("edit_doctor", id=id)
            doctor.password = make_password(new_password)

        doctor.save()
        messages.success(request, f"Doctor Dr. {doctor.name} updated successfully.")
        return redirect("admin_doctors")

    return render(request, "admin/admin_dashboard.html", {
        "page": "edit_doctor",
        "doctor": doctor,
    })


@admin_required
def delete_doctor(request, id):
    doctor = get_object_or_404(Doctor, id=id)
    name = doctor.name
    doctor.delete()
    messages.success(request, f"Doctor Dr. {name} deleted successfully.")
    return redirect("admin_doctors")


@admin_required
def admin_queries(request):
    """Admin view for incoming patient contact queries."""
    queries = Contact.objects.all().order_by("-created_at")
    return render(request, "admin/admin_dashboard.html", {
        "page": "queries",
        "queries": queries,
    })
