from django import forms
from core.models import Prompt, Game
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

User = get_user_model()

class PromptForm(forms.ModelForm):
    text = forms.CharField(max_length=250, help_text="Please enter the prompt")    

    class Meta:
        model = Prompt
        fields = ["text"]

class TruthOrDareForm(forms.ModelForm):
    TRUTH_DARE_CHOICES = [
        ("truth", "Truth"),
        ("dare", "Dare"),
    ]
    truth_or_dare = forms.ChoiceField(choices=TRUTH_DARE_CHOICES)
    text = forms.CharField(max_length=250, help_text="Please enter the prompt") 

    class Meta:
        model = Prompt
        fields = ["text", "truth_or_dare"]

class GameForm(forms.Form):
    game = forms.ModelChoiceField(queryset=Game.objects.all(), 
                                empty_label="Select a game",
                                widget=forms.Select(attrs={"class": "form-select"}))


# Django's UserCreationForm
class UserForm(UserCreationForm):
    email = forms.EmailField(required=False)  # Optionally add email field later 

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "profile_picture"]
