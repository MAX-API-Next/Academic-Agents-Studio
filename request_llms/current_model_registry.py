"""Current first-party model IDs supported by the built-in provider bridges."""

# Refresh this catalog against provider documentation when model lifecycles change.
CATALOG_LAST_VERIFIED = "2026-07-17"

CURRENT_MODEL_SPECS = {
    "openai": {
        "gpt-5.6": {
            "max_token": 1_050_000,
            "max_output_token": 128_000,
            "has_multimodal_capacity": True,
            "omit_sampling_parameters": True,
        },
        "gpt-5.6-sol": {
            "max_token": 1_050_000,
            "max_output_token": 128_000,
            "has_multimodal_capacity": True,
            "omit_sampling_parameters": True,
        },
        "gpt-5.6-terra": {
            "max_token": 1_050_000,
            "max_output_token": 128_000,
            "has_multimodal_capacity": True,
            "omit_sampling_parameters": True,
        },
        "gpt-5.6-luna": {
            "max_token": 1_050_000,
            "max_output_token": 128_000,
            "has_multimodal_capacity": True,
            "omit_sampling_parameters": True,
        },
    },
    "claude": {
        "claude-fable-5": {
            "max_token": 1_000_000,
            "max_output_token": 128_000,
            "has_multimodal_capacity": True,
            "omit_sampling_parameters": True,
        },
        "claude-opus-4-8": {
            "max_token": 1_000_000,
            "max_output_token": 128_000,
            "has_multimodal_capacity": True,
            "omit_sampling_parameters": True,
        },
        "claude-sonnet-5": {
            "max_token": 1_000_000,
            "max_output_token": 128_000,
            "has_multimodal_capacity": True,
            "omit_sampling_parameters": True,
        },
        "claude-haiku-4-5": {
            "max_token": 200_000,
            "max_output_token": 64_000,
            "has_multimodal_capacity": True,
        },
        "claude-haiku-4-5-20251001": {
            "max_token": 200_000,
            "max_output_token": 64_000,
            "has_multimodal_capacity": True,
        },
    },
    "gemini": {
        "gemini-3.5-flash": {
            "max_token": 1_048_576,
            "max_output_token": 65_536,
            "has_multimodal_capacity": True,
        },
        "gemini-3.1-flash-lite": {
            "max_token": 1_048_576,
            "max_output_token": 65_536,
            "has_multimodal_capacity": True,
        },
        "gemini-3.1-pro-preview": {
            "max_token": 1_048_576,
            "max_output_token": 65_536,
            "has_multimodal_capacity": True,
        },
    },
    "kimi": {
        "kimi-k3": {
            "max_token": 1_000_000,
            "omit_sampling_parameters": True,
        },
        "kimi-k2.7-code": {
            "max_token": 256_000,
            "omit_sampling_parameters": True,
        },
        "kimi-k2.7-code-highspeed": {
            "max_token": 256_000,
            "omit_sampling_parameters": True,
        },
        "kimi-k2.6": {
            "max_token": 256_000,
            "omit_sampling_parameters": True,
        },
    },
    "glm": {
        "glm-5.2": {"max_token": 1_000_000, "max_output_token": 128_000},
        "glm-5.1": {"max_token": 200_000, "max_output_token": 128_000},
        "glm-5-turbo": {"max_token": 200_000, "max_output_token": 128_000},
        "glm-4.7-flash": {"max_token": 200_000, "max_output_token": 128_000},
    },
    "qwen": {
        "qwen3.7-max": {"max_token": 1_000_000},
        "qwen3.7-plus": {"max_token": 1_000_000},
        "qwen3.6-flash": {"max_token": 1_000_000},
    },
    "grok": {
        "grok-4.5": {"max_token": 500_000, "enable_reasoning": True},
        "grok-4.3": {"max_token": 1_000_000, "enable_reasoning": True},
    },
}


DEFAULT_CURRENT_MODELS = (
    "gpt-5.6",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "claude-fable-5",
    "claude-opus-4-8",
    "claude-sonnet-5",
    "claude-haiku-4-5",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "kimi-k3",
    "kimi-k2.7-code",
    "kimi-k2.7-code-highspeed",
    "kimi-k2.6",
    "glm-5.2",
    "glm-5.1",
    "glm-5-turbo",
    "glm-4.7-flash",
    "qwen3.7-max",
    "qwen3.7-plus",
    "qwen3.6-flash",
    "grok-4.5",
    "grok-4.3",
)


def current_model_names(provider):
    return tuple(CURRENT_MODEL_SPECS[provider])


def get_current_model_spec(provider, model):
    return CURRENT_MODEL_SPECS.get(provider, {}).get(model, {})


def omits_sampling_parameters(provider, model):
    return get_current_model_spec(provider, model).get(
        "omit_sampling_parameters", False
    )
