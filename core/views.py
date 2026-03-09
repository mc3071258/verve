from django.shortcuts import render
from django.shortcuts import redirect

def home(request):
    return render(request, "home.html")

def game(request, slug):
    return render(request, "games/game.html", {"slug": slug})

def game_play(request, slug):
    return render(request, "games/play.html", {"slug": slug})

def game_prompts(request, slug):
    return render(request, "games/prompts.html", {"slug": slug})

def create_prompt(request):
    return render(request, "prompts/create.html")

def login(request):
    return render(request, "auth/login.html")

def register(request):
    return render(request, "auth/register.html")

def logout(request):
    # Add logout logic later
    return redirect("home")

def my_profile(request):
    return render(request, "profiles/my_profile.html", {"edit_mode": False})

def my_profile_edit(request):
    return render(request, "profiles/my_profile.html", {"edit_mode": True})

def profile(request, username):
    return render(request, "profiles/profile.html", {"username": username})