from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random

def generate_otp(user):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    user.otp = otp
    user.otp_valid_until = timezone.now() + timedelta(minutes=10)
    user.save()
    send_mail(
        'Your Registration OTP',
        f'Your OTP for registration is: {otp}. Valid for 10 minutes.',
        'from@yourdomain.com',
        [user.email],
        fail_silently=False,
    )
    return otp

def generate_name_from_email(email):
    first_name = email.split('@')[0]
    last_name = email.split('@')[1].split('.')[0]
    return first_name, last_name    

