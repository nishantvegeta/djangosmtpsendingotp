from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import RegistrationForm, OTPForm, LoginForm
from .models import OTP
import datetime
from django.utils import timezone

def home_view(request):
    return render(request, 'registration/home.html')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            otp_instance = OTP.objects.create(user=user)
            otp_instance.generate_otp()
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp_instance.otp}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
            return redirect('otp_verify')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def otp_verify(request):
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            try:
                otp_instance = OTP.objects.get(otp=otp_code)
                otp_created_at = otp_instance.created_at
                if timezone.is_naive(otp_created_at):
                    otp_created_at = timezone.make_aware(otp_created_at, timezone.get_current_timezone())

                if timezone.now() - otp_created_at < datetime.timedelta(minutes=10):
                    user = otp_instance.user
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'OTP has expired.')
            except OTP.DoesNotExist:
                messages.error(request, 'Invalid OTP.')
    else:
        form = OTPForm()
    return render(request, 'registration/otp_verify.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'registration/login.html')
