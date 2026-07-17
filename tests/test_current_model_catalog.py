import ast
import unittest
from pathlib import Path

from request_llms.current_model_registry import (
    CURRENT_MODEL_SPECS,
    DEFAULT_CURRENT_MODELS,
    current_model_names,
    omits_sampling_parameters,
)
from request_llms.provider_compat import (
    apply_openai_sampling_compatibility,
    extract_anthropic_text_delta,
)


ROOT = Path(__file__).resolve().parents[1]


def read_config_assignment(name):
    tree = ast.parse((ROOT / "config.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing config assignment: {name}")


class CurrentModelCatalogTests(unittest.TestCase):
    def test_expected_current_models_are_registered(self):
        expected = {
            "openai": {"gpt-5.6", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"},
            "claude": {
                "claude-fable-5",
                "claude-opus-4-8",
                "claude-sonnet-5",
                "claude-haiku-4-5",
                "claude-haiku-4-5-20251001",
            },
            "gemini": {
                "gemini-3.5-flash",
                "gemini-3.1-flash-lite",
                "gemini-3.1-pro-preview",
            },
            "kimi": {
                "kimi-k3",
                "kimi-k2.7-code",
                "kimi-k2.7-code-highspeed",
                "kimi-k2.6",
            },
            "glm": {"glm-5.2", "glm-5.1", "glm-5-turbo", "glm-4.7-flash"},
            "qwen": {"qwen3.7-max", "qwen3.7-plus", "qwen3.6-flash"},
            "grok": {"grok-4.5", "grok-4.3"},
        }

        self.assertEqual(set(CURRENT_MODEL_SPECS), set(expected))
        for provider, model_names in expected.items():
            self.assertEqual(set(current_model_names(provider)), model_names)

    def test_default_config_exposes_every_recommended_model_once(self):
        configured_models = read_config_assignment("AVAIL_LLM_MODELS")
        self.assertTrue(set(DEFAULT_CURRENT_MODELS).issubset(configured_models))
        self.assertEqual(len(configured_models), len(set(configured_models)))

    def test_multi_query_defaults_are_selectable(self):
        configured_models = set(read_config_assignment("AVAIL_LLM_MODELS"))
        multi_query_models = set(
            read_config_assignment("MULTI_QUERY_LLM_MODELS").split("&")
        )
        self.assertTrue(multi_query_models.issubset(configured_models))

    def test_model_ids_are_unique_across_providers(self):
        model_names = [
            model_name
            for models in CURRENT_MODEL_SPECS.values()
            for model_name in models
        ]
        self.assertEqual(len(model_names), len(set(model_names)))

    def test_every_current_model_has_a_positive_context_window(self):
        for provider, models in CURRENT_MODEL_SPECS.items():
            for model_name, spec in models.items():
                with self.subTest(provider=provider, model=model_name):
                    self.assertGreater(spec["max_token"], 0)

    def test_provider_bridges_consume_each_registry_group(self):
        bridge_all = (ROOT / "request_llms" / "bridge_all.py").read_text(
            encoding="utf-8"
        )
        for provider in CURRENT_MODEL_SPECS:
            with self.subTest(provider=provider):
                self.assertIn(f'CURRENT_MODEL_SPECS["{provider}"]', bridge_all)

    def test_qwen_api_key_can_be_configured(self):
        self.assertEqual(read_config_assignment("DASHSCOPE_API_KEY"), "")

    def test_fixed_sampling_models_use_provider_defaults(self):
        for model_name in current_model_names("openai"):
            self.assertTrue(omits_sampling_parameters("openai", model_name))
        for model_name in current_model_names("kimi"):
            self.assertTrue(omits_sampling_parameters("kimi", model_name))
        for model_name in ("claude-fable-5", "claude-opus-4-8", "claude-sonnet-5"):
            self.assertTrue(omits_sampling_parameters("claude", model_name))


class ProviderCompatibilityTests(unittest.TestCase):
    def test_openai_current_models_drop_sampling_parameters(self):
        payload = {"temperature": 0.2, "top_p": 0.9, "n": 1}
        apply_openai_sampling_compatibility(
            payload, {"omit_sampling_parameters": True}
        )
        self.assertEqual(payload, {"n": 1})

    def test_legacy_openai_reasoning_flag_only_drops_temperature(self):
        payload = {"temperature": 0.2, "top_p": 0.9}
        apply_openai_sampling_compatibility(
            payload, {"openai_force_temperature_one": True}
        )
        self.assertEqual(payload, {"top_p": 0.9})

    def test_anthropic_text_delta_is_extracted(self):
        event = {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": "answer"},
        }
        self.assertEqual(extract_anthropic_text_delta(event), "answer")

    def test_anthropic_thinking_delta_is_ignored(self):
        event = {
            "type": "content_block_delta",
            "delta": {"type": "thinking_delta", "thinking": "private"},
        }
        self.assertEqual(extract_anthropic_text_delta(event), "")


if __name__ == "__main__":
    unittest.main()
