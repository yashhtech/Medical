from django.db import models
from django.contrib.auth.models import User


class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

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

    def __str__(self):
        return self.name



class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    


class Doctor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField()
    address = models.TextField()

    # 🔥 NEW FIELDS
    bio = models.TextField(blank=True)
    hobbies = models.CharField(max_length=255, blank=True)
    qualification = models.CharField(max_length=255, blank=True)

    image = models.ImageField(upload_to="doctors/images/", blank=True, null=True)
    document = models.FileField(upload_to="doctors/docs/", blank=True, null=True)

    is_profile_completed = models.BooleanField(default=False)

    password = models.CharField(max_length=255)


    def __str__(self):
        return self.name





class Appointment(models.Model):
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

    date = models.DateField()
    time = models.CharField(max_length=20)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    message = models.TextField(blank=True)

    amount = models.IntegerField(default=300)
    status = models.CharField(
        max_length=20,
        default="Confirmed"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} → {self.doctor} ({self.date} {self.time})"


class ChatThread(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="chat"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

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
    
    def __str__(self):
        return f"{self.sender}: {self.message[:30]}"
