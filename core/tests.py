from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from .models import Game, Prompt, Follow, Vote, Profile

# Test constrains for core models.
# Note : Wrap expected IntegrityError writes in transaction.atomic()
# to isolate the failure and roll back to a savepoint.

class ModelConstraintTests(TestCase):
    def setUp(self):
        User = get_user_model()
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
