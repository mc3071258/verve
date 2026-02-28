from django.db import models
from django.conf import settings
from django.db.models import Q, F

# Use AUTH_USER_MODEL to aviod hardcoding User

class Game(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name
    
class Prompt(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Truncate to aviod visibility issues in admin
        return f"{self.game.name}: {self.text[:30]}"
    
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to="profile_pics/")

    def __str__(self):
        return f"Profile: {self.user.username}"
    
class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    # No duplicate follows
    # User cannot follow themselves
    class Meta:
        constraints = [models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_pair"),
                       models.CheckConstraint(condition=~Q(follower=F("following")), name="no_self_follow"),
                       ]
    