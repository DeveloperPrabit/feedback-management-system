# utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(user_email, otp):
    subject = "Your OTP for Password Reset"
    message = f"Dear user,\n\nYour OTP for resetting your password is: {otp}\n\nThis OTP will expire in 10 minutes.\n\nThank you."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
