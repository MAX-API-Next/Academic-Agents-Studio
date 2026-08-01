import base64
import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


_PROXY_NAMES = ("ALL_PROXY", "all_proxy")
_PROXY_VALUES = {
    name: os.environ.pop(name)
    for name in _PROXY_NAMES
    if name in os.environ
}
try:
    from mcp_servers.image_generation_tool import AcademicImageGenerationTool
    from mcp_servers.mcp_manager import MCPManager, _format_local_image_result
    from request_llms.bridge_all import _image_tool_is_configured
finally:
    os.environ.update(_PROXY_VALUES)


class FakeResponse:
    status_code = 200
    ok = True
    headers = {}

    def json(self):
        return {
            "data": [{
                "b64_json": base64.b64encode(b"image").decode("ascii"),
            }],
        }


class FakeSession:
    def post(self, url, **kwargs):
        return FakeResponse()


class MCPImageToolTests(unittest.TestCase):
    def setUp(self):
        self.chatbot = SimpleNamespace(_cookies={
            "mcp_enabled": True,
            "api_key": "sk-" + "a" * 48,
            "llm_model": "gpt-5-mini",
            "user_id": "review-user",
            "user_name": "review-user",
        })
        self.llm_config = {
            "model": "gpt-5-mini",
            "model_server": "https://example.invalid/v1",
            "api_key": self.chatbot._cookies["api_key"],
        }

    def test_normal_agent_creation_registers_image_tool(self):
        manager = MCPManager()
        expected_bot = SimpleNamespace(function_map={})
        with (
            patch.object(manager, "get_llm_config", return_value=self.llm_config),
            patch("mcp_servers.mcp_manager.Assistant", return_value=expected_bot) as assistant,
        ):
            bot = manager.create_agent_bot(
                self.chatbot,
                mcp_servers=[{"mcpServers": {"test": {"url": "https://example.invalid"}}}],
            )

        self.assertIs(bot, expected_bot)
        function_list = assistant.call_args.kwargs["function_list"]
        self.assertIsInstance(function_list[-1], AcademicImageGenerationTool)
        self.assertIs(function_list[-1].chatbot, self.chatbot)

    def test_fallback_agent_creation_registers_image_tool(self):
        manager = MCPManager()
        expected_bot = SimpleNamespace(function_map={})
        with (
            patch.object(manager, "get_llm_config", return_value=self.llm_config),
            patch(
                "mcp_servers.mcp_manager.Assistant",
                side_effect=[RuntimeError("MCP init failed"), expected_bot],
            ) as assistant,
        ):
            bot = manager.create_agent_bot(
                self.chatbot,
                mcp_servers=[{"mcpServers": {"test": {"url": "https://example.invalid"}}}],
            )

        self.assertIs(bot, expected_bot)
        self.assertEqual(assistant.call_count, 2)
        fallback_tools = assistant.call_args_list[1].kwargs["function_list"]
        self.assertEqual(len(fallback_tools), 1)
        self.assertIsInstance(fallback_tools[0], AcademicImageGenerationTool)
        self.assertIs(fallback_tools[0].chatbot, self.chatbot)
        self.assertTrue(self.chatbot._cookies["mcp_bot_created"])

    def test_local_image_result_uses_exact_bot_tool_without_remote_formatter(self):
        manager = MCPManager()
        with tempfile.TemporaryDirectory() as output_dir:
            tool = AcademicImageGenerationTool(
                api_keys=self.llm_config["api_key"],
                output_dir=output_dir,
                session=FakeSession(),
            )
            result_text = tool.call({"prompt": "academic illustration"})
            bot = SimpleNamespace(
                function_map={AcademicImageGenerationTool.name: tool},
                run=lambda messages: iter([[{
                    "role": "function",
                    "content": result_text,
                }]]),
            )

            output = list(manager.chat_with_mcp(
                "draw an image",
                chatbot=self.chatbot,
                bot=bot,
            ))

        self.assertIn('<img src="file=', "".join(output))

    def test_unrecognized_result_is_escaped_and_rendered_locally(self):
        manager = MCPManager()
        bot = SimpleNamespace(
            function_map={},
            run=lambda messages: iter([[{
                "role": "function",
                "content": json.dumps({
                    "result": "<script>private research</script>",
                }),
            }]]),
        )

        output = list(manager.chat_with_mcp(
            "use a tool",
            chatbot=self.chatbot,
            bot=bot,
        ))

        response = "".join(output)
        self.assertIn("<pre><code>", response)
        self.assertIn("&lt;script&gt;private research&lt;/script&gt;", response)
        self.assertNotIn("<script>", response)

    def test_agent_error_is_logged_but_raw_details_are_not_returned(self):
        manager = MCPManager()
        sensitive_error = "Authorization=Bearer secret-research-token"

        def failing_run(messages):
            raise RuntimeError(sensitive_error)

        bot = SimpleNamespace(function_map={}, run=failing_run)
        with patch("mcp_servers.mcp_manager.logger") as server_logger:
            output = list(manager.chat_with_mcp(
                "use a tool",
                chatbot=self.chatbot,
                bot=bot,
            ))

        response = "".join(output)
        self.assertIn("调用出错", response)
        self.assertIn("错误编号", response)
        self.assertNotIn(sensitive_error, response)
        server_logger.opt.return_value.error.assert_called_once()

    def test_image_tool_configuration_matches_key_and_endpoint(self):
        manager = SimpleNamespace()
        manager.get_llm_config = lambda chatbot: {"api_key": chatbot}
        valid_key = "sk-" + "a" * 48

        with patch(
            "request_llms.bridge_all.get_conf",
            return_value=("gpt-image-2", "https://api.aiearth.dev/v1/images/generations"),
        ):
            for api_key, expected in (
                ("", False),
                ("invalid", False),
                (valid_key, True),
            ):
                with self.subTest(api_key=api_key):
                    self.assertEqual(
                        _image_tool_is_configured(manager, api_key),
                        expected,
                    )

        with patch(
            "request_llms.bridge_all.get_conf",
            return_value=("aioagi-gpt-image-2", "https://api.aiearth.dev/v1/images/generations"),
        ):
            self.assertTrue(_image_tool_is_configured(manager, valid_key))

        with patch(
            "request_llms.bridge_all.get_conf",
            return_value=("gpt-image-2", "relative/images/generations"),
        ):
            with self.assertRaisesRegex(ValueError, "IMAGE_API_URL"):
                _image_tool_is_configured(manager, valid_key)

    def test_result_cannot_be_rendered_by_another_bot_tool(self):
        with (
            tempfile.TemporaryDirectory() as first_output,
            tempfile.TemporaryDirectory() as second_output,
        ):
            first_tool = AcademicImageGenerationTool(
                api_keys=self.llm_config["api_key"],
                output_dir=first_output,
                session=FakeSession(),
            )
            second_tool = AcademicImageGenerationTool(
                api_keys=self.llm_config["api_key"],
                output_dir=second_output,
                session=FakeSession(),
            )
            result_text = first_tool.call({"prompt": "academic illustration"})

            wrong_bot = SimpleNamespace(
                function_map={AcademicImageGenerationTool.name: second_tool},
            )
            right_bot = SimpleNamespace(
                function_map={AcademicImageGenerationTool.name: first_tool},
            )
            self.assertIsNone(_format_local_image_result(wrong_bot, result_text))
            self.assertIn(
                '<img src="file=',
                _format_local_image_result(right_bot, result_text),
            )


if __name__ == "__main__":
    unittest.main()
