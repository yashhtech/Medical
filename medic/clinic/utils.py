from django.core.mail import send_mail
from django.conf import settings

def send_auto_reply(email, subject, message):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


