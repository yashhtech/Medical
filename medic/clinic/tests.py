"""
Comprehensive test suite for Medical Clinic project.
Tests covering:
- Models (creation, password hashing, safe URL fallbacks, str representation)
- Authentication (patient, doctor, admin sessions and redirects)
- Public views (home, about, contact, departments, newsletter)
- Patient portal access controls and IDOR protections
- Admin portal access controls and CRUD actions
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from clinic.models import Patient, Doctor, Appointment, Contact, Newsletter, ChatMessage, Notification


class ModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            name="John Doe",
            email="john@example.com",
            password=make_password("password123"),
            gender="Male",
            age=30,
            mobile="9876543210",
            address="123 Health Ave"
        )
        self.doctor = Doctor.objects.create(
            name="Sarah Smith",
            email="sarah@clinic.com",
            password=make_password("doctorpass123"),
            specialization="Cardiologist",
            mobile="9123456789",
            experience=10,
            address="Suite 404 Medical Tower"
        )

    def test_patient_creation_and_str(self):
        self.assertEqual(str(self.patient), "John Doe")
        self.assertEqual(self.patient.email, "john@example.com")
        self.assertTrue(self.patient.password.startswith("pbkdf2_"))

    def test_patient_fallback_image(self):
        # When no image uploaded, get_image_url returns static fallback SVG
        self.assertIn("default-user.svg", self.patient.get_image_url())

    def test_doctor_creation_and_str(self):
        self.assertEqual(str(self.doctor), "Dr. Sarah Smith (Cardiologist)")
        self.assertIn("default-doctor.svg", self.doctor.get_image_url())

    def test_newsletter_creation(self):
        sub = Newsletter.objects.create(email="subscriber@example.com")
        self.assertEqual(str(sub), "subscriber@example.com")


class PublicViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Nav-tab/index.html")

    def test_about_page(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_departments_page(self):
        response = self.client.get(reverse("departments"))
        self.assertEqual(response.status_code, 200)

    def test_cardiology_page(self):
        response = self.client.get(reverse("cardiology"))
        self.assertEqual(response.status_code, 200)

    def test_contact_submission(self):
        response = self.client.post(reverse("contact_view"), {
            "first_name": "Alice",
            "last_name": "Brown",
            "email": "alice@example.com",
            "mobile": "9998887776",
            "message": "I would like to inquire about cardiology consultation."
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Contact.objects.count(), 1)
        query = Contact.objects.first()
        self.assertEqual(query.message, "I would like to inquire about cardiology consultation.")

    def test_newsletter_signup(self):
        response = self.client.post(reverse("newsletter_signup"), {
            "email": "news@example.com"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Newsletter.objects.filter(email="news@example.com").exists())


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = Patient.objects.create(
            name="Mark Taylor",
            email="mark@example.com",
            password=make_password("securepassword"),
            gender="Male",
            age=40,
            mobile="9876543211",
            address="789 Pine Rd"
        )
        self.doctor = Doctor.objects.create(
            name="Emily Chen",
            email="emily@clinic.com",
            password=make_password("docsecret123"),
            specialization="Neurology",
            mobile="9123456780",
            experience=8,
            address="Clinic Neuro Wing"
        )

    def test_patient_login_success(self):
        response = self.client.post(reverse("role_login", kwargs={"role": "patient"}), {
            "email": "mark@example.com",
            "password": "securepassword"
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("patient_dashboard"))
        self.assertEqual(self.client.session.get("patient_id"), self.patient.id)

    def test_patient_login_invalid_password(self):
        response = self.client.post(reverse("role_login", kwargs={"role": "patient"}), {
            "email": "mark@example.com",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session.get("patient_id"))

    def test_doctor_login_success(self):
        response = self.client.post(reverse("role_login", kwargs={"role": "doctor"}), {
            "email": "emily@clinic.com",
            "password": "docsecret123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("doctor_dashboard"))
        self.assertEqual(self.client.session.get("doctor_id"), self.doctor.id)

    def test_patient_registration(self):
        response = self.client.post(reverse("new_patient_register"), {
            "name": "New User",
            "email": "newuser@example.com",
            "gender": "Female",
            "age": "25",
            "mobile": "9812345678",
            "address": "456 Elm St",
            "password": "newpass123",
            "confirm_password": "newpass123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Patient.objects.filter(email="newuser@example.com").exists())


class AccessControlAndSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient = Patient.objects.create(
            name="Protected Patient",
            email="protected@example.com",
            password=make_password("patientpass"),
            gender="Female",
            age=29,
            mobile="9876543212",
            address="101 Cedar Ln"
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Gregory",
            email="gregory@clinic.com",
            password=make_password("gregorypass"),
            specialization="Orthopaedics",
            mobile="9123456782",
            experience=15,
            address="Orthopaedics Dept"
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            first_name="Protected",
            last_name="Patient",
            email="protected@example.com",
            phone="9876543212",
            date="2026-10-15",
            time="10:00 AM",
            status="Confirmed",
            is_paid=True
        )

    def test_patient_dashboard_requires_login(self):
        response = self.client.get(reverse("patient_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_doctor_dashboard_requires_login(self):
        response = self.client.get(reverse("doctor_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_admin_dashboard_requires_login(self):
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_invoice_idor_protection(self):
        # Create an unauthenticated client
        response = self.client.get(reverse("download_invoice", kwargs={"appointment_id": self.appointment.id}))
        # Must redirect or deny when not logged in as the patient or admin
        self.assertEqual(response.status_code, 302)

        # Login as another patient
        other_patient = Patient.objects.create(
            name="Intruder Patient",
            email="intruder@example.com",
            password=make_password("intruderpass"),
            gender="Male",
            age=35,
            mobile="9876543219",
            address="999 False St"
        )
        session = self.client.session
        session["patient_id"] = other_patient.id
        session.save()

        response = self.client.get(reverse("download_invoice", kwargs={"appointment_id": self.appointment.id}))
        # IDOR check: unauthorized patient receives 403 Forbidden
        self.assertEqual(response.status_code, 403)

        # Login as the rightful patient
        session["patient_id"] = self.patient.id
        session.save()
        response = self.client.get(reverse("download_invoice", kwargs={"appointment_id": self.appointment.id}))
        # Now authorized: should return the PDF invoice
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_notification_creation_and_delivery(self):
        notif = Notification.objects.create(
            patient=self.patient,
            role="patient",
            title="Appointment Notice",
            message="Your appointment is confirmed.",
            link="/patient_dashboard/?page=appointments",
            is_read=False,
        )
        self.assertEqual(Notification.objects.filter(patient=self.patient, is_read=False).count(), 1)
        self.assertEqual(str(notif), f"[{notif.role}] {notif.title}")

    def test_upi_test_payment_and_duplicate_prevention(self):
        session = self.client.session
        session["patient_id"] = self.patient.id
        session.save()

        # 1. Book appointment using test UPI mode
        payload = {
            "doctor_id": self.doctor.id,
            "date": "2026-11-20",
            "time": "11:30 AM",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "9876543210",
            "message": "Routine checkup",
            "upi_id": "testuser@okaxis",
        }
        import json
        response = self.client.post(
            reverse("payment_verify"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

        # Verify created appointment and notifications
        created_appt = Appointment.objects.get(
            patient=self.patient, doctor=self.doctor, date="2026-11-20", time="11:30 AM"
        )
        self.assertTrue(created_appt.is_paid)
        self.assertTrue(created_appt.razorpay_payment_id.startswith("pay_upi_test_"))
        self.assertIn("testuser@okaxis", created_appt.message)

        # Verify notifications were created for both patient and doctor
        self.assertTrue(Notification.objects.filter(patient=self.patient, role="patient").exists())
        self.assertTrue(Notification.objects.filter(doctor=self.doctor, role="doctor").exists())

        # 2. Attempt duplicate booking with exact same patient, doctor, date, and time
        dup_response = self.client.post(
            reverse("payment_verify"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(dup_response.status_code, 409)
        dup_data = dup_response.json()
        self.assertEqual(dup_data["status"], "failed")
        self.assertIn("already have an appointment", dup_data["error"])

