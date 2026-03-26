from django.db import models
from django.conf import settings
from django.db.models import Q, F
from django.utils.text import slugify

# Use standard pattern AUTH_USER_MODEL to aviod hardcoding User

class Game(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()

    # Auto create slug field
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Prompt(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="prompts")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prompts")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Truth or dare needs extra field (DB, display)
    CATEGORY_CHOICES = [("truth", "Truth"), ("dare", "Dare")]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)

    def __str__(self):
        # Truncate to aviod visibility issues in admin, some prompt might be too long
        return f"{self.game.name}: {self.text[:30]}"
    
    # For would you rather, split text by pipe and display as "Option 1 or Option 2"    
    @property
    def display_text(self):
        """Return formatted text, splitting WYR pipe delimiter."""
        if self.game.slug == "would-you-rather" and "|" in self.text:
            parts = self.text.split("|", 1)
            return f"Would you rather {parts[0].strip().lower()} or {parts[1].strip().lower()}"
        return self.text
    
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Allow empty bio and profile pic
    bio = models.TextField(blank=True, max_length=200)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)

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
    
class Vote(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name="votes")
    # Nullable since guest can vote
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="votes")
    guest_session_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Logged in users can only vote once per prompt
    # Guest can only vote once per prompt + per brower session
    # Either logged in or guest (XOR)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["prompt", "voter"], condition=Q(voter__isnull=False), name="unique_prompt_vote_per_user"),
            models.UniqueConstraint(fields=["prompt", "guest_session_id"], condition=Q(guest_session_id__isnull=False), name="unique_prompt_vote_per_session"),
            models.CheckConstraint(condition=(Q(voter__isnull=False, guest_session_id__isnull=True) | Q(voter__isnull=True, guest_session_id__isnull=False)) & ~Q(guest_session_id="") ,
                                   name="vote_requires_user_or_session")
        ]
    
    def __str__(self):
        if self.voter_id: 
            who = self.voter.username
        else:
            who = self.guest_session_id
        return f"{who} voted on prompt {self.prompt_id}"
    