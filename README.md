# 🏥 Medical Clinic — Comprehensive Healthcare Management Portal

A modernized, secure, and production-ready healthcare management web platform developed with **Django 6**, modern CSS, and SQLite/PostgreSQL support.

---

## 🌟 Key Features

### 👤 Patient Portal
- **Secure Registration & Login**: Custom hashed credential storage with session authentication.
- **Doctor Discovery**: Filter clinicians by medical specialization, search by name, view qualifications and bios.
- **Appointment Scheduling**: Interactive multi-step calendar booking interface with date & time selection.
- **Payment Verification**: Test-ready Razorpay gateway integration with digital PDF invoice download (ReportLab).
- **Clinical Hub**: Patient dashboard featuring teleconsultation waiting room, lab reports, health trackers, and doctor messaging.

### 🩺 Doctor Portal
- **Practitioner Dashboard**: Quick telemetry on daily patient loads and upcoming appointments.
- **Consultation Workspace**: View patient profiles, clinical history, and direct messaging.
- **Prescription System**: Attach digital prescription notes and clinical report documents directly to appointment records.
- **Profile Customization**: Manage qualifications, specialties, bio, and credentials.

### 🔐 Administrative Command Center
- **Live Clinic Telemetry**: Dynamic count cards for registered patients, doctors, appointment bookings, and public inquiries.
- **Doctor & Patient Records Management**: Complete CRUD interface with protected POST endpoints and confirmation safeguards.
- **Inquiry Management**: Centralized inbox for public inquiries submitted through the contact form.

---

## 🛠️ Technology Stack & Architecture

- **Backend**: Python 3.13, Django 6.0
- **Static Assets & Assets Engine**: WhiteNoise with compression and cache headers
- **Document Generation**: ReportLab PDF Generation
- **Payment Gateway**: Razorpay REST SDK
- **Security & Hardening**:
  - Environment-based configuration (`python-dotenv`)
  - CSRF protections across all state-mutating requests
  - IDOR-protected invoice endpoints
  - Session-based custom role decorators (`@admin_required`, `@patient_required`, `@doctor_required`)
  - Case-insensitive email authentication

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Virtual environment (`venv`)

### 2. Installation

Clone repository and activate your virtual environment:

```bash
# Clone the repository
git clone https://github.com/your-org/medical-clinic.git
cd medical-clinic

# Activate virtual environment
# Windows:
.\myenv\Scripts\activate
# Linux/macOS:
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

Copy `.env.example` to `.env` in the root workspace and populate your credentials:

```bash
cp .env.example .env
```

Key environment variables:
- `DJANGO_SECRET_KEY`: Random high-entropy string
- `DEBUG`: `True` for local development, `False` for production
- `ADMIN_EMAIL`: Admin portal master credential
- `ADMIN_PASSWORD`: Admin portal password
- `RAZORPAY_KEY_ID`: Razorpay public key
- `RAZORPAY_KEY_SECRET`: Razorpay secret key

### 4. Database Migrations

```bash
python medic/manage.py migrate
```

### 5. Run the Test Suite

```bash
python medic/manage.py test clinic
```

### 6. Start the Development Server

```bash
python medic/manage.py runserver
```

Visit the application at: `http://127.0.0.1:8000/`

---

## 🧪 Automated Testing

The project includes an automated test suite verifying:
- Model instantiations, image fallback logic, and string representations
- Role-based authentication workflows and session persistence
- Public routes, newsletter subscriptions, and contact form handling
- IDOR access controls on patient records and PDF receipts

---

## 🔒 Security Audit Summary

- **Secrets Management**: All API keys, database secrets, and credentials migrated from codebase to `.env`.
- **Injection & IDOR Prevention**: Gated appointment invoice downloads to authenticated patient owners or authorized administrators.
- **HTTP Method Safety**: Converted destructive deletion actions from insecure GET links to CSRF-verified POST forms.
