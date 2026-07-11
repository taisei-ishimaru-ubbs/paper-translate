import json
import multiprocessing
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.openai_daily_quota import (
    DailyQuotaExceeded,
    DailyQuotaGuard,
    UsageUnavailable,
    configured_limit,
    fetch_organization_usage,
)


NOW = datetime(2026, 7, 12, 3, 0, tzinfo=timezone.utc)


def reserve_in_process(state_path: str, result_queue) -> None:
    os.environ["OPENAI_DAILY_TOKEN_LIMIT"] = "1000"
    guard = DailyQuotaGuard(
        "test",
        "openai/gpt-5.6-terra",
        state_path=Path(state_path),
        usage_reader=lambda _model: 0,
        now=lambda: NOW,
    )
    try:
        guard.reserve(600)
        result_queue.put("reserved")
    except DailyQuotaExceeded:
        result_queue.put("blocked")


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class OpenAIDailyQuotaTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "quota.json"
        self.env = patch.dict(
            os.environ,
            {"OPENAI_DAILY_TOKEN_LIMIT": "2400000"},
            clear=False,
        )
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp_dir.cleanup()

    def guard(self, usage=100):
        return DailyQuotaGuard(
            "test",
            "openai/gpt-5.6-terra",
            state_path=self.state_path,
            usage_reader=lambda _model: usage,
            now=lambda: NOW,
        )

    def test_reserve_settle_and_status(self):
        guard = self.guard(usage=1000)
        reservation = guard.reserve(500)
        guard.settle(reservation, 120)

        status = guard.status()
        self.assertEqual(status["organization_used"], 1000)
        self.assertEqual(status["local_used"], 120)
        self.assertEqual(status["local_reserved"], 0)

    def test_release_removes_reservation_without_usage(self):
        guard = self.guard()
        reservation = guard.reserve(500)
        guard.release(reservation)
        self.assertEqual(guard.status()["local_used"], 0)
        self.assertEqual(guard.status()["local_reserved"], 0)

    def test_global_limit_blocks_request(self):
        guard = self.guard(usage=2_399_900)
        with self.assertRaises(DailyQuotaExceeded):
            guard.reserve(101)

    def test_local_limit_counts_active_reservations(self):
        guard = self.guard(usage=0)
        first = guard.reserve(1_300_000)
        with self.assertRaises(DailyQuotaExceeded):
            guard.reserve(1_100_001)
        guard.release(first)

    def test_utc_date_change_resets_local_state(self):
        guard = self.guard()
        reservation = guard.reserve(500)
        guard.settle(reservation, 120)
        tomorrow = datetime(2026, 7, 13, 0, 1, tzinfo=timezone.utc)
        next_guard = DailyQuotaGuard(
            "test",
            "openai/gpt-5.6-terra",
            state_path=self.state_path,
            usage_reader=lambda _model: 0,
            now=lambda: tomorrow,
        )
        self.assertEqual(next_guard.status()["local_used"], 0)

    def test_corrupt_state_fails_closed(self):
        self.state_path.write_text("not-json", encoding="utf-8")
        with self.assertRaises(UsageUnavailable):
            self.guard().reserve(10)

    def test_invalid_limit_fails_closed(self):
        with patch.dict(os.environ, {"OPENAI_DAILY_TOKEN_LIMIT": "invalid"}):
            with self.assertRaises(UsageUnavailable):
                configured_limit()

    def test_zero_limit_disables_guard_without_usage_api(self):
        with patch.dict(os.environ, {"OPENAI_DAILY_TOKEN_LIMIT": "0"}):
            guard = DailyQuotaGuard(
                "test",
                "openai/gpt-5.6-terra",
                state_path=self.state_path,
                usage_reader=lambda _model: self.fail("usage reader should not run"),
            )
            self.assertIsNone(guard.reserve(100))

    def test_usage_api_sums_input_and_output_tokens(self):
        payload = {
            "data": [
                {
                    "results": [
                        {"input_tokens": 10, "output_tokens": 5},
                        {"input_tokens": 20, "output_tokens": 7},
                    ]
                }
            ]
        }

        def opener(_request, timeout):
            self.assertGreater(timeout, 0)
            return FakeResponse(payload)

        self.assertEqual(
            fetch_organization_usage(
                "openai/gpt-5.6-terra",
                admin_key="sk-admin-test",
                opener=opener,
                now=NOW,
            ),
            42,
        )

    def test_parallel_processes_cannot_overreserve(self):
        context = multiprocessing.get_context("spawn")
        queue = context.Queue()
        processes = [
            context.Process(target=reserve_in_process, args=(str(self.state_path), queue))
            for _ in range(3)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        results = [queue.get(timeout=2) for _ in processes]
        self.assertEqual(results.count("reserved"), 1)
        self.assertEqual(results.count("blocked"), 2)


if __name__ == "__main__":
    unittest.main()
