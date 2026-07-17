"""Small payload and stream compatibility helpers shared by provider bridges."""


def remove_request_parameters(payload, *parameter_names):
    for parameter_name in parameter_names:
        payload.pop(parameter_name, None)
    return payload


def apply_openai_sampling_compatibility(payload, model_config):
    if model_config.get("omit_sampling_parameters", False):
        return remove_request_parameters(payload, "temperature", "top_p")
    if model_config.get("openai_force_temperature_one", False):
        return remove_request_parameters(payload, "temperature")
    return payload


def extract_anthropic_text_delta(event):
    if not isinstance(event, dict) or event.get("type") != "content_block_delta":
        return ""

    delta = event.get("delta")
    if not isinstance(delta, dict):
        return ""
    if delta.get("type") not in (None, "text_delta"):
        return ""

    text = delta.get("text", "")
    return text if isinstance(text, str) else ""
