import os
import unittest

os.environ["no_proxy"] = "*"

from crazy_functional import get_crazy_functions
from main import (
    DRAWING_FORMAT_OPTIONS,
    DRAWING_QUALITY_OPTIONS,
    DRAWING_RESOLUTION_OPTIONS,
    build_drawing_plugin_kwargs,
)
from shared_utils.image_generation import (
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_IMAGE_QUALITIES,
    SUPPORTED_IMAGE_SIZES,
)


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


if __name__ == "__main__":
    unittest.main()
