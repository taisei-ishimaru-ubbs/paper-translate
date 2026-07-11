import sys
import types
import unittest
from unittest.mock import patch

from scripts.openai_daily_quota import Reservation, UsageUnavailable
from scripts import translate_markdown


class FakeResponse:
    def __init__(self, model):
        self.model = model
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content="翻訳結果"))]
        self.usage = types.SimpleNamespace(total_tokens=42)


class FakeLiteLLM(types.ModuleType):
    def __init__(self):
        super().__init__("litellm")
        self.calls = []
        self.suppress_debug_info = False

    def token_counter(self, **_kwargs):
        return 10

    def completion(self, *, model, **_kwargs):
        self.calls.append(model)
        return FakeResponse(model)


class BlockingGuard:
    def __init__(self, *_args, **_kwargs):
        pass

    def reserve(self, _estimated):
        raise UsageUnavailable("usage unavailable")


class RecordingGuard:
    settled = []

    def __init__(self, *_args, **_kwargs):
        pass

    def reserve(self, estimated):
        return Reservation("reservation", estimated, 0, 0)

    def settle(self, reservation, actual):
        self.settled.append((reservation.reservation_id, actual))

    def release(self, _reservation):
        raise AssertionError("successful calls must not release reservations")


class TranslateQuotaFallbackTests(unittest.TestCase):
    def setUp(self):
        self.litellm = FakeLiteLLM()
        self.module_patch = patch.dict(sys.modules, {"litellm": self.litellm})
        self.module_patch.start()
        self.logs = []

    def tearDown(self):
        self.module_patch.stop()
        RecordingGuard.settled.clear()

    def test_usage_guard_failure_skips_openai_and_uses_gemini(self):
        with patch.object(translate_markdown, "DailyQuotaGuard", BlockingGuard):
            result = translate_markdown.call_llm(
                "source",
                "openai/gpt-5.6-terra",
                "gemini/gemini-3.1-flash-lite",
                self.logs.append,
            )
        self.assertEqual(result, "翻訳結果")
        self.assertEqual(self.litellm.calls, ["gemini/gemini-3.1-flash-lite"])
        self.assertTrue(any("using gemini/" in line for line in self.logs))

    def test_successful_openai_call_is_settled_from_response_usage(self):
        with patch.object(translate_markdown, "DailyQuotaGuard", RecordingGuard):
            result = translate_markdown.call_llm(
                "source",
                "openai/gpt-5.6-terra",
                "gemini/gemini-3.1-flash-lite",
                self.logs.append,
            )
        self.assertEqual(result, "翻訳結果")
        self.assertEqual(self.litellm.calls, ["openai/gpt-5.6-terra"])
        self.assertEqual(RecordingGuard.settled, [("reservation", 42)])


if __name__ == "__main__":
    unittest.main()
