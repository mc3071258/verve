from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction
from core.forms import UserForm, UserProfileForm

def home(request):
    return render(request, "home.html")

# Auth
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect("home")
        else:
            # Invalid creds
            return render(request, "auth/login.html", {"error": "Invalid username or password"})
    
    return render(request, "auth/login.html")

def register(request):
    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        # Write to DB if both forms valid   
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            auth_login(request, user)
            return redirect("home")
    else:
        # Get requests give them empty forms
        user_form = UserForm()
        profile_form = UserProfileForm()
    
    return render(request, "auth/register.html", {"user_form": user_form, "profile_form": profile_form})

def logout(request):
    auth_logout(request)
    return redirect("home")

# Games
def game(request, slug):
    return render(request, "games/game.html", {"slug": slug})

def game_play(request, slug):
    return render(request, "games/play.html", {"slug": slug})

def game_prompts(request, slug):
    return render(request, "games/prompts.html", {"slug": slug})

# Prompts
@login_required
def create_prompt(request):
    return render(request, "prompts/create.html")


# Profiles
@login_required
def my_profile(request):
    return render(request, "profiles/my_profile.html", {"edit_mode": False})

@login_required
def my_profile_edit(request):
    return render(request, "profiles/my_profile.html", {"edit_mode": True})

def profile(request, username):
    return render(request, "profiles/profile.html", {"username": username})

