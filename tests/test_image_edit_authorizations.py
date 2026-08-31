import os
import tempfile
import unittest

from shared_utils.image_edit_authorizations import ImageEditAuthorizationStore


class ImageEditAuthorizationStoreTests(unittest.TestCase):
    def test_token_restores_server_owned_parameters_for_same_owner(self):
        store = ImageEditAuthorizationStore()
        with tempfile.TemporaryDirectory() as output_root:
            image_path = os.path.join(output_root, "result.png")
            with open(image_path, "wb") as image_file:
                image_file.write(b"image")
            token = store.issue(
                owner="alice",
                file_path=image_path,
                output_root=output_root,
                model="gpt-image-2-4k",
                size="3840x2160",
                quality="high",
                output_format="webp",
            )

            authorization = store.resolve(
                token,
                owner="alice",
                output_root=output_root,
            )

        self.assertEqual(authorization.file_path, os.path.realpath(image_path))
        self.assertEqual(authorization.model, "gpt-image-2-4k")
        self.assertEqual(authorization.size, "3840x2160")
        self.assertEqual(authorization.quality, "high")
        self.assertEqual(authorization.output_format, "webp")

    def test_token_cannot_be_used_by_another_owner(self):
        store = ImageEditAuthorizationStore()
        with tempfile.TemporaryDirectory() as output_root:
            image_path = os.path.join(output_root, "result.png")
            with open(image_path, "wb") as image_file:
                image_file.write(b"image")
            token = store.issue(
                owner="alice",
                file_path=image_path,
                output_root=output_root,
            )
            self.assertIsNone(store.resolve(
                token,
                owner="bob",
                output_root=output_root,
            ))

    def test_file_outside_output_root_is_rejected(self):
        store = ImageEditAuthorizationStore()
        with tempfile.TemporaryDirectory() as output_root:
            with tempfile.NamedTemporaryFile(suffix=".png") as outside_file:
                with self.assertRaises(ValueError):
                    store.issue(
                        owner="alice",
                        file_path=outside_file.name,
                        output_root=output_root,
                    )

    def test_expired_token_is_rejected(self):
        store = ImageEditAuthorizationStore(ttl_seconds=-1)
        with tempfile.TemporaryDirectory() as output_root:
            image_path = os.path.join(output_root, "result.png")
            with open(image_path, "wb") as image_file:
                image_file.write(b"image")
            token = store.issue(
                owner="alice",
                file_path=image_path,
                output_root=output_root,
            )
            self.assertIsNone(store.resolve(
                token,
                owner="alice",
                output_root=output_root,
            ))


if __name__ == "__main__":
    unittest.main()
