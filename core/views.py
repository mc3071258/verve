from django.shortcuts import render
from core.models import Prompt

# Create your views here.

from django.http import HttpResponse

def home(request):
    prompt_list = Prompt.objects.order_by('-upvotes')[:5]
    context_dict = {}
    context_dict['boldmessage'] = 'Crunchy'
    context_dict['prompts'] = prompt_list

    return render(request, "core/home.html", context=context_dict)

