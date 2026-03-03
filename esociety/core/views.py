from django.shortcuts import render,redirect
from .forms import UserSignupForm,UserLoginForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
import threading
import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# Create your views here.
def userSignupView(request):

    signup_form = UserSignupForm(request.POST or None)
    login_form = AuthenticationForm()
   
    active_form = "signup"

    if request.method == "POST":
        if signup_form.is_valid():
            user = signup_form.save()

            threading.Thread(
                target=send_welcome_email,
                args=(user,),
                daemon=True
            ).start()

            messages.success(
                request,
                "Account created successfully! now you can login."
            )

            return redirect("login")
        
    return render(request, "core/auth.html", {
        "login_form": login_form,
        "signup_form": signup_form,
        "active_form": active_form,
        
    })
    
def userLoginview(request):

    login_form = AuthenticationForm(request, data=request.POST or None)
    signup_form = UserSignupForm()
    
    active_form = "signin"

    if request.method == "POST":
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)

            if user.role == "Admin":
                return redirect("admin_dashboard")
            elif user.role == "Resident":
                return redirect("resident_dashboard")
            elif user.role == "Securityguard":
                return redirect("security_dashboard")
            else:
                return redirect("home")

        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "core/auth.html", {
        "login_form": login_form,
        "signup_form": signup_form,
        "active_form": active_form,
        
    })
   
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
    image_path = os.path.join(settings.BASE_DIR, 'static/images/welcome.png')
    email_message.attach_file(image_path)

    email_message.send()



