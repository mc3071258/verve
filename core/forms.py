from django import forms
from core.models import Prompt, Game
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Prompt, Game

User = get_user_model()

class NeverHaveIEverForm(forms.ModelForm):
    text = forms.CharField(required=True, max_length=250, help_text="Please enter the prompt")    

    class Meta:
        model = Prompt
        fields = ["text"]

class TruthOrDareForm(forms.ModelForm):
    TRUTH_DARE_CHOICES = [
        ("truth", "Truth"),
        ("dare", "Dare"),
    ]
    category = forms.ChoiceField(choices=TRUTH_DARE_CHOICES)
    text = forms.CharField(required=True, max_length=250, help_text="Please enter the prompt") 

    class Meta:
        model = Prompt
        fields = ["text", "category"]

class WouldYouRatherForm(forms.ModelForm):
    optionA = forms.CharField(required=True, max_length=250, help_text="Please enter option 1")
    optionB = forms.CharField(required=True, max_length=250, help_text="Please enter option 1")

    class Meta:
        model = Prompt
        fields = []

    def clean_optionA(self):
        value = self.cleaned_data["optionA"]
        if  "|" in value:
            raise forms.ValidationError("Character '|' is not allowed.")
        return value
    
    def clean_optionB(self):
        value = self.cleaned_data["optionB"]
        if  "|" in value:
            raise forms.ValidationError("Character '|' is not allowed.")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)

        optionA = self.cleaned_data["optionA"]
        optionB = self.cleaned_data["optionB"]

        instance.text = f"{optionA}|{optionB}"

        if commit:
            instance.save()
        
        return instance

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