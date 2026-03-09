from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

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