from django.db import models


class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-subscribed_at"]
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"

    def __str__(self):
        return self.email


class Patient(models.Model):
    salutation = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="patients/images/", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.salutation} {self.name}".strip()

    def get_image_url(self):
        if self.image:
            try:
                return self.image.url
            except ValueError:
                pass
        return "/static/images/default-user.svg"


class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Inquiry"
        verbose_name_plural = "Contact Inquiries"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Doctor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField()
    address = models.TextField()

    bio = models.TextField(blank=True)
    hobbies = models.CharField(max_length=255, blank=True)
    qualification = models.CharField(max_length=255, blank=True)

    image = models.ImageField(upload_to="doctors/images/", blank=True, null=True)
    document = models.FileField(upload_to="doctors/docs/", blank=True, null=True)

    is_profile_completed = models.BooleanField(default=False)
    password = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

    def __str__(self):
        return f"Dr. {self.name} ({self.specialization})"

    def get_image_url(self):
        if self.image:
            try:
                return self.image.url
            except ValueError:
                pass
        return "/static/images/default-doctor.svg"

    def get_document_url(self):
        if self.document:
            try:
                return self.document.url
            except ValueError:
                pass
        return None


class Appointment(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
        ("Rejected", "Rejected"),
    )

    patient = models.ForeignKey(
        "clinic.Patient",
        on_delete=models.CASCADE,
        related_name="appointments"
    )
    doctor = models.ForeignKey(
        "clinic.Doctor",
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    date = models.DateField(db_index=True)
    time = models.CharField(max_length=20)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    message = models.TextField(blank=True)

    amount = models.IntegerField(default=300)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Confirmed",
        db_index=True
    )
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    prescription_notes = models.TextField(blank=True, default="")
    prescription_file = models.FileField(upload_to="prescriptions/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"

    def __str__(self):
        return f"{self.patient} -> {self.doctor} ({self.date} {self.time})"


class ChatThread(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="chat"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chat Thread"
        verbose_name_plural = "Chat Threads"

    def __str__(self):
        return f"Chat - {self.appointment}"


class ChatMessage(models.Model):
    thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.CharField(
        max_length=50,
        choices=(("doctor", "Doctor"), ("patient", "Patient"))
    )

    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"{self.sender}: {self.message[:30]}"


class Notification(models.Model):
    RECIPIENT_ROLES = (
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("admin", "Admin"),
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    role = models.CharField(max_length=20, choices=RECIPIENT_ROLES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.role}] {self.title}"

