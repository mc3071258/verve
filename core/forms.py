from django import forms
from core.models import Prompt
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

User = get_user_model()

class PromptForm(forms.ModelForm):
    text = forms.CharField(max_length=250, help_text="Please enter the prompt")    

    class Meta:
        model = Prompt
        fields = ["game", "text"]

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
