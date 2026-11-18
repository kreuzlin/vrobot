"""Tests for /version (commit of the running build)."""

from django.test import TestCase, override_settings


class VersionTests(TestCase):
    @override_settings(APP_COMMIT="d6abe2599595292b8b7e7e977a4e81937393b322")
    def test_returns_commit_as_json(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "commit": "d6abe2599595292b8b7e7e977a4e81937393b322",
                "short": "d6abe25",
            },
        )
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_local_build_reports_dev(self):
        response = self.client.get("/version")
        self.assertEqual(response.json()["commit"], "dev")
