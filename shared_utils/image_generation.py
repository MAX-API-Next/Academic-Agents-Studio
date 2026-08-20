import base64
import binascii
import os
import time
import uuid
from dataclasses import dataclass
from typing import Optional

import requests
from loguru import logger


SUPPORTED_IMAGE_SIZES = {
    "auto",
    "1024x1024",
    "1536x1024",
    "1024x1536",
    "2048x2048",
    "2048x1152",
    "3840x2160",
    "2160x3840",
}
SUPPORTED_IMAGE_QUALITIES = {"auto", "low", "medium", "high"}
SUPPORTED_IMAGE_FORMATS = {"png", "jpeg", "webp"}


class ImageGenerationError(RuntimeError):
    pass


class ImageGenerationCancelled(ImageGenerationError):
    """Raised when the caller stops an in-flight image request."""


@dataclass(frozen=True)
class ImageGenerationResult:
    file_path: str
    model: str
    size: str
    quality: str
    output_format: str
    request_id: Optional[str] = None
    source_url: Optional[str] = None


def generate_image(
    *,
    prompt,
    api_key,
    output_dir,
    endpoint,
    model="gpt-image-2",
    size="auto",
    quality="medium",
    output_format="png",
    timeout=180,
    proxies=None,
    session=None,
    cancel_event=None,
):
    """Generate one image through an OpenAI-compatible Images API."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise ImageGenerationError("图片描述不能为空。")
    if not api_key or not api_key.strip():
        raise ImageGenerationError("未配置 AIOAGI API Key，请先在设置中填写 OpenAI / 兼容渠道密钥。")
    if size not in SUPPORTED_IMAGE_SIZES:
        raise ImageGenerationError(f"不支持的图片尺寸：{size}")
    if quality not in SUPPORTED_IMAGE_QUALITIES:
        raise ImageGenerationError(f"不支持的图片质量：{quality}")
    if output_format not in SUPPORTED_IMAGE_FORMATS:
        raise ImageGenerationError(f"不支持的图片格式：{output_format}")
    _raise_if_cancelled(cancel_event)

    client = session or requests
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
        "output_format": output_format,
    }
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }

    started_at = time.monotonic()
    try:
        response = client.post(
            endpoint,
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        if cancel_event is not None and cancel_event.is_set():
            raise ImageGenerationCancelled("图片生成已停止。") from exc
        raise ImageGenerationError(f"图片接口连接失败：{exc}") from exc

    _raise_if_cancelled(cancel_event)

    request_id = response.headers.get("x-request-id")
    elapsed = time.monotonic() - started_at
    logger.info(
        "GPT Image request completed: model={} status={} elapsed={:.2f}s request_id={}",
        model,
        response.status_code,
        elapsed,
        request_id or "-",
    )
    if not response.ok:
        raise ImageGenerationError(_format_api_error(response, request_id))

    try:
        body = response.json()
        image_data = body["data"][0]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ImageGenerationError("图片接口返回格式不正确，未找到 data[0]。") from exc

    source_url = image_data.get("url")
    encoded_image = image_data.get("b64_json")
    if encoded_image:
        try:
            image_bytes = base64.b64decode(encoded_image, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ImageGenerationError("图片接口返回了无效的 base64 数据。") from exc
    elif source_url:
        image_bytes = _download_image(
            client,
            source_url,
            proxies=proxies,
            timeout=timeout,
            cancel_event=cancel_event,
        )
    else:
        raise ImageGenerationError("图片接口既未返回 b64_json，也未返回 url。")

    _raise_if_cancelled(cancel_event)
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    filename = f"Image-{timestamp}-{uuid.uuid4().hex[:8]}.{output_format}"
    file_path = os.path.abspath(os.path.join(output_dir, filename))
    try:
        with open(file_path, "wb") as image_file:
            image_file.write(image_bytes)
        _raise_if_cancelled(cancel_event)
    except ImageGenerationCancelled:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
        raise

    return ImageGenerationResult(
        file_path=file_path,
        model=model,
        size=size,
        quality=quality,
        output_format=output_format,
        request_id=request_id,
        source_url=source_url,
    )


def _raise_if_cancelled(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise ImageGenerationCancelled("图片生成已停止。")


def _download_image(client, url, *, proxies, timeout, cancel_event=None):
    _raise_if_cancelled(cancel_event)
    try:
        response = client.get(url, proxies=proxies, timeout=timeout)
    except requests.RequestException as exc:
        if cancel_event is not None and cancel_event.is_set():
            raise ImageGenerationCancelled("图片生成已停止。") from exc
        raise ImageGenerationError(f"图片下载失败：{exc}") from exc
    _raise_if_cancelled(cancel_event)
    if not response.ok:
        raise ImageGenerationError(f"图片下载失败，HTTP {response.status_code}。")
    return response.content


def _format_api_error(response, request_id):
    message = ""
    try:
        payload = response.json()
        error = payload.get("error", payload)
        if isinstance(error, dict):
            message = str(error.get("message") or error.get("code") or "")
        else:
            message = str(error)
    except ValueError:
        message = (response.text or "").strip()
    message = message[:1000] or "未提供错误详情"
    request_suffix = f"，request_id={request_id}" if request_id else ""
    return f"图片生成失败，HTTP {response.status_code}{request_suffix}：{message}"
