from django.contrib import admin
from .models import Game, Prompt, Profile, Follow, Vote

admin.site.register(Game)
admin.site.register(Prompt)
admin.site.register(Profile)
admin.site.register(Follow)
admin.site.register(Vote)