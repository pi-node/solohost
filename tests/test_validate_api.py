"""Regression tests for the SoloHost hosted-validator client.

Run with: python3 -m unittest discover -s tests -v
All network interactions are mocked; these tests are safe to run offline.
"""
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

SCRIPT = Path(__file__).parents[1] / "skills/solohost-package/scripts/validate_api.py"
SPEC = importlib.util.spec_from_file_location("validate_api", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class ValidatorTests(unittest.TestCase):
    def test_read_requires_compose_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                validator._read(directory)

    def test_read_requires_config_file(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                validator._read(directory)

    def test_read_returns_both_files(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            Path(directory, "config_options.yml").write_text("fields: []\n", encoding="utf-8")
            self.assertEqual(
                validator._read(directory),
                ("services: {}\n", "fields: []\n"),
            )

    def test_validate_posts_both_package_files(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            Path(directory, "config_options.yml").write_text("fields: []\n", encoding="utf-8")
            expected = {
                "composeYaml": "services: {}\n",
                "configOptionsYaml": "fields: []\n",
            }
            with mock.patch.object(validator, "_post", return_value={"ok": True}) as post:
                self.assertEqual(validator.validate(directory), {"ok": True})
            post.assert_called_once_with(validator.VALIDATE_URL, expected)

    def test_retry_after_uses_header_and_caps_wait(self):
        error = HTTPError("https://example.test", 429, "limited", {"Retry-After": "90"}, None)
        self.assertEqual(validator._retry_after(error), validator.RATE_LIMIT_WAIT_SECONDS)

    def test_retry_after_falls_back_when_header_is_invalid(self):
        error = HTTPError("https://example.test", 429, "limited", {"Retry-After": "later"}, None)
        self.assertEqual(validator._retry_after(error), validator.RATE_LIMIT_WAIT_SECONDS)

    def test_post_returns_successful_json(self):
        with mock.patch.object(validator.urllib.request, "urlopen", return_value=Response({"ok": True})):
            self.assertEqual(validator._post("https://example.test", {"x": 1}), {"ok": True})

    def test_post_returns_json_body_for_client_error(self):
        failure = HTTPError(
            "https://example.test", 400, "invalid", {}, io.BytesIO(b'{"ok": false, "errors": ["invalid"]}')
        )
        with mock.patch.object(validator.urllib.request, "urlopen", side_effect=failure):
            self.assertEqual(
                validator._post("https://example.test", {}),
                {"ok": False, "errors": ["invalid"]},
            )

    def test_post_retries_server_error_then_succeeds(self):
        failure = HTTPError("https://example.test", 503, "unavailable", {}, io.BytesIO(b"busy"))
        with mock.patch.object(
            validator.urllib.request, "urlopen",
            side_effect=[failure, Response({"ok": True})],
        ), mock.patch.object(validator.time, "sleep"):
            self.assertEqual(validator._post("https://example.test", {}), {"ok": True})

    def test_preview_env_writes_api_generated_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            Path(directory, "config_options.yml").write_text("fields: []\n", encoding="utf-8")
            with mock.patch.object(validator, "_post", return_value={"ok": True, "env": "TOKEN=dummy\n"}):
                self.assertEqual(validator.preview_env([directory, "TOKEN=dummy"]), 0)
            self.assertEqual(Path(directory, ".env").read_text(encoding="utf-8"), "TOKEN=dummy\n")

    def test_preview_env_rejects_malformed_value(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(validator.preview_env([directory, "NOT_A_PAIR"]), 2)


if __name__ == "__main__":
    unittest.main()
