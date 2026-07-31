import ast
import importlib
import ipaddress
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from shared_utils.config_loader import get_conf, read_single_conf_with_lru_cache


CREDENTIAL_CONFIG_KEYS = {
    "OpenAI / 兼容渠道": "API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "Google Gemini": "GEMINI_API_KEY",
    "DeepSeek": "DEEPSEEK_API_KEY",
    "Moonshot AI": "MOONSHOT_API_KEY",
    "智谱 AI": "ZHIPUAI_API_KEY",
    "阿里云百炼": "DASHSCOPE_API_KEY",
    "xAI": "GROK_API_KEY",
    "Microsoft Azure": "AZURE_API_KEY",
    "火山引擎": "ARK_API_KEY",
}

DEFAULT_CREDENTIAL_PROVIDER = next(iter(CREDENTIAL_CONFIG_KEYS))
MANAGED_BLOCK_START = "# >>> Academic Agents Studio web settings (managed)"
MANAGED_BLOCK_END = "# <<< Academic Agents Studio web settings (managed)"
DEFAULT_PRIVATE_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config_private.py"
MAX_SECRET_LENGTH = 16_384


class WebConfigError(ValueError):
    pass


def can_manage_config(request, authentication):
    """Only a configured first user (admin) or an unauthenticated loopback client may save."""
    username = getattr(request, "username", None)
    if authentication:
        try:
            return username == authentication[0][0]
        except (IndexError, TypeError):
            return False

    client = getattr(request, "client", None)
    client_host = getattr(client, "host", "")
    headers = getattr(request, "headers", {})
    host_header = headers.get("host", "") if headers else ""
    try:
        requested_host = urlsplit(f"//{host_header}").hostname or ""
    except ValueError:
        return False
    return _is_loopback_host(client_host) and _is_loopback_host(requested_host)


def _is_loopback_host(host):
    host = str(host).strip().lower().rstrip(".")
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def credential_status(provider):
    config_key = CREDENTIAL_CONFIG_KEYS.get(provider)
    if config_key is None:
        return "未识别的密钥厂商"
    try:
        configured = _looks_configured(get_conf(config_key))
    except Exception:
        configured = False
    state = "已配置" if configured else "未配置"
    return f"**{provider}**：{state}。密钥不会在页面中回显。"


def save_web_settings(
    request,
    provider,
    api_key,
    clear_api_key,
    default_model,
    authentication,
    available_models,
    config_path=DEFAULT_PRIVATE_CONFIG_PATH,
):
    """Validate and persist the small, explicit set of settings exposed by the UI."""
    if not can_manage_config(request, authentication):
        return "", False, "保存被拒绝：请从服务本机访问，或使用配置中的首个管理员账号登录。"

    config_key = CREDENTIAL_CONFIG_KEYS.get(provider)
    if config_key is None:
        return "", False, "保存失败：未识别的密钥厂商。"
    if default_model not in available_models:
        return "", False, "保存失败：默认模型不在可用模型列表中。"

    api_key = (api_key or "").strip()
    try:
        _validate_secret(api_key)
        updates = {"LLM_MODEL": default_model}
        if clear_api_key:
            updates[config_key] = ""
        elif api_key:
            updates[config_key] = api_key
        config_path = Path(config_path)
        _update_managed_private_config(updates, config_path)
        if config_path.resolve() == DEFAULT_PRIVATE_CONFIG_PATH.resolve():
            _refresh_config_cache()
    except (OSError, WebConfigError):
        return "", False, "保存失败：无法安全更新私有配置文件，请检查文件权限和格式。"

    action = "已清除" if clear_api_key else "已更新" if api_key else "保持不变"
    message = f"保存成功：{provider} 密钥{action}，默认模型为 `{default_model}`。重启服务后全部生效。"
    return "", False, message


def _validate_secret(value):
    if len(value) > MAX_SECRET_LENGTH:
        raise WebConfigError("Secret is too long")
    if "\n" in value or "\r" in value:
        raise WebConfigError("Secret must be a single line")


def _looks_configured(value):
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.strip().lower()
    placeholders = ("xxxxxxxx", "填入", "00000000-0000-0000-0000-000000000000")
    return not any(marker in normalized for marker in placeholders)


def _read_managed_values(block):
    values = {}
    if not block.strip():
        return values
    try:
        tree = ast.parse(block)
    except SyntaxError as exc:
        raise WebConfigError("Managed config block is invalid") from exc
    allowed_keys = {*CREDENTIAL_CONFIG_KEYS.values(), "LLM_MODEL"}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in allowed_keys:
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError) as exc:
            raise WebConfigError("Managed config values must be literals") from exc
        if not isinstance(value, str):
            raise WebConfigError("Managed config values must be strings")
        values[target.id] = value
    return values


def _split_managed_block(content):
    start_count = content.count(MANAGED_BLOCK_START)
    end_count = content.count(MANAGED_BLOCK_END)
    if start_count != end_count or start_count > 1:
        raise WebConfigError("Managed config markers are invalid")
    if start_count == 0:
        return content.rstrip(), "", ""

    before, remainder = content.split(MANAGED_BLOCK_START, 1)
    block, after = remainder.split(MANAGED_BLOCK_END, 1)
    return before.rstrip(), block.strip(), after.lstrip("\n")


def _render_managed_block(values):
    ordered_keys = ["LLM_MODEL", *CREDENTIAL_CONFIG_KEYS.values()]
    lines = [MANAGED_BLOCK_START]
    for key in ordered_keys:
        if key in values:
            lines.append(f"{key} = {values[key]!r}")
    lines.append(MANAGED_BLOCK_END)
    return "\n".join(lines)


def _update_managed_private_config(updates, path):
    if path.is_symlink():
        raise WebConfigError("Private config must not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    before, old_block, after = _split_managed_block(content)
    values = _read_managed_values(old_block)
    values.update(updates)

    sections = [section for section in (before, _render_managed_block(values), after.rstrip()) if section]
    new_content = "\n\n".join(sections) + "\n"

    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_name = temp_file.name
            temp_file.write(new_content)
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def _refresh_config_cache():
    importlib.invalidate_caches()
    private_module = sys.modules.get("config_private")
    if private_module is not None:
        importlib.reload(private_module)
    read_single_conf_with_lru_cache.cache_clear()
    get_conf.cache_clear()
