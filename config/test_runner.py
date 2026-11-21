"""Test runner: Django's default runner with a fast password hasher.

Hashing a password with the production hasher (PBKDF2) takes about 0.1 s;
the tests create dozens of accounts. MD5 is only acceptable because test
passwords are throwaway values. The override lives here, not in
`config/settings.py`, so it can never reach production.
`config/tests/test_password_hashers.py` checks both sides.
"""

from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

TEST_PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


class TestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._fast_hasher = override_settings(PASSWORD_HASHERS=TEST_PASSWORD_HASHERS)
        self._fast_hasher.enable()

    def teardown_test_environment(self, **kwargs):
        self._fast_hasher.disable()
        super().teardown_test_environment(**kwargs)
