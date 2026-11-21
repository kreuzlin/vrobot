"""The fast test hasher must stay in tests; production keeps PBKDF2."""

import importlib

from django.conf import global_settings, settings
from django.test import SimpleTestCase

PBKDF2 = "django.contrib.auth.hashers.PBKDF2PasswordHasher"
WEAK_HASHERS = {
    "django.contrib.auth.hashers.MD5PasswordHasher",
    "django.contrib.auth.hashers.UnsaltedMD5PasswordHasher",
    "django.contrib.auth.hashers.SHA1PasswordHasher",
    "django.contrib.auth.hashers.UnsaltedSHA1PasswordHasher",
    "django.contrib.auth.hashers.CryptPasswordHasher",
}


class ProductionPasswordHasherTests(SimpleTestCase):
    def production_hashers(self):
        # The settings module as production loads it, without the test
        # runner's override. Not set there = Django's default list.
        module = importlib.import_module("config.settings")
        return getattr(module, "PASSWORD_HASHERS", global_settings.PASSWORD_HASHERS)

    def test_production_uses_pbkdf2(self):
        self.assertEqual(self.production_hashers()[0], PBKDF2)

    def test_production_lists_no_weak_hasher(self):
        self.assertFalse(WEAK_HASHERS & set(self.production_hashers()))

    def test_fast_hasher_only_via_test_runner(self):
        self.assertEqual(settings.TEST_RUNNER, "config.test_runner.TestRunner")
        # Active during this test run (set by the runner, not by settings).
        self.assertEqual(
            settings.PASSWORD_HASHERS,
            ["django.contrib.auth.hashers.MD5PasswordHasher"],
        )
