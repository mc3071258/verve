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
        ("Truth or Dare", "Choose between honestly answering a question or performing a challenging task!"),
        ("Would You Rather", "Use your decision making skills to decide between two scenarios!"),
        ("Never Have I Ever", "Each player starts with ten fingers- drop one each time the given scenario applies to you!"),
    ]

    users_data = [
        ("james", "JamesPass1234!", "Party game champion, Professional verve addict"),
        ("mary", "MaryPass1234!", "Following friends only, Truth or Dare is my fave"),
        ("lucas","LucasPass1234!","Check out my prompts- I spent way too long on them!!"),
        ("emma", "EmmaPass1234!", "Student at UofG, procrastinating too hard rn"),
        ("noah", "NoahPass1234!", "Just for fun! Here to find new games to try."),
        ("olivia", "OliviaPass1234!", "Life of the party 🎵"),
    ]
    
    # game : (text, creator_name)
    prompts_data = {
        "Truth or Dare": [
            ("What's the strangest dream you've had?", "james", "truth"),
            ("Try and lick your own elbow", "mary", "dare"),
            ("Who's your celebrity crush?", "lucas", "truth"),
            ("Text your crush right now", "emma", "dare"),
            ("What's your biggest fear?", "noah", "truth"),
            ("Have you ever lied to your best friend?", "mary", "truth"),
            ("What's your most embarrassing moment?", "lucas", "truth"),
            ("Do 10 push-ups right now", "olivia", "dare"),
            ("Sing a song loudly for 30 seconds", "mary", "dare"),
            ("What's a secret you've never told anyone?", "noah", "truth"),
            ("Dance with no music for 1 minute", "lucas", "dare"),
            ("Let someone send a message from your phone", "emma", "dare"),
        ],
        "Would You Rather": [
            ("Shoot spaghetti out of your fingers | Sneeze meatballs", "james"),
            ("Eat only beans forever | Never eat beans again", "mary"),
            ("Always whisper | Always shout", "lucas"),
            ("Be invisible | Be able to fly", "james"),
            ("Live without music | Live without movies", "lucas"),
            ("Always be late | Always be early", "emma"),
            ("Have no internet | Have no phone", "noah"),
            ("Speak all languages | Talk to animals", "olivia"),
            ("Be super strong | Be super smart", "james"),
            ("Never sleep | Never eat", "mary"),
            ("Live in the past | Live in the future", "lucas"),
            ("Win the lottery | Find true love", "olivia"),
        ],
        "Never Have I Ever": [
            ("Never have I ever broken a bone", "james"),
            ("Never have I ever skipped a lecture", "mary"),
            ("Never have I ever fainted", "lucas"),
            ("Never have I ever lied to get out of plans", "mary"),
            ("Never have I ever stayed up all night", "lucas"),
            ("Never have I ever laughed at the wrong moment", "noah"),
            ("Never have I ever forgotten someone's name", "james"),
            ("Never have I ever looked through someone's phone", "mary"),
            ("Never have I ever gotten lost", "lucas"),
            ("Never have I ever been on stage", "emma"),
            ("Never have I ever cried during a movie", "noah"),
            ("Never have I ever cheated in a test", "olivia"),
        ],
    }

    follow_pairs = [
        ("james", "mary"),
        ("james", "lucas"),
        ("james", "olivia"),
        ("mary", "james"),
        ("mary", "emma"),
        ("lucas","james"),
        ("lucas", "olivia"),
        ("lucas", "noah"),
        ("emma", "james"),
        ("emma", "mary"),
        ("noah", "emma"),
        ("noah", "james"),
        ("olivia", "mary"),
        ("olivia", "emma"),
    ]

    # (game_name, prompt_text, user_voters, guest_sessions)
    votes_data = [
        # Truth or Dare
        ("Truth or Dare", "What's the strangest dream you've had?", ["mary", "emma"], ["session1234a"]),
        ("Truth or Dare", "Try and lick your own elbow", ["james", "lucas"], ["session1234b"]),
        ("Truth or Dare", "Who's your celebrity crush?", ["emma", "olivia"], []),
        ("Truth or Dare", "Text your crush right now", ["james", "mary"], ["session1234c"]),
        ("Truth or Dare", "What's your biggest fear?", ["lucas"], ["session1234d"]),
        ("Truth or Dare", "Have you ever lied to your best friend?", ["james", "olivia"], []),
        ("Truth or Dare", "What's your most embarrassing moment?", ["mary"], ["session1234e"]),
        ("Truth or Dare", "Do 10 push-ups right now", ["noah", "james"], []),
        ("Truth or Dare", "Sing a song loudly for 30 seconds", ["emma"], ["session1234f"]),
        ("Truth or Dare", "What's a secret you've never told anyone?", ["lucas", "mary"], []),
        ("Truth or Dare", "Dance with no music for 1 minute", ["noah"], ["session1234g"]),
        ("Truth or Dare", "Let someone send a message from your phone", ["olivia"], []),

        # Would You Rather
        ("Would You Rather", "Shoot spaghetti out of your fingers | Sneeze meatballs", ["mary", "emma"], ["session2234a"]),
        ("Would You Rather", "Eat only beans forever | Never eat beans again", ["james", "olivia"], []),
        ("Would You Rather", "Always whisper | Always shout", ["emma"], ["session2234b"]),
        ("Would You Rather", "Be invisible | Be able to fly", ["mary", "noah"], []),
        ("Would You Rather", "Live without music | Live without movies", ["james"], ["session2234c"]),
        ("Would You Rather", "Always be late | Always be early", ["lucas", "olivia"], []),
        ("Would You Rather", "Have no internet | Have no phone", ["james", "emma"], ["session2234d"]),
        ("Would You Rather", "Speak all languages | Talk to animals", ["mary"], []),
        ("Would You Rather", "Be super strong | Be super smart", ["lucas", "noah"], ["session2234e"]),
        ("Would You Rather", "Never sleep | Never eat", ["emma"], []),
        ("Would You Rather", "Live in the past | Live in the future", ["james", "mary"], ["session2234f"]),
        ("Would You Rather", "Win the lottery | Find true love", ["noah", "olivia"], []),

        # Never Have I Ever
        ("Never Have I Ever", "Never have I ever broken a bone", ["mary"], ["session3234a"]),
        ("Never Have I Ever", "Never have I ever skipped a lecture", ["james", "emma"], []),
        ("Never Have I Ever", "Never have I ever fainted", ["mary", "olivia"], ["session3234b"]),
        ("Never Have I Ever", "Never have I ever lied to get out of plans", ["lucas"], []),
        ("Never Have I Ever", "Never have I ever stayed up all night", ["james", "noah"], ["session3234c"]),
        ("Never Have I Ever", "Never have I ever laughed at the wrong moment", ["emma"], []),
        ("Never Have I Ever", "Never have I ever forgotten someone's name", ["mary", "lucas"], []),
        ("Never Have I Ever", "Never have I ever looked through someone's phone", ["noah"], ["session3234d"]),
        ("Never Have I Ever", "Never have I ever gotten lost", ["james"], []),
        ("Never Have I Ever", "Never have I ever been on stage", ["olivia", "mary"], ["session3234e"]),
        ("Never Have I Ever", "Never have I ever cried during a movie", ["lucas"], []),
        ("Never Have I Ever", "Never have I ever cheated in a test", ["james", "emma"], ["session3234f"]),
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
            for prompt_entry in prompts:
                text = prompt_entry[0]
                creator = creator_map[prompt_entry[1]]
                # For truth or dare
                if len(prompt_entry) > 2:
                    category = prompt_entry[2] 
                else:
                    category = None
                Prompt.objects.get_or_create(game=game, creator=creator, text=text, category=category)
                
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
    print("Population complete.")