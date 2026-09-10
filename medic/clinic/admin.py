from django.contrib import admin
from .models import (
    Patient,
    Doctor,
    Appointment,
    Contact,
    Newsletter,
    ChatThread,
    ChatMessage,
    Notification,
)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "mobile", "gender", "age", "created_at")
    search_fields = ("name", "email", "mobile")
    list_filter = ("gender", "created_at")
    ordering = ("-created_at",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "specialization",
        "experience",
        "mobile",
        "is_profile_completed",
    )
    search_fields = ("name", "email", "specialization")
    list_filter = ("specialization", "is_profile_completed")
    ordering = ("name",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "doctor",
        "date",
        "time",
        "status",
        "amount",
        "is_paid",
        "created_at",
    )
    list_filter = ("status", "is_paid", "date")
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "patient__name",
        "doctor__name",
        "razorpay_order_id",
        "razorpay_payment_id",
    )
    ordering = ("-date", "-created_at")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "mobile", "created_at")
    search_fields = ("first_name", "last_name", "email", "message")
    list_filter = ("created_at",)
    ordering = ("-created_at",)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("email", "subscribed_at")
    search_fields = ("email",)
    ordering = ("-subscribed_at",)


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "is_active", "created_at")
    list_filter = ("is_active", "created_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "thread", "sender", "created_at", "short_message")
    list_filter = ("sender", "created_at")

    def short_message(self, obj):
        return obj.message[:40]
    short_message.short_description = "Message"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "role", "patient", "doctor", "is_read", "created_at")
    list_filter = ("role", "is_read", "created_at")
    search_fields = ("title", "message", "patient__name", "doctor__name")
    ordering = ("-created_at",)