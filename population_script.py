import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verve.settings')

import django
from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth import get_user_model

# get_or_create also return a boolean created but we don't need it here, so using _ here
def populate():
    django.setup()

    from core.models import Game, Prompt, Follow, Vote, Profile
    User = get_user_model()

    games_data = [
        ("Truth or Dare", ""),
        ("Would You Rather", ""),
        ("Never Have I Ever", ""),
    ]

    users_data = [
        ("james", "BobPass1234!", "Hi, this is James's bio."),
        ("mary", "MaryPass1234!", "Hi, this is Mary's bio."),
    ]
    
    # game : (text, creator_name)
    prompts_data = {
        "Truth or Dare": [
            ("Truth: test1", "james"),
            ("Dare: test2", "mary"),
        ],
        "Would You Rather": [
            ("Would you rather test1", "james"),
            ("Would you rather test2", "mary"),
        ],
        "Never Have I Ever": [
            ("Never have I ever test1", "james"),
            ("Never have I ever test2", "mary"),
        ],
    }

    follow_pairs = [
        ("james", "mary"),
        ("mary", "james"),
    ]

    # (game_name, prompt_text, user_voters, guest_sessions)
    votes_data = [
        ("Truth or Dare", "Truth: test1", ["james"], ["session1234a"]),
        ("Truth or Dare", "Dare: test2", ["mary"], ["session1234a", "session1234b"]),
        ("Would You Rather", "Would you rather test1", ["james", "mary"], []),
        ("Would You Rather", "Would you rather test2", ["mary"], ["session1234b"]),
        ("Never Have I Ever", "Never have I ever test1", [], ["session1234a"]),
        ("Never Have I Ever", "Never have I ever test2", [], []),
    ]

    with transaction.atomic():
        # Seed Games
        for name, description in games_data:
            game, _ = Game.objects.get_or_create(name=name)
            game.description = description
            game.slug = slugify(game.name)

            game.save()

        # Seed User + Profile
        for username, password, bio in users_data:
            user, _ = User.objects.get_or_create(username=username)
            # Hash it using set_password()
            user.set_password(password)

            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.bio = bio

            profile.save()

        # Seed Prompts
        # For less query and faster lookups
        usernames = []
        for user in users_data:
            usernames.append(user[0])

        # Reduce look up to one
        creators_qs = User.objects.filter(username__in=usernames)

        creator_map = {}
        for u in creators_qs:
            creator_map[u.username] = u

        for game_name, prompts in prompts_data.items():
            game = Game.objects.get(name=game_name)
            for text, creator_username in prompts:
                creator = creator_map[creator_username]
                Prompt.objects.get_or_create(game=game, creator=creator, text=text)

        # Seed follow pairs
        # Constraints
        for follower_username, following_username in follow_pairs:
            if follower_username == following_username:
                continue  # Disallow self-follow

            follower = creator_map[follower_username]
            following = creator_map[following_username]

            Follow.objects.get_or_create(follower=follower, following=following)

        # Seed Votes
        for game_name, prompt_text, user_voters, guest_sessions in votes_data:
            game = Game.objects.get(name=game_name)
            prompt = Prompt.objects.get(game=game, text=prompt_text)

            # Users votes
            for voter_username in user_voters:
                Vote.objects.get_or_create(prompt=prompt, voter=creator_map[voter_username])

            # Guests votes
            for guest_session_id in guest_sessions:
                Vote.objects.get_or_create(prompt=prompt, guest_session_id=guest_session_id)
        

if __name__ == '__main__':
    print('Starting Verve population script...')
    populate()
    print("Django set up OK")
