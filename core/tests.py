from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from .models import Game, Prompt, Follow, Vote, Profile

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
        """Test logout clears session and redirects home. """
        self.client.login(username=self.user.username, password="TestPass1234!")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

#Test Home Page
class HomeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.game = Game.objects.create(name="Test Game", slug="test-game")
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



