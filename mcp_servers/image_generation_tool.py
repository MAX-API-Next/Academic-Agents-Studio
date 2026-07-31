import html
import json
import os

from qwen_agent.tools.base import BaseTool

from shared_utils.image_generation import generate_image
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

    def call(self, params, **kwargs):
        params = self._verify_json_format_args(params)
        model, endpoint, timeout, proxies = get_conf(
            "IMAGE_MODEL",
            "IMAGE_API_URL",
            "IMAGE_TIMEOUT_SECONDS",
            "proxies",
        )
        api_key = select_api_key(self.api_keys, model)
        output_dir = self.output_dir
        if output_dir is None:
            from toolbox import get_log_folder, get_user

            user_name = get_user(self.chatbot) if self.chatbot is not None else None
            output_dir = get_log_folder(user_name, plugin_name="image_gen")
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
        if self.chatbot is not None:
            from toolbox import promote_file_to_downloadzone

            promote_file_to_downloadzone(result.file_path, chatbot=self.chatbot)

        return json.dumps(
            {
                "kind": IMAGE_RESULT_KIND,
                "file_path": result.file_path,
                "model": result.model,
                "size": result.size,
                "quality": result.quality,
                "output_format": result.output_format,
                "request_id": result.request_id,
            },
            ensure_ascii=False,
        )


def format_academic_image_result(result_text):
    """Render only trusted generated files; return None for other tool results."""
    try:
        result = json.loads(result_text)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(result, dict) or result.get("kind") != IMAGE_RESULT_KIND:
        return None

    file_path = os.path.abspath(str(result.get("file_path", "")))
    logging_root = os.path.abspath(get_conf("PATH_LOGGING"))
    try:
        inside_logging_root = os.path.commonpath([logging_root, file_path]) == logging_root
    except ValueError:
        inside_logging_root = False
    if not inside_logging_root or not os.path.isfile(file_path):
        return None

    safe_path = html.escape(file_path, quote=True)
    safe_model = html.escape(str(result.get("model", "gpt-image-2")))
    safe_size = html.escape(str(result.get("size", "auto")))
    return (
        f'<div align="center"><img src="file={safe_path}" alt="生成的学术插图"></div>'
        f'<br>模型：<code>{safe_model}</code>，尺寸：<code>{safe_size}</code>'
        f'<br><a href="file={safe_path}" target="_blank">下载原图</a>'
    )
