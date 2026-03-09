from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse

from django.http import HttpResponse

def home(request):
    return HttpResponse("Home page works")

def game(request, slug):
    return HttpResponse(f"Game page works: {slug}")

def game_play(request, slug):
    return HttpResponse(f"Game play works: {slug}")

def game_prompts(request, slug):
    return HttpResponse(f"Game prompts works: {slug}")

def create_prompt(request):
    return HttpResponse("Create prompt page works")

def login(request):
    return HttpResponse("Login page works")

def register(request):
    return HttpResponse("Register page works")

def logout(request):
    return HttpResponse("Logout page works")

def my_profile(request):
    return HttpResponse("My profile page works")

def my_profile_edit(request):
    return HttpResponse("Edit profile page works")

def profile(request, username):
    return HttpResponse(f"Public profile works: {username}")