import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_auto_reply(email, subject, message):
    if not email:
        return False
    from_email = getattr(
        settings,
        "DEFAULT_FROM_EMAIL",
        getattr(settings, "EMAIL_HOST_USER", "noreply@medicalclinic.com")
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=True,
        )
        return True
    except Exception as exc:
        logger.warning(f"Failed to send email to {email}: {exc}")
        return False



