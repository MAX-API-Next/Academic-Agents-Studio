import base64
import json
import os
import re
import tempfile
import threading
import unittest

import requests

from mcp_servers.image_generation_tool import (
    AcademicImageGenerationTool,
    format_academic_image_result,
)
from shared_utils.image_edit_authorizations import image_edit_authorizations
from shared_utils.image_generation import (
    ImageGenerationCancelled,
    ImageGenerationError,
    edit_image,
    generate_image,
    list_image_models,
)
from shared_utils.config_loader import get_conf


class FakeResponse:
    def __init__(self, payload=None, status_code=200, content=b"", headers=None, text=""):
        self._payload = payload
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.text = text

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, post_response=None, get_response=None):
        self.post_response = post_response
        self.get_response = get_response
        self.post_call = None
        self.get_call = None

    def post(self, url, **kwargs):
        self.post_call = (url, kwargs)
        if isinstance(self.post_response, Exception):
            raise self.post_response
        return self.post_response

    def get(self, url, **kwargs):
        self.get_call = (url, kwargs)
        if isinstance(self.get_response, Exception):
            raise self.get_response
        return self.get_response


class ImageGenerationClientTests(unittest.TestCase):
    def test_model_list_keeps_only_models_supported_by_images_endpoint(self):
        session = FakeSession(get_response=FakeResponse({
            "data": [
                {"id": "gpt-image-1.5", "supported_endpoint_types": ["openai"]},
                {"id": "gpt-image-2", "supported_endpoint_types": ["openai"]},
                {"id": "gpt-image-2-4k", "supported_endpoint_types": ["openai"]},
                {"id": "gpt-image-2-4k-auto", "supported_endpoint_types": ["openai"]},
                {"id": "gpt-image-2.5", "supported_endpoint_types": ["openai"]},
                {"id": "gpt-image-2.5-4k", "supported_endpoint_types": ["openai"]},
                {"id": "gpt-image-1", "supported_endpoint_types": ["image-generation", "openai"]},
                {"id": "qwen-image-3.0", "supported_endpoint_types": ["image-generation"]},
                {"id": "gemini-2.5-flash-image-preview", "supported_endpoint_types": ["openai", "gemini"]},
                {"id": "grok-4.2-image", "supported_endpoint_types": ["openai"]},
            ],
        }))
        models = list_image_models(
            api_key="secret",
            endpoint="https://api.aiearth.dev/v1/images/generations",
            session=session,
        )
        self.assertEqual(models, [
            "gpt-image-1.5",
            "gpt-image-2",
            "gpt-image-2-4k",
            "gpt-image-2-4k-auto",
            "gpt-image-2.5",
            "gpt-image-2.5-4k",
        ])
        self.assertEqual(session.get_call[0], "https://api.aiearth.dev/v1/models")

    def test_multipart_edit_sends_model_and_gpt_image_options(self):
        image_bytes = b"edited-image"
        session = FakeSession(FakeResponse({
            "data": [{"b64_json": base64.b64encode(image_bytes).decode("ascii")}],
        }))
        with tempfile.TemporaryDirectory() as output_dir:
            source = os.path.join(output_dir, "source.png")
            with open(source, "wb") as image_file:
                image_file.write(b"source-image")
            result = edit_image(
                prompt="make the labels larger",
                image_path=source,
                api_key="secret",
                output_dir=output_dir,
                endpoint="https://api.aiearth.dev/v1/images/generations",
                model="gpt-image-2-4k",
                size="2048x1152",
                quality="high",
                output_format="webp",
                session=session,
            )

            with open(result.file_path, "rb") as image_file:
                self.assertEqual(image_file.read(), image_bytes)

        url, request = session.post_call
        self.assertEqual(url, "https://api.aiearth.dev/v1/images/edits")
        self.assertEqual(request["data"]["model"], "gpt-image-2-4k")
        self.assertEqual(request["data"]["size"], "2048x1152")
        self.assertEqual(request["data"]["quality"], "high")
        self.assertEqual(request["data"]["output_format"], "webp")
        self.assertEqual(request["files"]["image"][1], b"source-image")
        self.assertNotIn("Content-Type", request["headers"])

    def test_qwen_edit_sends_base64_json_contract(self):
        session = FakeSession(FakeResponse({
            "data": [{"b64_json": base64.b64encode(b"edited").decode("ascii")}],
        }))
        with tempfile.TemporaryDirectory() as output_dir:
            source = os.path.join(output_dir, "source.png")
            with open(source, "wb") as image_file:
                image_file.write(b"source-image")
            edit_image(
                prompt="use a blue background",
                image_path=source,
                api_key="secret",
                output_dir=output_dir,
                endpoint="https://api.aiearth.dev/v1/images/generations",
                model="qwen-image-edit",
                size="1024x1024",
                session=session,
            )

        _, request = session.post_call
        payload = request["json"]
        self.assertEqual(payload["model"], "qwen-image-edit")
        content = payload["input"]["messages"][0]["content"]
        self.assertTrue(content[0]["image"].startswith("data:image/png;base64,"))
        self.assertEqual(content[1]["text"], "use a blue background")
        self.assertEqual(payload["parameters"]["size"], "1024x1024")
        self.assertNotIn("files", request)

    def test_edit_api_error_keeps_request_id(self):
        session = FakeSession(FakeResponse(
            {"error": {"message": "edit unavailable"}},
            status_code=400,
            headers={"x-request-id": "req-edit-error"},
        ))
        with tempfile.TemporaryDirectory() as output_dir:
            source = os.path.join(output_dir, "source.png")
            with open(source, "wb") as image_file:
                image_file.write(b"source")
            with self.assertRaisesRegex(ImageGenerationError, "req-edit-error"):
                edit_image(
                    prompt="edit",
                    image_path=source,
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                )

    def test_cancelled_edit_does_not_reach_provider(self):
        cancel_event = threading.Event()
        cancel_event.set()
        session = FakeSession(FakeResponse({"data": []}))
        with tempfile.TemporaryDirectory() as output_dir:
            source = os.path.join(output_dir, "source.png")
            with open(source, "wb") as image_file:
                image_file.write(b"source")
            with self.assertRaises(ImageGenerationCancelled):
                edit_image(
                    prompt="edit",
                    image_path=source,
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                    cancel_event=cancel_event,
                )
        self.assertIsNone(session.post_call)

    def test_cancelled_request_does_not_reach_provider(self):
        session = FakeSession(FakeResponse({"data": []}))
        cancel_event = threading.Event()
        cancel_event.set()

        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(ImageGenerationError, "已停止"):
                generate_image(
                    prompt="illustration",
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                    cancel_event=cancel_event,
                )

        self.assertIsNone(session.post_call)

    def test_cancelled_response_is_not_saved(self):
        cancel_event = threading.Event()

        class CancellingSession(FakeSession):
            def post(self, url, **kwargs):
                response = super().post(url, **kwargs)
                cancel_event.set()
                return response

        session = CancellingSession(FakeResponse({
            "data": [{"b64_json": base64.b64encode(b"image").decode("ascii")}],
        }))
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(ImageGenerationError, "已停止"):
                generate_image(
                    prompt="illustration",
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                    cancel_event=cancel_event,
                )

            self.assertEqual(os.listdir(output_dir), [])

    def test_cancelled_post_error_raises_cancelled_without_output(self):
        cancel_event = threading.Event()

        class CancellingPostSession(FakeSession):
            def post(self, url, **kwargs):
                self.post_call = (url, kwargs)
                cancel_event.set()
                raise requests.RequestException("cancelled post")

        session = CancellingPostSession(FakeResponse({"data": []}))
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaises(ImageGenerationCancelled):
                generate_image(
                    prompt="illustration",
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                    cancel_event=cancel_event,
                )

            self.assertEqual(os.listdir(output_dir), [])

    def test_cancelled_download_error_raises_cancelled_without_output(self):
        cancel_event = threading.Event()

        class CancellingGetSession(FakeSession):
            def get(self, url, **kwargs):
                self.get_call = (url, kwargs)
                cancel_event.set()
                raise requests.RequestException("cancelled get")

        session = CancellingGetSession(
            FakeResponse({"data": [{"url": "https://cdn.example/image"}]}),
        )
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaises(ImageGenerationCancelled):
                generate_image(
                    prompt="illustration",
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                    cancel_event=cancel_event,
                )

            self.assertEqual(os.listdir(output_dir), [])

    def test_base64_response_is_saved_and_request_uses_aiearth_contract(self):
        image_bytes = b"test-image-bytes"
        session = FakeSession(FakeResponse(
            {"data": [{"b64_json": base64.b64encode(image_bytes).decode("ascii")}]},
            headers={"x-request-id": "req-test"},
        ))
        with tempfile.TemporaryDirectory() as output_dir:
            result = generate_image(
                prompt="A clear academic concept illustration",
                api_key="secret",
                output_dir=output_dir,
                endpoint="https://api.aiearth.dev/v1/images/generations",
                model="gpt-image-2",
                size="1024x1024",
                quality="medium",
                output_format="png",
                session=session,
            )

            with open(result.file_path, "rb") as image_file:
                self.assertEqual(image_file.read(), image_bytes)
            self.assertEqual(result.request_id, "req-test")
            self.assertTrue(result.file_path.endswith(".png"))

        url, request = session.post_call
        self.assertEqual(url, "https://api.aiearth.dev/v1/images/generations")
        self.assertEqual(request["json"]["model"], "gpt-image-2")
        self.assertEqual(request["json"]["output_format"], "png")
        self.assertNotIn("response_format", request["json"])
        self.assertEqual(request["timeout"], 180)

    def test_url_response_is_downloaded_for_legacy_compatibility(self):
        session = FakeSession(
            FakeResponse({"data": [{"url": "https://cdn.example/image"}]}),
            FakeResponse(content=b"downloaded-image"),
        )
        with tempfile.TemporaryDirectory() as output_dir:
            result = generate_image(
                prompt="illustration",
                api_key="secret",
                output_dir=output_dir,
                endpoint="https://api.aiearth.dev/v1/images/generations",
                output_format="webp",
                session=session,
            )
            with open(result.file_path, "rb") as image_file:
                self.assertEqual(image_file.read(), b"downloaded-image")
        self.assertEqual(session.get_call[0], "https://cdn.example/image")

    def test_api_error_keeps_request_id(self):
        session = FakeSession(FakeResponse(
            {"error": {"message": "model is unavailable"}},
            status_code=400,
            headers={"x-request-id": "req-error"},
        ))
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(ImageGenerationError, "req-error"):
                generate_image(
                    prompt="illustration",
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                )

    def test_connection_error_has_user_safe_message(self):
        session = FakeSession(requests.RequestException("connection failed"))
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(ImageGenerationError, "图片接口连接失败"):
                generate_image(
                    prompt="illustration",
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                )

    def test_url_download_connection_error_has_user_safe_message(self):
        session = FakeSession(
            FakeResponse({"data": [{"url": "https://cdn.example/image"}]}),
            requests.RequestException("download failed"),
        )
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(ImageGenerationError, "图片下载失败"):
                generate_image(
                    prompt="illustration",
                    api_key="secret",
                    output_dir=output_dir,
                    endpoint="https://api.aiearth.dev/v1/images/generations",
                    session=session,
                )


class AcademicImageToolTests(unittest.TestCase):
    def setUp(self):
        self.logging_root = os.path.abspath(get_conf("PATH_LOGGING"))
        os.makedirs(self.logging_root, exist_ok=True)
        self.output_dir = tempfile.TemporaryDirectory(dir=self.logging_root)

    def tearDown(self):
        self.output_dir.cleanup()

    def test_tool_returns_structured_local_result_that_can_be_rendered(self):
        session = FakeSession(FakeResponse({
            "data": [{"b64_json": base64.b64encode(b"image").decode("ascii")}],
        }))
        tool = AcademicImageGenerationTool(
            api_keys="sk-" + "a" * 48,
            output_dir=self.output_dir.name,
            session=session,
        )

        result_text = tool.call({
            "prompt": "A publication-ready graphical abstract",
            "size": "1536x1024",
            "quality": "high",
            "output_format": "png",
        })
        result = json.loads(result_text)

        self.assertEqual(result["kind"], "academic_image_result")
        self.assertEqual(result["model"], "gpt-image-2")
        self.assertTrue(os.path.isfile(result["file_path"]))
        rendered = format_academic_image_result(result_text, tool=tool)
        self.assertIn('<img src="file=', rendered)
        self.assertIn("下载原图", rendered)
        self.assertIn("data-image-token=", rendered)
        self.assertNotIn("data-image-source=", rendered)

    def test_renderer_rejects_forged_path_for_another_user(self):
        session = FakeSession(FakeResponse({
            "data": [{"b64_json": base64.b64encode(b"image").decode("ascii")}],
        }))
        tool = AcademicImageGenerationTool(
            api_keys="sk-" + "a" * 48,
            output_dir=self.output_dir.name,
            session=session,
        )
        result = json.loads(tool.call({"prompt": "illustration"}))

        with tempfile.TemporaryDirectory(dir=self.logging_root) as other_user_dir:
            other_user_file = os.path.join(other_user_dir, "private.png")
            with open(other_user_file, "wb") as image_file:
                image_file.write(b"private")
            result["file_path"] = other_user_file

            self.assertIsNone(
                format_academic_image_result(json.dumps(result), tool=tool)
            )

    def test_renderer_uses_server_owned_parameters_when_result_is_tampered(self):
        session = FakeSession(FakeResponse({
            "data": [{"b64_json": base64.b64encode(b"image").decode("ascii")}],
        }))
        tool = AcademicImageGenerationTool(
            api_keys="sk-" + "a" * 48,
            output_dir=self.output_dir.name,
            session=session,
        )
        result = json.loads(tool.call({
            "prompt": "illustration",
            "model": "gpt-image-2-4k",
            "size": "1536x1024",
            "quality": "high",
            "output_format": "webp",
        }))
        result.update({
            "model": "attacker-model",
            "size": "attacker-size",
            "quality": "low",
            "output_format": "jpeg",
        })

        rendered = format_academic_image_result(json.dumps(result), tool=tool)
        token = re.search(r'data-image-token="([^"]+)"', rendered).group(1)
        authorization = image_edit_authorizations.resolve(
            token,
            owner=self.output_dir.name,
            output_root=self.output_dir.name,
        )

        self.assertIn("gpt-image-2-4k", rendered)
        self.assertNotIn("attacker-model", rendered)
        self.assertEqual(authorization.model, "gpt-image-2-4k")
        self.assertEqual(authorization.size, "1536x1024")
        self.assertEqual(authorization.quality, "high")
        self.assertEqual(authorization.output_format, "webp")

    def test_renderer_rejects_unknown_file_in_current_user_directory(self):
        unknown_file = os.path.join(self.output_dir.name, "unknown.png")
        with open(unknown_file, "wb") as image_file:
            image_file.write(b"unknown")
        forged_result = json.dumps({
            "kind": "academic_image_result",
            "file_path": unknown_file,
            "render_token": "forged",
        })
        tool = AcademicImageGenerationTool(
            api_keys="sk-" + "a" * 48,
            output_dir=self.output_dir.name,
        )

        self.assertIsNone(format_academic_image_result(forged_result, tool=tool))

    def test_tool_requires_chatbot_when_output_directory_is_not_explicit(self):
        session = FakeSession(FakeResponse())
        tool = AcademicImageGenerationTool(
            api_keys="sk-" + "a" * 48,
            session=session,
        )

        with self.assertRaisesRegex(ImageGenerationError, "缺少当前用户会话"):
            tool.call({"prompt": "illustration"})
        self.assertIsNone(session.post_call)


if __name__ == "__main__":
    unittest.main()
