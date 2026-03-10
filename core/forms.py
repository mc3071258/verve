from django import forms
from core.models import Prompt
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class PromptForm(forms.ModelForm):
    text = forms.CharField(max_length=250, help_text="Please enter the prompt")    
    slug = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Prompt
        fields = ('game', 'text')

User = get_user_model()

# Django's UserCreationForm
class UserForm(UserCreationForm):
    class Meta:
        email = forms.EmailField(required=False)  # Optionally add email field later 

        model = User
        fields = ["username", "password1", "password2"]

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "profile_picture"]
