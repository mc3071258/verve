from django.urls import path
from . import views
from django.http import HttpResponse

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home), # Add redirect later

    path("game/<slug:slug>/", views.game, name="game"),
    path("game/<slug:slug>/play/", views.game_play, name="game_play"),
    path("game/<slug:slug>/view/", views.game_prompts, name="game_prompts"),

    path("create-prompt/", views.create_prompt, name="create_prompt"),

    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),

    path("profiles/", views.my_profile, name="my_profile"),
    path("profiles/edit/", views.my_profile_edit, name="edit_profile"),
    path("profiles/<str:username>/", views.profile, name="profile"),
]


