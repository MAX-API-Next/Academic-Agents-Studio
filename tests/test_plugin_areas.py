import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ["no_proxy"] = "*"

from crazy_functional import get_crazy_functions
from main import (
    DRAWING_FORMAT_OPTIONS,
    DRAWING_QUALITY_OPTIONS,
    DRAWING_RESOLUTION_OPTIONS,
    build_drawing_pending_message,
    build_drawing_plugin_kwargs,
    replace_drawing_job_message,
)
from crazy_functions.Image_Generate import 图片生成_GPT_IMAGE
from toolbox import ChatBotWithCookies
from shared_utils.image_generation import (
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_IMAGE_QUALITIES,
    SUPPORTED_IMAGE_SIZES,
)
from shared_utils.image_jobs import ImageJobManager


class DrawingAreaTests(unittest.TestCase):
    def test_gpt_image_entry_is_not_registered_as_a_function_plugin(self):
        plugin_name = "🎨学术插图 / 图片生成（GPT Image 2）"
        plugins = get_crazy_functions()

        self.assertNotIn(plugin_name, plugins)

    def test_drawing_controls_offer_every_supported_api_value(self):
        self.assertEqual(set(DRAWING_RESOLUTION_OPTIONS), SUPPORTED_IMAGE_SIZES)
        self.assertEqual(set(DRAWING_QUALITY_OPTIONS), SUPPORTED_IMAGE_QUALITIES)
        self.assertEqual(set(DRAWING_FORMAT_OPTIONS), SUPPORTED_IMAGE_FORMATS)

    def test_drawing_values_are_forwarded_to_the_image_generator(self):
        self.assertEqual(
            build_drawing_plugin_kwargs("3840x2160", "high", "webp"),
            {
                "resolution": "3840x2160",
                "quality": "high",
                "output_format": "webp",
            },
        )

    def test_image_plugin_replaces_progress_message_with_final_image(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            result = SimpleNamespace(
                file_path=image_file.name,
                model="gpt-image-2",
                size="1024x1024",
            )
            chatbot = ChatBotWithCookies({"user_name": "default_user"})
            with (
                patch(
                    "crazy_functions.Image_Generate.generate_image_via_api",
                    return_value=result,
                ),
                patch("crazy_functions.Image_Generate.promote_file_to_downloadzone"),
            ):
                outputs = list(图片生成_GPT_IMAGE(
                    "draw a blue square",
                    {"api_key": "sk-" + "a" * 48},
                    {"resolution": "1024x1024", "quality": "medium", "output_format": "png"},
                    chatbot,
                    [],
                    "system",
                    SimpleNamespace(),
                ))

        self.assertEqual(len(outputs), 2)
        self.assertEqual(len(chatbot), 1)
        self.assertEqual(chatbot[0][0], "draw a blue square")
        self.assertIn('<img src="file=', chatbot[0][1])
        self.assertEqual(outputs[-1][3], "图片生成完成")

    def test_completed_background_job_replaces_its_pending_message(self):
        job_id = "job-123"
        pending = build_drawing_pending_message(job_id, "gpt-image-2")
        chatbot = [["draw", pending], ["later question", "later answer"]]

        result = replace_drawing_job_message(chatbot, job_id, "draw", "<img>")

        self.assertEqual(result[0], ["draw", "<img>"])
        self.assertEqual(result[1], ["later question", "later answer"])

    def test_image_job_manager_signals_completion_without_polling(self):
        manager = ImageJobManager(max_workers=1)
        job = manager.submit(owner="tester", prompt="draw", work=lambda: "image")

        completed = manager.wait(job.job_id, owner="tester")

        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.result, "image")
        self.assertIsNone(manager.get(job.job_id, owner="someone-else"))


if __name__ == "__main__":
    unittest.main()
