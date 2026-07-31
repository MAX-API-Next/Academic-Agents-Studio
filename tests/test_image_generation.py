import base64
import json
import os
import tempfile
import unittest

from mcp_servers.image_generation_tool import (
    AcademicImageGenerationTool,
    format_academic_image_result,
)
from shared_utils.image_generation import ImageGenerationError, generate_image
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
    def __init__(self, post_response, get_response=None):
        self.post_response = post_response
        self.get_response = get_response
        self.post_call = None
        self.get_call = None

    def post(self, url, **kwargs):
        self.post_call = (url, kwargs)
        return self.post_response

    def get(self, url, **kwargs):
        self.get_call = (url, kwargs)
        return self.get_response


class ImageGenerationClientTests(unittest.TestCase):
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
        rendered = format_academic_image_result(result_text)
        self.assertIn('<img src="file=', rendered)
        self.assertIn("下载原图", rendered)

    def test_renderer_rejects_paths_outside_logging_root(self):
        with tempfile.NamedTemporaryFile() as outside_file:
            result_text = json.dumps({
                "kind": "academic_image_result",
                "file_path": outside_file.name,
            })
            self.assertIsNone(format_academic_image_result(result_text))


if __name__ == "__main__":
    unittest.main()
