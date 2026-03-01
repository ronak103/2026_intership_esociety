from django.shortcuts import render,redirect
from .forms import UserSignupForm,UserLoginForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# Create your views here.
def userSignupView(request):

    form = UserSignupForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():
            user = form.save()

            # Send email in background
            threading.Thread(
                target=send_welcome_email,
                args=(user,),
                daemon=True
            ).start()

            messages.success(request, "Account created successfully! Please login.")
            return redirect("login")

    return render(request, "core/signup.html", {"form": form})

    
def userLoginview(request):

    form = UserLoginForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)

                if user.role == "Admin":
                    return redirect("admin_dashboard")
                elif user.role == "Resident":
                    return redirect("resident_dashboard")
                elif user.role == "Securityguard":
                    return redirect("security_dashboard")
            else:
                # 🔴 Wrong credentials
                form.add_error(None, "Invalid email or password.")

    return render(request, "core/login.html", {"form": form})
   
def LogoutView(request):
    logout(request)
    return redirect("login") 

def send_welcome_email(user):
    subject = "Welcome to E-Society"
    from_email = settings.EMAIL_HOST_USER
    to = [user.email]

    html_content = render_to_string(
        "core/welcome_email.html",
        {"first_name": user.first_name}
    )

    email_message = EmailMultiAlternatives(
        subject,
        "Welcome to E-Society",
        from_email,
        to
    )

    email_message.attach_alternative(html_content, "text/html")
    email_message.send()

from django.contrib.auth import login

def authView(request):
    login_form = AuthenticationForm()
    signup_form = UserSignupForm()
    active_form = 'signup' if request.resolver_match and request.resolver_match.url_name == 'signup' else 'signin'

    if request.method == "POST":

        if 'signup_submit' in request.POST:
            active_form = 'signup'
            signup_form = UserSignupForm(request.POST)
            if signup_form.is_valid():
                user = signup_form.save()
                threading.Thread(target=send_welcome_email, args=(user,), daemon=True).start()
                messages.success(request, "Account created! Please login.")
                return redirect("login")

        elif 'signin_submit' in request.POST:
            active_form = 'signin'
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)

                # Role based redirect
                role = user.role  # adjust field name if different

                if role == 'Admin':
                    return redirect('admin_dashboard')
                elif role == 'Resident':
                    return redirect('resident_dashboard')
                elif role == 'Security':
                    return redirect('security_dashboard')
                else:
                    return redirect('home')  # fallback

    return render(request, "core/auth.html", {
        'login_form': login_form,
        'signup_form': signup_form,
        'active_form': active_form,
    })