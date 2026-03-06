from django.contrib import admin
from .models import Prompt
from .models import Game

admin.site.register(Prompt)
admin.site.register(Game)

# Register your models here.
