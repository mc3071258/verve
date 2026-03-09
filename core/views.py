from django.shortcuts import render
from core.forms import UserForm, UserProfileForm
from django.db import transaction
from django.http import HttpResponse
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

def register(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                user.set_password(user.password)
                user.save()

                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()

            registered = True
        # else: let template display errors

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(
        request,
        'core/register.html',
        {
            'user_form': user_form,
            'profile_form': profile_form,
            'registered': registered
        }
    )