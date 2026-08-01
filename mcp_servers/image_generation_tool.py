import html
import json
import os
import secrets
import threading

from qwen_agent.tools.base import BaseTool

from shared_utils.image_generation import ImageGenerationError, generate_image
from shared_utils.config_loader import get_conf
from shared_utils.key_pattern_manager import select_api_key


IMAGE_RESULT_KIND = "academic_image_result"


class AcademicImageGenerationTool(BaseTool):
    name = "generate_academic_image"
    description = (
        "根据用户明确提出的要求生成学术概念插图、图形摘要、封面插图或普通图片。"
        "不要用此工具生成要求数值精确的统计图表；条形图、折线图、散点图等应使用学术图表工具。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "详细描述图片主体、布局、风格、文字和用途。",
            },
            "size": {
                "type": "string",
                "enum": ["auto", "1024x1024", "1536x1024", "1024x1536"],
                "description": "图片尺寸，默认由模型自动选择。",
            },
            "quality": {
                "type": "string",
                "enum": ["low", "medium", "high", "auto"],
                "description": "生成质量；草稿用 low，普通使用 medium，成稿使用 high。",
            },
            "output_format": {
                "type": "string",
                "enum": ["png", "jpeg", "webp"],
                "description": "输出文件格式。",
            },
        },
        "required": ["prompt"],
    }

    def __init__(self, *, api_keys, chatbot=None, output_dir=None, session=None):
        super().__init__()
        self.api_keys = api_keys or ""
        self.chatbot = chatbot
        self.output_dir = output_dir
        self.session = session
        self._render_authorizations = {}
        self._render_authorizations_lock = threading.Lock()

    def call(self, params, **kwargs):
        params = self._verify_json_format_args(params)
        output_dir = self._get_output_directory()
        model, endpoint, timeout, proxies = get_conf(
            "IMAGE_MODEL",
            "IMAGE_API_URL",
            "IMAGE_TIMEOUT_SECONDS",
            "proxies",
        )
        api_key = select_api_key(self.api_keys, model)
        result = generate_image(
            prompt=params["prompt"],
            api_key=api_key,
            output_dir=output_dir,
            endpoint=endpoint,
            model=model,
            size=params.get("size", "auto"),
            quality=params.get("quality", "medium"),
            output_format=params.get("output_format", "png"),
            timeout=timeout,
            proxies=proxies,
            session=self.session,
        )
        file_path, output_root = self._resolve_generated_file(result.file_path, output_dir)
        if self.chatbot is not None:
            from toolbox import promote_file_to_downloadzone

            promote_file_to_downloadzone(file_path, chatbot=self.chatbot)

        render_token = secrets.token_urlsafe(32)
        with self._render_authorizations_lock:
            self._render_authorizations[render_token] = (file_path, output_root)

        return json.dumps(
            {
                "kind": IMAGE_RESULT_KIND,
                "file_path": file_path,
                "model": result.model,
                "size": result.size,
                "quality": result.quality,
                "output_format": result.output_format,
                "request_id": result.request_id,
                "render_token": render_token,
            },
            ensure_ascii=False,
        )

    def _get_output_directory(self):
        if self.output_dir is not None:
            return self.output_dir
        if self.chatbot is None:
            raise ImageGenerationError("缺少当前用户会话，无法确定图片保存目录。")

        from toolbox import get_log_folder, get_user

        return get_log_folder(get_user(self.chatbot), plugin_name="image_gen")

    @staticmethod
    def _resolve_generated_file(file_path, output_dir):
        output_root = os.path.realpath(os.path.abspath(output_dir))
        resolved_file = os.path.realpath(os.path.abspath(file_path))
        try:
            is_inside_output = os.path.commonpath([output_root, resolved_file]) == output_root
        except ValueError:
            is_inside_output = False
        if not is_inside_output or not os.path.isfile(resolved_file):
            raise ImageGenerationError("图片文件不在当前用户的生成目录中。")
        return resolved_file, output_root

    def consume_render_authorization(self, result):
        """Return an authorized path once for a result produced by this tool instance."""
        render_token = result.get("render_token")
        if not isinstance(render_token, str):
            return None

        with self._render_authorizations_lock:
            authorization = self._render_authorizations.pop(render_token, None)
        if authorization is None:
            return None

        expected_file, output_root = authorization
        candidate = os.path.realpath(os.path.abspath(str(result.get("file_path", ""))))
        try:
            is_inside_output = os.path.commonpath([output_root, candidate]) == output_root
        except ValueError:
            is_inside_output = False
        if candidate != expected_file or not is_inside_output or not os.path.isfile(candidate):
            return None
        return candidate


def format_academic_image_result(result_text, tool=None):
    """Render a result authorized by the current session's local image tool."""
    try:
        result = json.loads(result_text)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(result, dict) or result.get("kind") != IMAGE_RESULT_KIND:
        return None
    if not isinstance(tool, AcademicImageGenerationTool):
        return None

    file_path = tool.consume_render_authorization(result)
    if file_path is None:
        return None

    safe_path = html.escape(file_path, quote=True)
    safe_model = html.escape(str(result.get("model", "gpt-image-2")))
    safe_size = html.escape(str(result.get("size", "auto")))
    return (
        f'<div align="center"><img src="file={safe_path}" alt="生成的学术插图"></div>'
        f'<br>模型：<code>{safe_model}</code>，尺寸：<code>{safe_size}</code>'
        f'<br><a href="file={safe_path}" target="_blank">下载原图</a>'
    )
