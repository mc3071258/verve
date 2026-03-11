from django.urls import path
from . import views
from django.views.generic import RedirectView


urlpatterns = [
    path("", views.home, name="home"),
    path("home/", RedirectView.as_view(pattern_name="home", permanent=False)),

    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),

    path("profiles/", views.my_profile, name="my_profile"),
    path("profiles/edit/", views.my_profile_edit, name="edit_profile"),
    path("profiles/<str:username>/", views.profile, name="profile"),

]


