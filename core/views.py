from django.shortcuts import render
from core.forms import UserForm, UserProfileForm

# Create your views here.

from django.http import HttpResponse

def home(request):
    return render(request, "core/home.html")

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