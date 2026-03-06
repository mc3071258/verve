from django.urls import path
from . import views
from django.http import HttpResponse

urlpatterns = [
    path("", views.home, name="home"),
    path('register/', views.register, name="register"),
]

def home(request):
    return HttpResponse("Home page works")  