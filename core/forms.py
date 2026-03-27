from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Prompt, Game

User = get_user_model()


class BasePromptForm(forms.ModelForm):
    text = forms.CharField(required=True, max_length=250, help_text="Please enter the prompt") 

    class Meta:
        model = Prompt
        fields = ["text"]

class NeverHaveIEverForm(BasePromptForm):
    pass

class TruthOrDareForm(BasePromptForm):
    category = forms.ChoiceField(choices=Prompt.CATEGORY_CHOICES, help_text="Is it a truth or a dare")

    class Meta(BasePromptForm.Meta):
        fields = ["text", "category"]

class WouldYouRatherForm(forms.ModelForm):
    optionA = forms.CharField(required=True, max_length=250, help_text="Please enter option 1")
    optionB = forms.CharField(required=True, max_length=250, help_text="Please enter option 2")

    class Meta:
        model = Prompt
        fields = []

    def _clean_option(self, field_name):
        value = self.cleaned_data[field_name]
        if "|" in value:
            raise forms.ValidationError("Character '|' is not allowed.")
        return value

    def clean_optionA(self):
        return self._clean_option("optionA")

    def clean_optionB(self):
        return self._clean_option("optionB")

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."

class UserProfileForm(forms.ModelForm):
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), max_length=200, help_text="Tell us about yourself (max 200 characters)")

    class Meta:
        model = Profile
        fields = ["bio", "profile_picture"]