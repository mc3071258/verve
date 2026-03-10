from django.shortcuts import render
from django.shortcuts import redirect

from core.models import Profile, Prompt
from django.contrib.auth.models import User
from core.forms import PromptForm

# Create your views here.

from django.http import HttpResponse

def home(request):
    prompt_list = Prompt.objects.order_by('-upvotes')[:5]
    context_dict = {}
    context_dict['boldmessage'] = 'Crunchy'
    context_dict['prompts'] = prompt_list

    return render(request, "core/home.html", context=context_dict)

def create_prompt(request):
    form = PromptForm()

    if request.method == "POST":
        form = PromptForm(request.POST)
    
        if form.is_valid():
            prompt = form.save(commit=False)
            prompt.creator = User.objects.filter(is_superuser=True).first()
            prompt.save()
            
            #THIS MAY BE INCORRECT
            return redirect('/')
        else:
            print(form.errors)

    return render(request, 'core/create_prompt.html', {'form': form})



