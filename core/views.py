from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from core.models import Prompt, Vote, Profile, Game
from core.forms import UserForm, UserProfileForm, PromptForm, GameForm, TruthOrDareForm

User = get_user_model()

def home(request):
    prompt_list = (
        Prompt.objects.annotate(upvote_count=Count("votes")).order_by("-upvote_count")[:5]
    )
    voted_prompts_list = set()

    if request.user.is_authenticated:
        voted_prompts_list = set(
            Vote.objects.filter(voter=request.user).values_list("prompt_id", flat=True)
        )

    else:
        if request.session.session_key:
            voted_prompts_list = set(
                Vote.objects.filter(guest_session_id=request.session.session_key)
                .values_list("prompt_id", flat=True)
            )

    context_dict = {}
    context_dict["prompts"] = prompt_list
    context_dict["voted_prompts"] = voted_prompts_list

    return render(request, "home.html", context=context_dict)

# Prompts
@login_required
def create_prompt(request, slug):
    game = get_object_or_404(Game, slug=slug)


    if game.slug == "truth-or-dare":
        FormClass = TruthOrDareForm
    else:
        FormClass = PromptForm

    if request.method == "POST":
        form = FormClass(request.POST)
    
        if form.is_valid():
            with transaction.atomic():
                prompt = form.save(commit=False)
                prompt.creator = request.user
                prompt.game = game
                prompt.save()
                
            return redirect("home")

    else:
        form = FormClass

    return render(request, "prompts/create.html", {"form": form, "game": game})

def choose_game(request):
    form = GameForm()

    if request.method == "POST":
        form = GameForm(request.POST)
        if form.is_valid():
            game = form.cleaned_data["game"]
            return redirect("create_prompt", slug=game.slug)

    return render(request, "prompts/choose_game.html", {"form": form})

@require_POST
def upvote_prompt(request, prompt_id):
    prompt = get_object_or_404(Prompt, id=prompt_id)
    if request.user.is_authenticated:
        voter = request.user
        session_id = None
    else:
        if not request.session.session_key:
            request.session.save()

        voter = None
        session_id = request.session.session_key

    try:
        Vote.objects.create(
            prompt=prompt,
            voter=voter,
            guest_session_id=session_id
        )
    except IntegrityError:
        pass

    return redirect("home")

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
    form = PromptForm()

    if request.method == "POST":
        form = PromptForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                prompt = form.save(commit=False)
                prompt.creator = request.user
                prompt.save()

            return redirect("home")

    return render(request, "prompts/create.html", {"form":form})

# Profiles
@login_required
def my_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, "profiles/my_profile.html", {
        "profile_user": request.user,
        "profile": profile,
        "edit_mode": False})


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

    return render(request, "profiles/edit_profile.html", {
        "profile_form": profile_form
    })

@login_required
def my_prompts(request):
    context_dict = {"edit_mode": False}
    current_user = request.user
    user_prompts = Prompt.objects.annotate(upvote_count=Count("votes")).filter(creator=current_user)
    
    context_dict["prompts"] = user_prompts
    
    return render(request, "profiles/my_prompts.html", context_dict)

@login_required
def edit_prompt(request, prompt_id):
    context_dict = {}
    prompt_inst = get_object_or_404(Prompt, id=prompt_id)

    if prompt_inst.creator == request.user:
        context_dict["prompt"] = prompt_inst
        if request.method == "POST":
                new_text = request.POST.get("text")
                if len(new_text) > 0 and len(new_text) < 250:
                    prompt_inst.text = request.POST.get("text")
                    prompt_inst.save()
                else:
                    context_dict["error"] = "Input of invalid length."
    else:
        context_dict["auth_error"] = "You are not the creator of this prompt."
    
    return render(request, "prompts/edit.html", context_dict)

def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)

    return render(request, "profiles/profile.html", {
        "profile_user": user,
        "profile": profile})

