import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from shared_utils.web_config import (
    DEFAULT_CREDENTIAL_PROVIDER,
    MANAGED_BLOCK_END,
    MANAGED_BLOCK_START,
    _update_managed_private_config,
    can_manage_config,
    save_web_settings,
)


def make_request(host, username=None, host_header=None):
    if host_header is None:
        formatted_host = f"[{host}]" if ":" in host else host
        host_header = f"{formatted_host}:7860"
    return SimpleNamespace(client=SimpleNamespace(host=host), headers={"host": host_header}, username=username)


class WebConfigAccessTests(unittest.TestCase):
    def test_unauthenticated_config_requires_loopback(self):
        self.assertTrue(can_manage_config(make_request("127.0.0.1"), []))
        self.assertTrue(can_manage_config(make_request("::1"), []))

    def test_loopback_proxy_does_not_make_a_public_host_local(self):
        self.assertFalse(can_manage_config(make_request("127.0.0.1", host_header="studio.example.com"), []))
        self.assertFalse(can_manage_config(make_request("192.0.2.10"), []))

    def test_first_authenticated_user_is_the_config_admin(self):
        authentication = [("admin", "secret"), ("member", "secret")]
        self.assertTrue(can_manage_config(make_request("192.0.2.10", "admin"), authentication))
        self.assertFalse(can_manage_config(make_request("127.0.0.1", "member"), authentication))


class WebConfigPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config_private.py"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_managed_block_preserves_manual_config(self):
        self.config_path.write_text("CUSTOM_SETTING = 'keep-me'\n", encoding="utf-8")

        _update_managed_private_config(
            {"LLM_MODEL": "gpt-5-mini", "API_KEY": "first-secret"},
            self.config_path,
        )
        _update_managed_private_config(
            {"ANTHROPIC_API_KEY": "second-secret"},
            self.config_path,
        )

        content = self.config_path.read_text(encoding="utf-8")
        self.assertIn("CUSTOM_SETTING = 'keep-me'", content)
        self.assertIn("API_KEY = 'first-secret'", content)
        self.assertIn("ANTHROPIC_API_KEY = 'second-secret'", content)
        self.assertEqual(content.count(MANAGED_BLOCK_START), 1)
        self.assertEqual(content.count(MANAGED_BLOCK_END), 1)
        self.assertEqual(stat.S_IMODE(self.config_path.stat().st_mode), 0o600)

    def test_remote_save_is_rejected_without_writing_secret(self):
        password, clear, message = save_web_settings(
            request=make_request("192.0.2.10"),
            provider=DEFAULT_CREDENTIAL_PROVIDER,
            api_key="not-a-real-secret",
            clear_api_key=False,
            default_model="gpt-5-mini",
            authentication=[],
            available_models=["gpt-5-mini"],
            config_path=self.config_path,
        )

        self.assertEqual(password, "")
        self.assertFalse(clear)
        self.assertIn("保存被拒绝", message)
        self.assertNotIn("not-a-real-secret", message)
        self.assertFalse(self.config_path.exists())

    def test_local_save_does_not_echo_secret(self):
        password, clear, message = save_web_settings(
            request=make_request("127.0.0.1"),
            provider=DEFAULT_CREDENTIAL_PROVIDER,
            api_key="not-a-real-secret",
            clear_api_key=False,
            default_model="gpt-5-mini",
            authentication=[],
            available_models=["gpt-5-mini"],
            config_path=self.config_path,
        )

        self.assertEqual(password, "")
        self.assertFalse(clear)
        self.assertIn("保存成功", message)
        self.assertNotIn("not-a-real-secret", message)
        self.assertIn("API_KEY = 'not-a-real-secret'", self.config_path.read_text(encoding="utf-8"))

    def test_invalid_secret_and_model_do_not_write(self):
        for api_key, model in (("line-one\nline-two", "gpt-5-mini"), ("valid", "missing-model")):
            with self.subTest(api_key=api_key, model=model):
                _, _, message = save_web_settings(
                    request=make_request("127.0.0.1"),
                    provider=DEFAULT_CREDENTIAL_PROVIDER,
                    api_key=api_key,
                    clear_api_key=False,
                    default_model=model,
                    authentication=[],
                    available_models=["gpt-5-mini"],
                    config_path=self.config_path,
                )
                self.assertIn("保存失败", message)
                self.assertFalse(self.config_path.exists())


if __name__ == "__main__":
    unittest.main()
