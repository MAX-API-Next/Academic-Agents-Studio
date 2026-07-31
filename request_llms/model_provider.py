"""Model provider labels used by the model selector UI."""

ALL_MODEL_PROVIDERS = "全部厂商"


def infer_model_provider(model_name):
    """Return a stable provider/access-channel label for a configured model ID."""
    name = model_name.lower().strip()

    # Routing prefixes take precedence because they determine credentials and billing.
    access_channels = (
        ("aioagi-", "AIOAGI"),
        ("openrouter-", "OpenRouter"),
        ("azure", "Microsoft Azure"),
        ("volcengine-", "火山引擎"),
        ("ollama-", "Ollama（本地）"),
        ("vllm-", "vLLM（本地）"),
    )
    for prefix, provider in access_channels:
        if name.startswith(prefix):
            return provider
    if "@" in name:
        return "Text Generation WebUI（本地）"

    provider_prefixes = (
        (("gpt-", "chatgpt-", "o1", "o3", "o4", "dall-e"), "OpenAI"),
        (("claude", "stack-claude"), "Anthropic"),
        (("gemini",), "Google"),
        (("kimi", "moonshot"), "Moonshot AI"),
        (("glm", "chatglm"), "智谱 AI"),
        (("qwen",), "阿里云"),
        (("grok",), "xAI"),
        (("deepseek",), "DeepSeek"),
        (("qianfan", "ernie"), "百度智能云"),
        (("spark",), "科大讯飞"),
        (("yi-",), "零一万物"),
        (("cohere",), "Cohere"),
        (("taichu",), "中科院自动化所"),
        (("skylark",), "火山引擎"),
    )
    for prefixes, provider in provider_prefixes:
        if name.startswith(prefixes):
            return provider

    local_prefixes = (
        "internlm",
        "jittorllms",
        "llama",
        "moss",
        "qwen-local",
    )
    if name.startswith(local_prefixes):
        return "其他本地模型"
    return "其他兼容模型"


def group_models_by_provider(models):
    """Group model IDs by provider while preserving configuration order."""
    groups = {}
    for model in dict.fromkeys(models):
        provider = infer_model_provider(model)
        groups.setdefault(provider, []).append(model)
    return groups


def models_for_provider(models, provider):
    """Return the model choices for one provider or all configured providers."""
    unique_models = list(dict.fromkeys(models))
    if provider == ALL_MODEL_PROVIDERS:
        return unique_models
    return group_models_by_provider(unique_models).get(provider, [])
