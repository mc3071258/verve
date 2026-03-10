from django import forms
from core.models import Prompt

class PromptForm(forms.ModelForm):
    text = forms.CharField(max_length=250, help_text="Please enter the prompt")    
    slug = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Prompt
        fields = ('game', 'text')

    