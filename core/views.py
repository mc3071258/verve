from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import UserForm, UserProfileForm
from .models import Profile

User = get_user_model()

def home(request):
    return render(request, "home.html")

def register(request):
    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save()

                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            
            auth_login(request, user)
            return redirect("home")
    else:
        user_form =  UserForm()
        profile_form = UserProfileForm()

    return render(request, "auth/register.html", {
        "user_form": user_form,
        "profile_form": profile_form
    })

def logout(request):
    auth_logout(request)
    return redirect("home")

def login(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request=request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect("home")
        else:
            return render(request, "auth/login.html", {
                "error": "This username or password is invalid!"
            })
    return render(request, 'auth/login.html')

@login_required
def my_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, "profiles/my_profile.html", {
        "profile_user": request.user,
        "profile": profile,
        "edit_mode": False
    })

@login_required
def my_profile_edit(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == "POST":
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect("my_profile")
        else:
            profile_form = UserProfileForm(instance=profile)

        return render(request, "profiles/edit_profile.html",{
            "profile_form": profile_form,
            "profile": profile
        })

def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)

    return render(request, "profiles/profile.html", {
        "profile_user": user,
        "profile": profile
    })