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


class FakeSSEContext:
    async def __aenter__(self):
        return "reader", "writer"

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeClientSession:
    def __init__(self, *streams):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def initialize(self):
        pass

    async def call_tool(self, name, arguments):
        content = [SimpleNamespace(text="remote-rendered")]
        return SimpleNamespace(content=content)


class FailingClientSession(FakeClientSession):
    async def call_tool(self, name, arguments):
        raise RuntimeError("remote formatter failed")


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

            with patch(
                "mcp_servers.mcp_manager.sse_client",
                side_effect=AssertionError("remote formatter should not be called"),
            ) as remote_formatter:
                output = list(manager.chat_with_mcp(
                    "draw an image",
                    chatbot=self.chatbot,
                    bot=bot,
                ))

        self.assertFalse(remote_formatter.called)
        self.assertIn('<img src="file=', "".join(output))

    def test_unrecognized_result_falls_back_to_remote_formatter(self):
        manager = MCPManager()
        bot = SimpleNamespace(
            function_map={},
            run=lambda messages: iter([[{
                "role": "function",
                "content": json.dumps({"result": "ordinary MCP output"}),
            }]]),
        )

        with (
            patch("mcp_servers.mcp_manager.sse_client", return_value=FakeSSEContext()),
            patch("mcp_servers.mcp_manager.ClientSession", FakeClientSession),
        ):
            output = list(manager.chat_with_mcp(
                "use a remote tool",
                chatbot=self.chatbot,
                bot=bot,
            ))

        self.assertIn("remote-rendered", "".join(output))

    def test_remote_formatter_failure_is_returned_to_the_user(self):
        manager = MCPManager()
        bot = SimpleNamespace(
            function_map={},
            run=lambda messages: iter([[{
                "role": "function",
                "content": json.dumps({"result": "ordinary MCP output"}),
            }]]),
        )

        with (
            patch("mcp_servers.mcp_manager.sse_client", return_value=FakeSSEContext()),
            patch("mcp_servers.mcp_manager.ClientSession", FailingClientSession),
        ):
            output = list(manager.chat_with_mcp(
                "use a remote tool",
                chatbot=self.chatbot,
                bot=bot,
            ))

        response = "".join(output)
        self.assertIn("调用出错", response)
        self.assertIn("remote formatter failed", response)

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
