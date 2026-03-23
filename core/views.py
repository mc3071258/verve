from django.db import transaction, IntegrityError
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from core.models import Prompt, Vote, Profile, Game, Follow
from core.forms import UserForm, UserProfileForm, GameForm, TruthOrDareForm, NeverHaveIEverForm, WouldYouRatherForm

User = get_user_model()

def home(request):
    # Top 5 prompts by upvote count 
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

@login_required
def choose_game(request):
    form = GameForm()

    if request.method == "POST":
        form = GameForm(request.POST)
        if form.is_valid():
            game = form.cleaned_data["game"]
            return redirect("create_prompt", slug=game.slug)

    return render(request, "prompts/choose_game.html", {"form": form})

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

@require_POST
def logout(request):
    auth_logout(request)
    return redirect("home")

# Games
# Game page
def game(request, slug):
    context_dict = {}
    context_dict["slug"] = slug
    context_dict["game_title"] = slug.replace("-", " ")
    
    return render(request, "games/game.html", context = context_dict)

# Game prompts page
def game_prompts(request, slug):
    game = get_object_or_404(Game, slug=slug)

    prompt_list = (
        Prompt.objects
            .filter(game=game)
            .annotate(upvote_count=Count("votes"))
            .order_by("-upvote_count")
    )

    if game.slug == "would-you-rather":
        for prompt in prompt_list:
            option_parts = prompt.text.split("|")
            prompt.optionA = option_parts[0]
            prompt.optionB = option_parts[1]

    context_dict = {}
    context_dict["game"] = game
    context_dict["prompt_list"] = prompt_list

    return render(request, "games/prompts.html", context = context_dict)

def game_play(request, slug):
    game = get_object_or_404(Game, slug=slug)
    context_dict = {}
    games_with_same_logic = ["would-you-rather", "never-have-i-ever"]

    if slug in games_with_same_logic:
        prompt_list = list(
            Prompt.objects
                .filter(game=game)
                .values_list("text", flat=True)
        )
        context_dict["prompts"] = prompt_list

    elif slug == "truth-or-dare":
        truth_list = list(
            Prompt.objects
                .filter(game=game, category="truth")
                .values_list("text", flat=True)
                
        )
        dare_list = list(
            Prompt.objects
                .filter(game=game, category="dare")
                .values_list("text", flat=True)
        )
        context_dict["truth_prompts"] = truth_list
        context_dict["dare_prompts"] =  dare_list

    else:
        raise Http404("Game not found")
    
    # Use user supplied slug, safe as else block handles invalid slugs
    template_name = f"games/{slug}/play.html" 

    return render(request, template_name, context = context_dict)
    
# Profiles
@login_required
def my_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    follower_count = Follow.objects.filter(following=request.user).count()
    following_count = Follow.objects.filter(follower=request.user).count()

    return render(request, "profiles/my_profile.html", {
        "profile_user": request.user,
        "profile": profile,
        "edit_mode": False,
        "follower_count": follower_count,
        "following_count": following_count,})

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

# Prompts
@require_POST
def upvote_prompt(request, prompt_id):
    prompt = get_object_or_404(Prompt, id=prompt_id)

    # Prevent self-voting
    if request.user.is_authenticated and request.user == prompt.creator:
        return redirect(request.META.get("HTTP_REFERER", "home"))

    if request.user.is_authenticated:
        voter = request.user
        session_id = None

    else:
        if not request.session.session_key:
            # Create a session so they get key
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

    return redirect(request.META.get("HTTP_REFERER", "home"))

@login_required
def create_prompt(request, slug):
    game = get_object_or_404(Game, slug=slug)

    if game.slug == "truth-or-dare":
        FormClass = TruthOrDareForm

    elif game.slug == "would-you-rather":
        FormClass = WouldYouRatherForm

    else:
        FormClass = NeverHaveIEverForm

    if request.method == "POST":
        form = FormClass(request.POST)
    
        if form.is_valid():
            with transaction.atomic():
                prompt = form.save(commit=False)
                prompt.creator = request.user
                prompt.game = game
                prompt.save()
                
            return redirect("my_prompts")
        else:
            return render(request, "prompts/create.html", {"form": form, "game": game})

    else:
        form = FormClass()

    return render(request, "prompts/create.html", {"form": form, "game": game})

@login_required
def my_prompts(request):
    context_dict = {}
    current_user = request.user
    user_prompts = Prompt.objects.annotate(upvote_count=Count("votes")).filter(creator=current_user)
    
    context_dict["prompts"] = user_prompts
    context_dict["del_auth_error"] = request.session.get("del_auth_error")
    
    return render(request, "profiles/my_prompts.html", context_dict)

@login_required
def edit_prompt(request, prompt_id):
    prompt_inst = get_object_or_404(Prompt, id=prompt_id, creator=request.user)
    game = prompt_inst.game

    if game.slug == "truth-or-dare":
        FormClass = TruthOrDareForm

    elif game.slug == "would-you-rather":
        FormClass = WouldYouRatherForm
    
    else:
        FormClass = NeverHaveIEverForm

    if request.method == "POST":
        form = FormClass(request.POST, instance=prompt_inst)
    
        if form.is_valid():
            form.save()
            return redirect("my_prompts")
        else:
            if game.slug == "would-you-rather":
                parts = prompt_inst.text.split("|", 1)
                initial = {
                    "optionA": parts[0],
                    "optionB": parts[1] if len(parts) > 1 else "",
                }
                form = FormClass(initial=initial, instance=prompt_inst)
            else:
                form = FormClass(instance=prompt_inst)
            
        return render(request, "prompts/edit.html", {"form": form, "prompt": prompt_inst})

@login_required
@require_POST
def del_prompt(request, prompt_id):
    prompt_inst = get_object_or_404(Prompt, id=prompt_id, creator=request.user)
    prompt_inst.delete()
    return redirect("my_prompts")

def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    is_following = False

    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(
            follower= request.user,
            following= user).exists()
        
    follower_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=profile.user).count()

    return render(request, "profiles/profile.html", {
        "profile_user": user,
        "profile": profile,
        "is_following": is_following,
        "follower_count": follower_count,
        "following_count": following_count,
        })

# Follow
@login_required
def follow_user(request, username):
    if request.method == "POST":
        target_user = get_object_or_404(User, username=username)

        if request.user != target_user:
            Follow.objects.get_or_create(
                follower=request.user,
                following=target_user)
    return redirect("profile", username=username)

@login_required
def unfollow_user(request, username):
    if request.method == "POST":
        target_user = get_object_or_404(User, username=username)

        Follow.objects.filter(
            follower=request.user,
            following=target_user).delete()
    return redirect("profile", username=username)
