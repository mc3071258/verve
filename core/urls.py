from django.urls import path
from . import views
from django.http import HttpResponse

urlpatterns = [
    path("", views.home, name="home"),
    path('create_prompt/', views.create_prompt, name='create_prompt'),

]

def home(request):
    return HttpResponse("Home page works")  