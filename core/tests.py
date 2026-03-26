from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from .models import Game, Prompt, Follow, Vote, Profile
from .forms import NeverHaveIEverForm

User = get_user_model()

# Test constrains for core models.
# Note : Wrap expected IntegrityError writes in transaction.atomic()
# to isolate the failure and roll back to a savepoint.
class ModelConstraintTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="u1", password="1234")
        self.u2 = User.objects.create_user(username="u2", password="1234")
        self.game = Game.objects.create(name="Test Game", description="Test")
        self.prompt = Prompt.objects.create(game=self.game, creator=self.u1, text="Test prompt")

    def test_follow_cannot_follow_self(self):
        """ Tests for no self follow allowed. """

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Follow.objects.create(follower=self.u1, following=self.u1)

    def test_follow_cannot_duplicate_pair(self):
        """ Tests for duplicate follow pair. """

        Follow.objects.create(follower=self.u1, following=self.u2)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Follow.objects.create(follower=self.u1, following=self.u2)

    def test_vote_limit_one_per_user(self):
        """ Tests for one vote per user per prompt. """

        Vote.objects.create(prompt=self.prompt, voter=self.u1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(prompt=self.prompt, voter=self.u1)

    def test_vote_limit_one_per_session(self):
        """ Tests for one vote per session id per prompt. """
        Vote.objects.create(prompt=self.prompt, guest_session_id="session1234")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(prompt=self.prompt, guest_session_id="session1234")

    def test_vote_requires_guest_or_user_not_both(self):
        """ Tests for either logged in or guest but not both. """
        # Neither set
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(prompt=self.prompt)

        # Both set
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vote.objects.create(prompt=self.prompt, voter=self.u1, guest_session_id="session1234")

    def test_vote_allow_mix_identities(self):
        """ Tests for vote allow mix of different identities. """

        Vote.objects.create(prompt=self.prompt, voter=self.u1)
        Vote.objects.create(prompt=self.prompt, voter=self.u2)
        Vote.objects.create(prompt=self.prompt, guest_session_id="session1234")
        Vote.objects.create(prompt=self.prompt, guest_session_id="session4321")

    def test_vote_count_is_derived(self):
        """ Tests for derived vote count. """

        Vote.objects.create(prompt=self.prompt, voter=self.u1)
        Vote.objects.create(prompt=self.prompt, guest_session_id="session1234")
        derived_vote_count = Vote.objects.filter(prompt=self.prompt).count()
        self.assertEqual(derived_vote_count, 2)

    def test_following_count_is_derived(self):
        """ Tests for derived following count. """

        Follow.objects.create(follower=self.u1, following=self.u2)
        derived_following_count = Follow.objects.filter(follower=self.u1).count()
        self.assertEqual(derived_following_count, 1)

    # Prompt Model Tests
    def test_prompt_requires_user(self):
        """ Tests for required logged in user """

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Prompt.objects.create(game=self.game, text="Test text")

    def test_prompt_creates_id(self):
        """ Tests for id generation on prompt create """

        prompt = Prompt.objects.create(game=self.game, creator=self.u1, text="")
        prompt.save()
        self.assertTrue(prompt.id is not None)

# Test auth url routing behaviour
class AuthViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="TestPass1234!")
        Profile.objects.create(user=self.user)

    def test_register_get(self):
        """ Tests for GET /register/. """
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/register.html")

    def test_register_post(self):
        """ Tests for POST /register/. """
        response = self.client.post(reverse("register"), 
                                            {"username": "testusernew",
                                             "password1" : "TestPassNew1!",
                                             "password2" : "TestPassNew1!"})
        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="testusernew")
        self.assertTrue(User.objects.filter(username = user.username).exists())
        # Check profile aswell
        self.assertTrue(Profile.objects.filter(user=user).exists())
        # Check auto login after register
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_get(self):
        """ Test for GET /login/. """
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/login.html")

    def test_login_post_valid(self):
        """ Test for valid POST /login/. """
        response = self.client.post(reverse("login"),
                                    {"username": self.user.username,
                                     "password": "TestPass1234!"})
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        

    def test_login_post_invalid(self):
        """ Test for invalid POST /login/. """
        response = self.client.post(reverse("login"),
                                    {"username": "NonExistUser",
                                     "password": "NonExistPassword"})
        self.assertTemplateUsed(response, "auth/login.html")
        self.assertIn("error", response.context)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        """Test logout clears session and redirects home."""
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class PromptViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="TestPass1234!")
        self.game = Game.objects.create(name="Test Game", description="Test")
        self.prompt = Prompt.objects.create(game=self.game, creator=self.user, text="Test prompt")
    
    def test_choose_game_get(self):
        """ Test for GET /create/. """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.get(reverse("choose_game"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "prompts/choose_game.html")
    
    def test_choose_game_post(self):
        """ Test for POST /create/. """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.post(reverse("choose_game"),
                                    {"game":self.game.id})
        self.assertRedirects(response, reverse("create_prompt", 
                                               kwargs={"slug":self.game.slug}))
    
    def test_create_get(self):
        """ Test for GET /create/<slug:slug>/. """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.get(reverse("create_prompt",
                                           kwargs={"slug":self.game.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "prompts/create.html")

    def test_create_post(self):
        """ Test for POST /create/<slug:slug>/. """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.post(reverse("create_prompt",kwargs={"slug":self.game.slug}),
                                    {"text":"Test post"})
        self.assertRedirects(response, reverse("my_prompts"))
        prompt = Prompt.objects.get(text="Test post")
        self.assertTrue(Prompt.objects.filter(creator=self.user).exists())
    
    def test_edit_get(self):
        """ Test for GET /<int:prompt_id>/edit/. """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.get(reverse("edit_prompt",
                                           kwargs={"prompt_id":self.prompt.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "prompts/edit.html")

    def test_edit_post(self):
        """ Test for POST /<int:prompt_id>/edit/. """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.post(reverse("edit_prompt", kwargs={"prompt_id":self.prompt.id}),
                                    {"text":"Test edit post",
                                     "prompt_id":self.prompt.id})
        self.assertRedirects(response, reverse("my_prompts"))
        prompt = Prompt.objects.get(id=self.prompt.id)
        self.assertTrue(Prompt.objects.filter(text="Test edit post").exists())

    def test_my_prompts_get(self):
        """ Test for GET /profiles/my_prompts/. """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.get(reverse("my_prompts"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/my_prompts.html")

    def test_delete_post(self):
        """ TEST for POST /prompts/<int:prompt_id>/delete """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.post(reverse("delete_prompt",
                                            kwargs={"prompt_id":self.prompt.id}))
        self.assertRedirects(response, reverse("my_prompts"))
        prompt = self.prompt
        self.assertFalse(Prompt.objects.filter(text=prompt.text).exists()) 
        
# Test follow/unfollow profile behaviour
class FollowViewTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="testuser1", password="TestPass1234!")
        self.u2 = User.objects.create_user(username="testuser2", password="TestPass1234!")
        Profile.objects.create(user=self.u1)
        Profile.objects.create(user=self.u2)

    def test_follow_user_post(self):
        """ Tests for following user """
        self.client.login(username="testuser1", password="TestPass1234!")
        response = self.client.post(reverse("follow_user", args=[self.u2.username]))

        self.assertRedirects(response, reverse("profile", args=[self.u2.username]))
        self.assertTrue(Follow.objects.filter(follower=self.u1, following=self.u2).exists())

    def test_unfollow_user_post(self):
        """ Tests for unfollowing user """
        Follow.objects.create(follower=self.u1, following=self.u2)
        self.client.login(username="testuser1", password="TestPass1234!")

        response = self.client.post(reverse("unfollow_user", args=[self.u2.username]))

        self.assertRedirects(response, reverse("profile", args=[self.u2.username]))
        self.assertFalse(Follow.objects.filter(follower=self.u1, following=self.u2).exists())

    def test_follow_user_requires_login(self):
        """ Tests that following user requires login """
        response = self.client.post(reverse("follow_user", args=[self.u2.username]))

        login_url = reverse("login")
        follow_url = reverse("follow_user", args=[self.u2.username])
        self.assertRedirects(response, f"{login_url}?next={follow_url}")
        self.assertFalse(Follow.objects.filter(follower=self.u1, following=self.u2).exists())

    def test_unfollow_user_requires_login(self):
        """ Tests that unfollow user requires login. """
        Follow.objects.create(follower=self.u1, following=self.u2)

        response = self.client.post(reverse("unfollow_user", args=[self.u2.username]))

        login_url = reverse("login")
        unfollow_url = reverse("unfollow_user", args=[self.u2.username])
        self.assertRedirects(response, f"{login_url}?next={unfollow_url}")
        self.assertTrue(Follow.objects.filter(follower=self.u1, following=self.u2).exists())

    def test_follow_user_cannot_follow_self(self):
        """ Tests logged in user cannot follow themselves. """
        self.client.login(username="testuser1", password="TestPass1234!")

        response = self.client.post(reverse("follow_user", args=[self.u1.username]))

        self.assertRedirects(response, reverse("profile", args=[self.u1.username]))
        self.assertFalse(Follow.objects.filter(follower=self.u1, following=self.u1).exists())

    def test_follow_user_no_duplicate_follow_created(self):
        """ Tests follow user does not create duplicate follow. """
        self.client.login(username="testuser1", password="TestPass1234!")

        self.client.post(reverse("follow_user", args=[self.u2.username]))
        response = self.client.post(reverse("follow_user", args=[self.u2.username]))

        self.assertRedirects(response, reverse("profile", args=[self.u2.username]))
        self.assertEqual(Follow.objects.filter(follower=self.u1, following=self.u2).count(), 1)

    # AJAX specific follow/unfollow tests
    def test_follow_user_ajax_returns_json(self):
        """ Tests AJAX follow returns JSON and creates follow record """
        self.client.login(username="testuser1", password="TestPass1234!")
        response = self.client.post(
            reverse("follow_user", args=[self.u2.username]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["following"])
        self.assertEqual(data["follower_count"], 1)
        self.assertEqual(data["next_url"], reverse("unfollow_user", args=[self.u2.username]))
        self.assertTrue(Follow.objects.filter(follower=self.u1, following=self.u2).exists())

    def test_unfollow_user_ajax_returns_json(self):
        """ Tests AJAX unfollow returns JSON and removes follow """
        Follow.objects.create(follower=self.u1, following=self.u2)
        self.client.login(username="testuser1", password="TestPass1234!")
        response = self.client.post(
            reverse("unfollow_user", args=[self.u2.username]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["following"])
        self.assertEqual(data["follower_count"], 0)
        self.assertEqual(data["next_url"], reverse("follow_user", args=[self.u2.username]))
        self.assertFalse(Follow.objects.filter(follower=self.u1, following=self.u2).exists())

    def test_follow_user_ajax_does_not_allow_self_follow(self):
        """ Tests AJAX self-follow does not create a follow """
        self.client.login(username="testuser1", password="TestPass1234!")
        response = self.client.post(
            reverse("follow_user", args=[self.u1.username]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["following"])
        self.assertEqual(data["follower_count"], 0)
        self.assertEqual(data["next_url"], reverse("unfollow_user", args=[self.u1.username]))
        self.assertFalse(Follow.objects.filter(follower=self.u1, following=self.u1).exists())
    
    def test_follow_user_ajax_does_not_duplicate_follow(self):
        """ Tests AJAX follow does not create duplicate follow """
        Follow.objects.create(follower=self.u1, following=self.u2)
        self.client.login(username="testuser1", password="TestPass1234!")
        response = self.client.post(
            reverse("follow_user", args=[self.u2.username]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["following"])
        self.assertEqual(data["follower_count"], 1)
        self.assertEqual(
            Follow.objects.filter(follower=self.u1, following=self.u2).count(),
            1)

#Test Home View
class HomeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.game = Game.objects.create(name="Test Game", slug="test-game")
        self.prompts = []

        for i in range(6):
            p = Prompt.objects.create(text=f"Prompt {i}", creator=self.user, game=self.game)
            self.prompts.append(p)

        Vote.objects.create(
            prompt=self.prompts[0],
            voter=self.user
        )
        Vote.objects.create(
            prompt=self.prompts[0],
            voter=None,
            guest_session_id="guest123"
        )
        Vote.objects.create(
            prompt=self.prompts[1],
            voter=self.user
        )

        self.client = Client()

    def test_home_view_status(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_top_prompts_order_and_length(self):
        response = self.client.get(reverse('home'))
        prompts_in_context = list(response.context["prompts"])
        self.assertEqual(prompts_in_context[0], self.prompts[0])
        self.assertEqual(len(prompts_in_context), 5)

    def test_home_authenticated_voted_prompts(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("home"))
        voted_prompts = response.context["voted_prompts"]
        self.assertIn(self.prompts[0].id, voted_prompts)
        self.assertIn(self.prompts[1].id, voted_prompts)

    def test_home_guest_voted_prompts(self):
        session = self.client.session
        session["foo"] = "bar"  # just here to ensure session exists
        session.save()

        Vote.objects.create(
            prompt=self.prompts[2], 
            voter=None, 
            guest_session_id=session.session_key
        )
        response = self.client.get(reverse("home"))
        voted_prompts = response.context["voted_prompts"]
        self.assertIn(self.prompts[2].id, voted_prompts)

class CreatePromptViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="pass")
        self.game1 = Game.objects.create(name="Mario Maker", slug="mario-maker")
        self.game2 = Game.objects.create(name="Truth Or Dare", slug="truth-or-dare")

    def test_redirect_guest_user(self):
        url = reverse("create_prompt", args=[self.game1.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302) 
        self.assertIn("/login", response.url) #redirected to log in page

    def test_get_request_returns_form(self):
        self.client.login(username="tester", password="pass")
        url = reverse("create_prompt", args=[self.game1.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_correct_form_for_truth_or_dare(self):
        self.client.login(username="tester", password="pass")
        url = reverse("create_prompt", args=[self.game2.slug])
        response = self.client.get(url)

        form = response.context["form"]

        self.assertEqual(form.__class__.__name__, "TruthOrDareForm")

    def test_post_creates_prompt(self):
        self.client.login(username="tester", password="pass")
        url = reverse("create_prompt", args=[self.game1.slug])
        data = {"text": "Test Prompt"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Prompt.objects.count(), 1) #A prompt has been created

        prompt = Prompt.objects.first()

        self.assertEqual(prompt.creator, self.user)
        self.assertEqual(prompt.game, self.game1)
        self.assertEqual(prompt.text, "Test Prompt")

    def test_post_invalid_prompt(self):
        self.client.login(username="tester", password="pass")
        url = reverse("create_prompt", args=[self.game1.slug])
        data = {}#{"text":""} #should be invalid, empty text
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200) #form is redisplayed
        self.assertEqual(Prompt.objects.count(), 0) #No prompt has been created

class GamePageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")

        self.would_you_rather = Game.objects.create(name="Would You Rather", slug="would-you-rather")
        self.never_have_i_ever = Game.objects.create(name="Never Have I Ever", slug="never-have-i-ever")
        self.truth_or_dare = Game.objects.create(name="Truth or Dare", slug="truth-or-dare")

    def test_game_play_never_have_i_ever(self):
        Prompt.objects.create(text="Be invisible?", game=self.never_have_i_ever, creator=self.user)
        Prompt.objects.create(text="Fly forever?", game=self.never_have_i_ever, creator=self.user)

        url = reverse("game_play", args=[self.never_have_i_ever.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("prompts", response.context)

    def test_game_invalid_slug(self):
        url = reverse("game_play", args=["invalid-game"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

# Upvote with AJAX tests
class UpvoteViewTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="voter", password="TestPass1234!")
        self.u2 = User.objects.create_user(username="creator", password="TestPass1234!")
        Profile.objects.create(user=self.u1)
        Profile.objects.create(user=self.u2)
        self.game = Game.objects.create(name="Test Game", description="Test")
        self.prompt = Prompt.objects.create(game=self.game, creator=self.u2, text="Test prompt")

    def test_upvote_creates_vote(self):
        """Test upvoting creates a vote."""
        self.client.login(username="voter", password="TestPass1234!")
        response = self.client.post(reverse("upvote_prompt", args=[self.prompt.id]))
        self.assertEqual(Vote.objects.filter(prompt=self.prompt, voter=self.u1).count(), 1)

    def test_upvote_toggle_removes_vote(self):
        """Test upvoting again removes the vote."""
        self.client.login(username="voter", password="TestPass1234!")
        self.client.post(reverse("upvote_prompt", args=[self.prompt.id]))
        self.client.post(reverse("upvote_prompt", args=[self.prompt.id]))
        self.assertEqual(Vote.objects.filter(prompt=self.prompt, voter=self.u1).count(), 0)

    def test_self_vote_blocked(self):
        """Test creator cannot vote on own prompt."""
        self.client.login(username="creator", password="TestPass1234!")
        self.client.post(reverse("upvote_prompt", args=[self.prompt.id]))
        self.assertEqual(Vote.objects.filter(prompt=self.prompt).count(), 0)

    def test_upvote_ajax_returns_json(self):
        """Test AJAX upvote returns JSON response."""
        self.client.login(username="voter", password="TestPass1234!")
        response = self.client.post(reverse("upvote_prompt", args=[self.prompt.id]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["voted"])
        self.assertEqual(data["vote_count"], 1)

    def test_upvote_ajax_toggle_returns_json(self):
        """Test AJAX unvote returns updated JSON."""
        self.client.login(username="voter", password="TestPass1234!")
        self.client.post(reverse("upvote_prompt", args=[self.prompt.id]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        response = self.client.post(reverse("upvote_prompt", args=[self.prompt.id]),HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        data = response.json()
        self.assertFalse(data["voted"])
        self.assertEqual(data["vote_count"], 0)

    def test_self_vote_ajax_returns_403(self):
        """Test AJAX self-vote returns 403."""
        self.client.login(username="creator", password="TestPass1234!")
        response = self.client.post(reverse("upvote_prompt", args=[self.prompt.id]),HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 403)

    def test_guest_vote(self):
        """Test guest can vote via session."""
        self.client.post(reverse("upvote_prompt", args=[self.prompt.id]))
        self.assertEqual(Vote.objects.filter(prompt=self.prompt).count(), 1)

    def test_get_rejected(self):
        """Test GET request returns 405."""
        response = self.client.get(reverse("upvote_prompt", args=[self.prompt.id]))
        self.assertEqual(response.status_code, 405)

# Test profiles/ views
class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_profile", password="TestPass1234!")
        Profile.objects.create(user=self.user)
    
    def test_get_my_profile_logged_in(self):
        """ Test GET /profiles/. """
        self.client.login(username="test_profile", password="TestPass1234!")
        response = self.client.get(reverse("my_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response="profiles/my_profile.html")

    def test_get_my_profile_logged_out(self):
        """ Test GET /profiles/ as guest. """
        response = self.client.get(reverse("my_profile"))
        login_url = reverse("login")
        follow_url = reverse("my_profile")
        self.assertRedirects(response, f"{login_url}?next={follow_url}")

    def test_correct_profile(self):
        """ Test GET /profiles/ uses logged in user's profile """
        self.client.login(username="test_profile", password="TestPass1234!")
        response = self.client.get(reverse("my_profile"))
        self.assertEqual(response.context["profile"].user, self.user)

    def test_get_edit_profile_logged_in(self):
        """ Test GET /profiles/edit/. """
        self.client.login(username="test_profile", password="TestPass1234!")
        response = self.client.get(reverse("edit_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response="profiles/edit_profile.html")

    def test_get_edit_profile_logged_out(self):
        """ Test GET /profiles/edit/ as guest. """
        response = self.client.get(reverse("edit_profile"))
        login_url = reverse("login")
        follow_url = reverse("edit_profile")
        self.assertRedirects(response, f"{login_url}?next={follow_url}")

    def test_post_edit_profile(self):
        """ Test POST /profiles/edit/. """
        self.client.login(username="test_profile", password="TestPass1234!")
        test_profile = Profile.objects.get(user=self.user)
        test_bio = "Test Bio"
        response = self.client.post(reverse("edit_profile"), 
                                    {"bio":test_bio})
        test_profile = Profile.objects.get(user=self.user)
        self.assertRedirects(response, reverse("my_profile"))
        self.assertEqual(test_profile.bio, test_bio)
    
    def test_get_other_profile(self):
        """ Test GET /profiles/<str:username>/. """
        response = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response="profiles/profile.html")

    def test_correct_other_profile(self):
        """ Test GET /profiles/<str:username>/ uses correct profile. """
        response = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertEqual(response.context["profile"].user, self.user)