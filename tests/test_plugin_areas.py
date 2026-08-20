import asyncio
import os
import tempfile
import threading
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
from shared_utils.image_generation import (
    ImageGenerationError,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_IMAGE_QUALITIES,
    SUPPORTED_IMAGE_SIZES,
)
from shared_utils.fastapi_server import stream_image_job_events
from toolbox import ChatBotWithCookies, default_user_name
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
        with tempfile.TemporaryDirectory() as temporary_log_dir:
            with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
                result = SimpleNamespace(
                    file_path=image_file.name,
                    model="gpt-image-2",
                    size="1024x1024",
                )
                chatbot = ChatBotWithCookies({"user_name": default_user_name})
                with (
                    patch(
                        "crazy_functions.Image_Generate.generate_image_via_api",
                        return_value=result,
                    ),
                    patch(
                        "crazy_functions.Image_Generate.get_log_folder",
                        return_value=temporary_log_dir,
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

    def test_image_plugin_shows_image_generation_errors_without_traceback(self):
        chatbot = ChatBotWithCookies({"user_name": default_user_name})
        with patch(
            "crazy_functions.Image_Generate.generate_gpt_image_result",
            side_effect=ImageGenerationError("未配置 AIOAGI API Key"),
        ):
            outputs = list(图片生成_GPT_IMAGE(
                "draw a blue square",
                {"api_key": ""},
                {"resolution": "1024x1024", "quality": "medium", "output_format": "png"},
                chatbot,
                [],
                "system",
                SimpleNamespace(),
            ))

        self.assertEqual(outputs[-1][3], "图片生成失败")
        self.assertIn("未配置 AIOAGI API Key", chatbot[-1][1])
        self.assertNotIn("Traceback", chatbot[-1][1])

    def test_completed_background_job_replaces_its_pending_message(self):
        job_id = "job-123"
        pending = build_drawing_pending_message(job_id, "gpt-image-2")
        chatbot = [["draw", pending], ["later question", "later answer"]]

        result = replace_drawing_job_message(chatbot, job_id, "draw", "<img>")

        self.assertEqual(result[0], ["draw", "<img>"])
        self.assertEqual(result[1], ["later question", "later answer"])

    def test_pending_drawing_message_contains_spinner_and_cancel_control(self):
        pending = build_drawing_pending_message("job-123", "gpt-image-2")

        self.assertIn('data-image-job-id="job-123"', pending)
        self.assertIn("image-job-spinner", pending)
        self.assertIn("image-job-cancel", pending)
        self.assertIn("停止", pending)

    def test_image_job_manager_signals_completion_without_polling(self):
        manager = ImageJobManager(max_workers=1)
        job = manager.submit(owner="tester", prompt="draw", work=lambda: "image")

        completed = manager.wait(job.job_id, owner="tester", timeout=1.0)

        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.result, "image")
        self.assertIsNone(manager.get(job.job_id, owner="someone-else"))

    def test_image_job_manager_discards_consumed_jobs(self):
        manager = ImageJobManager(max_workers=1)
        job = manager.submit(owner="tester", prompt="draw", work=lambda: "image")
        self.assertIsNotNone(manager.wait(job.job_id, owner="tester", timeout=1.0))

        self.assertTrue(manager.discard(job.job_id, owner="tester"))
        self.assertIsNone(manager.get(job.job_id, owner="tester"))
        self.assertFalse(manager.discard(job.job_id, owner="tester"))

    def test_image_job_manager_cancels_job_before_worker_finishes(self):
        work_started = threading.Event()
        release_work = threading.Event()
        manager = ImageJobManager(max_workers=1)
        job = manager.submit(
            owner="tester",
            prompt="draw",
            work=lambda: (work_started.set(), release_work.wait(1.0))[1],
        )
        self.assertTrue(work_started.wait(1.0))

        self.assertTrue(manager.cancel(job.job_id, owner="tester"))
        cancelled = manager.get(job.job_id, owner="tester")
        self.assertEqual(cancelled.status, "cancelled")
        self.assertTrue(cancelled.done.is_set())
        self.assertFalse(manager.cancel(job.job_id, owner="tester"))

        release_work.set()

    def test_image_job_manager_removes_result_created_during_cancel_race(self):
        result_ready = threading.Event()
        release_work = threading.Event()
        cleanup_finished = threading.Event()

        with tempfile.TemporaryDirectory() as temporary_dir:
            result_path = os.path.join(temporary_dir, "cancelled.png")

            def finish_after_cancel():
                with open(result_path, "wb") as image_file:
                    image_file.write(b"cancelled-image")
                result_ready.set()
                release_work.wait(1.0)
                return SimpleNamespace(file_path=result_path)

            real_remove = os.remove

            def tracked_remove(file_path):
                try:
                    real_remove(file_path)
                finally:
                    cleanup_finished.set()

            with patch("shared_utils.image_jobs.os.remove", side_effect=tracked_remove):
                manager = ImageJobManager(max_workers=1)
                job = manager.submit(owner="tester", prompt="draw", work=finish_after_cancel)
                self.assertTrue(result_ready.wait(1.0))
                self.assertTrue(os.path.isfile(result_path))

                self.assertTrue(manager.cancel(job.job_id, owner="tester"))
                release_work.set()
                self.assertTrue(cleanup_finished.wait(1.0))
                self.assertFalse(os.path.exists(result_path))

    def test_image_job_manager_wait_can_time_out_while_job_is_pending(self):
        work_started = threading.Event()
        release_work = threading.Event()

        def blocked_work():
            work_started.set()
            release_work.wait(1.0)
            return "image"

        manager = ImageJobManager(max_workers=1)
        job = manager.submit(owner="tester", prompt="draw", work=blocked_work)
        self.assertTrue(work_started.wait(1.0))

        pending = manager.wait(job.job_id, owner="tester", timeout=0.01)

        self.assertIsNotNone(pending)
        self.assertFalse(pending.done.is_set())
        release_work.set()
        completed = manager.wait(job.job_id, owner="tester", timeout=1.0)
        self.assertEqual(completed.status, "completed")

    def test_image_job_manager_records_background_failures(self):
        def failing_work():
            raise ValueError("image generation failed")

        manager = ImageJobManager(max_workers=1)
        job = manager.submit(owner="tester", prompt="draw", work=failing_work)

        failed = manager.wait(job.job_id, owner="tester", timeout=1.0)

        self.assertTrue(failed.done.is_set())
        self.assertEqual(failed.status, "failed")
        self.assertIn("image generation failed", failed.error)

    def test_image_job_event_stream_emits_completion_without_blocking_executor(self):
        manager = ImageJobManager(max_workers=1)
        job = manager.submit(owner="tester", prompt="draw", work=lambda: "image")
        completed = manager.wait(job.job_id, owner="tester", timeout=1.0)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.status, "completed")

        class ConnectedRequest:
            async def is_disconnected(self):
                return False

        async def collect_events():
            return [
                event
                async for event in stream_image_job_events(
                    manager,
                    job.job_id,
                    "tester",
                    ConnectedRequest(),
                    poll_interval=0.001,
                )
            ]

        events = asyncio.run(collect_events())

        self.assertEqual(len(events), 1)
        self.assertIn("event: image_job", events[0])
        self.assertIn(job.job_id, events[0])

    def test_image_job_event_stream_stops_when_client_disconnects(self):
        manager = ImageJobManager(max_workers=1)
        release_work = threading.Event()
        job = manager.submit(
            owner="tester",
            prompt="draw",
            work=lambda: release_work.wait(1.0),
        )

        class DisconnectedRequest:
            async def is_disconnected(self):
                return True

        async def collect_events():
            return [
                event
                async for event in stream_image_job_events(
                    manager,
                    job.job_id,
                    "tester",
                    DisconnectedRequest(),
                    poll_interval=0.001,
                )
            ]

        events = asyncio.run(collect_events())
        release_work.set()

        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
