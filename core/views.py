from django.db import transaction, IntegrityError
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Count
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from core.models import Prompt, Vote, Profile, Game, Follow
from core.forms import UserForm, UserProfileForm, GameForm, TruthOrDareForm, NeverHaveIEverForm, WouldYouRatherForm

User = get_user_model()

# Helper function
def _get_voted_prompts(request):
    """Return set of prompt IDs the current user/guest has voted on."""
    if request.user.is_authenticated:
        return set(
            Vote.objects.filter(voter=request.user)
            .values_list("prompt_id", flat=True)
        )
    if request.session.session_key:
        return set(
            Vote.objects.filter(guest_session_id=request.session.session_key)
            .values_list("prompt_id", flat=True)
        )
    return set()

def _get_prompt_form(slug):
    """Return the correct form class for a game slug."""
    if slug == "truth-or-dare":
        return TruthOrDareForm
    elif slug == "would-you-rather":
        return WouldYouRatherForm
    return NeverHaveIEverForm

def _get_profile_context(user):
    """Return common profile context for a given user."""
    return {
        "profile": get_object_or_404(Profile, user=user),
        "profile_user": user,
        "follower_count": Follow.objects.filter(following=user).count(),
        "following_count": Follow.objects.filter(follower=user).count(),
        "following_users": User.objects.filter(followers__follower=user),
        "user_prompts": (
            Prompt.objects.filter(creator=user)
            .annotate(upvote_count=Count("votes"))
            .order_by("game__name", "-upvote_count")
            .distinct()
        ),
    }

# Home page
def home(request):
    # Top 5 prompts by upvote count 
    prompt_list = (
        Prompt.objects.annotate(upvote_count=Count("votes")).order_by("-upvote_count")[:5]
    )

    context_dict = {}
    context_dict["prompts"] = prompt_list
    context_dict["voted_prompts"] = _get_voted_prompts(request)

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
    if request.user.is_authenticated:
        return redirect("home")
    
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
    if request.user.is_authenticated:
        return redirect("home")
    
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
    #fetch the game object by slug, or return 404 if it doesn't exist.
    game = get_object_or_404(Game, slug=slug)
    return render(request, "games/game.html", {"slug": game.slug, "game_title": game.name, "game_description":game.description,})

# Game prompts page
def game_prompts(request, slug):
    #get the game or return 404
    game = get_object_or_404(Game, slug=slug)

    # Query prompts for this game
    # Annotate each prompt with its vote count
    # Order prompts by most upvoted first
    prompt_list = (
        Prompt.objects
            .filter(game=game)
            .annotate(upvote_count=Count("votes"))
            .order_by("-upvote_count")
    )

    voted_prompts = _get_voted_prompts(request)

    context_dict = {}
    context_dict["game"] = game
    context_dict["prompt_list"] = prompt_list
    context_dict["voted_prompts"] = voted_prompts

    return render(request, "games/prompts.html", context = context_dict)

def game_play(request, slug):
    #get game or return 404.
    game = get_object_or_404(Game, slug=slug)
    context_dict = {}

    #games that share same logic (just a list of prompts)
    games_with_same_logic = ["would-you-rather", "never-have-i-ever"]

    if slug in games_with_same_logic:
        #get all prompts as a simple list of text strings
        prompt_list = list(
            Prompt.objects
                .filter(game=game)
                .annotate(upvote_count=Count("votes"))
                .order_by("-upvote_count")
                .values_list("text", flat=True)
        )

        context_dict["prompts"] = prompt_list

    elif slug == "truth-or-dare":
        #Seperate prompts into truth list and dare list.
        truth_list = list(
            Prompt.objects
                .filter(game=game, category="truth")
                .annotate(upvote_count=Count("votes"))
                .order_by("-upvote_count")
                .values_list("text", flat=True)       
        )

        dare_list = list(
            Prompt.objects
                .filter(game=game, category="dare")
                .annotate(upvote_count=Count("votes"))
                .order_by("-upvote_count")
                .values_list("text", flat=True)
        )

        context_dict["truth_prompts"] = truth_list
        context_dict["dare_prompts"] =  dare_list

    else:
        # If slug doesn't match any known game logic, return 404
        raise Http404("Game not found")
    
    # Use user supplied slug, safe as else block handles invalid slugs
    template_name = f"games/{slug}/play.html" 

    return render(request, template_name, context = context_dict)
    
# Profiles
@login_required
def my_profile(request):
    context = _get_profile_context(request.user)
    context["favourites"] = (
        Prompt.objects.filter(votes__voter=request.user)
        .annotate(upvote_count=Count("votes"))
        .order_by("game__name", "-upvote_count")
        .distinct()
    )
    return render(request, "profiles/my_profile.html", context)

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

def profile(request, username):
    user = get_object_or_404(User, username=username)
    context = _get_profile_context(user)
    context["is_following"] = (
        request.user.is_authenticated
        and request.user != user
        and Follow.objects.filter(follower=request.user, following=user).exists()
    )
    return render(request, "profiles/profile.html", context)

# Prompts
@require_POST
def upvote_prompt(request, prompt_id):
    # Toggle vote on a prompt, return JSON for AJAX or redirect for forms.
    prompt = get_object_or_404(Prompt, id=prompt_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.user.is_authenticated and request.user == prompt.creator:
        if is_ajax:
            return JsonResponse({"error": "Cannot vote on own prompt"}, status=403)
        return redirect(request.META.get("HTTP_REFERER", "home"))

    if request.user.is_authenticated:
        voter = request.user
        session_id = None
    else:
        if not request.session.session_key:
            request.session.save()
        voter = None
        session_id = request.session.session_key

    if voter:
        existing = Vote.objects.filter(prompt=prompt, voter=voter)
    else:
        existing = Vote.objects.filter(prompt=prompt, guest_session_id=session_id)

    if existing.exists():
        existing.delete()
        voted = False
    else:
        try:
            Vote.objects.create(prompt=prompt, voter=voter, guest_session_id=session_id)
            voted = True
        except IntegrityError:
            voted = True

    vote_count = Vote.objects.filter(prompt=prompt).count()

    if is_ajax:
        return JsonResponse({"voted": voted, "vote_count": vote_count})

    return redirect(request.META.get("HTTP_REFERER", "home"))

@login_required
def create_prompt(request, slug):
    #get game object by slug or return 404 if not found
    game = get_object_or_404(Game, slug=slug)

    #Choose the correct game form based on the game type
    FormClass = _get_prompt_form(game.slug)

    if request.method == "POST":
        form = FormClass(request.POST)
    
        if form.is_valid():
            with transaction.atomic():
                #create prompts object but dont save to the DB yet.
                prompt = form.save(commit=False)

                #add additional fields not included in the form.
                prompt.creator = request.user
                prompt.game = game

                #save completed prompt to the database.
                prompt.save()
                
            return redirect("my_prompts")
        else:
            return render(request, "prompts/create.html", {"form": form, "game": game})

    else:
        #if GET request, initialise an empty form
        form = FormClass()

    return render(request, "prompts/create.html", {"form": form, "game": game})

@login_required
def my_prompts(request):
    context_dict = {}
    current_user = request.user
    user_prompts = Prompt.objects.annotate(upvote_count=Count("votes")).filter(creator=current_user)
    
    context_dict["prompts"] = user_prompts
    
    return render(request, "profiles/my_prompts.html", context_dict)

@login_required
def edit_prompt(request, prompt_id):
    prompt_inst = get_object_or_404(Prompt, id=prompt_id, creator=request.user)
    game = prompt_inst.game

    FormClass = _get_prompt_form(game.slug)

    if request.method == "POST":
        form = FormClass(request.POST, instance=prompt_inst)
    
        if form.is_valid():
            form.save()
            return redirect("my_prompts")
        
    else:
        if game.slug == "would-you-rather":
            parts = prompt_inst.text.split("|", 1)
            initial = {
                "optionA": parts[0].strip(),
                "optionB": parts[1].strip() if len(parts) > 1 else "",
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

# Follow
@login_required
@require_POST
def follow_user(request, username):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        target_user = get_object_or_404(User, username=username)

        if request.user == target_user:
            if is_ajax:
                return JsonResponse({"error": "Cannot follow yourself"}, status=403)
            return redirect("profile", username=username)

        Follow.objects.get_or_create(
            follower=request.user,
            following=target_user)
            
        follower_count = Follow.objects.filter(following=target_user).count()

        if is_ajax:
            return JsonResponse({
                "following": True,
                "follower_count": follower_count,
                "next_url": reverse("unfollow_user", args=[target_user.username]),})
            
    return redirect("profile", username=username)

@require_POST
@login_required
def unfollow_user(request, username):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        target_user = get_object_or_404(User, username=username)

        Follow.objects.filter(
            follower=request.user,
            following=target_user).delete()
        
        follower_count = Follow.objects.filter(following=target_user).count()

        if is_ajax:
            return JsonResponse({
                "following": False,
                "follower_count": follower_count,
                "next_url": reverse("follow_user", args=[target_user.username]),})
    
    return redirect("profile", username=username)
