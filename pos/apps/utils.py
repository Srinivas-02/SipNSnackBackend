from django.conf import settings
from django.core.mail import send_mail

def send_email(subject, message,  to_email_list):
    """ Send Email"""

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        to_email_list,
        fail_silently=False,
    )