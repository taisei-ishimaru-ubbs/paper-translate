#!/usr/bin/env python3
"""Guard OpenAI calls with organization usage plus a repo-local UTC-day cap."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_LIMIT = 2_400_000
DEFAULT_TIMEOUT = 10.0
USAGE_URL = "https://api.openai.com/v1/organization/usage/completions"


class QuotaError(RuntimeError):
    """Base class for fail-closed quota errors."""


class UsageUnavailable(QuotaError):
    """The organization Usage API could not be read safely."""


class DailyQuotaExceeded(QuotaError):
    """The projected request would cross a daily limit."""


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    estimated_tokens: int
    global_used_tokens: int
    local_used_tokens: int


def is_openai_model(model: str) -> bool:
    return model.startswith("openai/")


def bare_model_name(model: str) -> str:
    return model.split("/", 1)[1] if "/" in model else model


def configured_limit() -> int:
    raw = os.environ.get("OPENAI_DAILY_TOKEN_LIMIT", str(DEFAULT_LIMIT))
    try:
        limit = int(raw)
    except ValueError as exc:
        raise UsageUnavailable("OPENAI_DAILY_TOKEN_LIMIT must be an integer") from exc
    if limit < 0:
        raise UsageUnavailable("OPENAI_DAILY_TOKEN_LIMIT must be zero or positive")
    return limit


def state_path_for(repo_name: str) -> Path:
    configured = os.environ.get("OPENAI_DAILY_QUOTA_STATE")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "state" / "ubbs" / f"{repo_name}-openai-quota.json"


def utc_day(now: datetime | None = None) -> tuple[str, int, int]:
    current = now or datetime.now(timezone.utc)
    current = current.astimezone(timezone.utc)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.date().isoformat(), int(start.timestamp()), int(end.timestamp())


def _usage_error_message(payload: bytes, fallback: str) -> str:
    try:
        parsed = json.loads(payload.decode("utf-8", errors="replace"))
        error = parsed.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or fallback)
        if error:
            return str(error)
    except (ValueError, AttributeError):
        pass
    return fallback


def fetch_organization_usage(
    model: str,
    *,
    admin_key: str | None = None,
    opener: Callable[..., Any] = urlopen,
    now: datetime | None = None,
) -> int:
    key = admin_key or os.environ.get("OPENAI_ADMIN_API_KEY")
    if not key:
        raise UsageUnavailable("OPENAI_ADMIN_API_KEY is not set")
    _, start, end = utc_day(now)
    query = urlencode(
        [
            ("start_time", start),
            ("end_time", end),
            ("bucket_width", "1d"),
            ("limit", 1),
            ("models", bare_model_name(model)),
        ]
    )
    request = Request(
        f"{USAGE_URL}?{query}",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        timeout = float(os.environ.get("OPENAI_USAGE_API_TIMEOUT", str(DEFAULT_TIMEOUT)))
    except ValueError as exc:
        raise UsageUnavailable("OPENAI_USAGE_API_TIMEOUT must be numeric") from exc
    try:
        with opener(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as exc:
        body = exc.read()
        raise UsageUnavailable(_usage_error_message(body, f"Usage API HTTP {exc.code}")) from exc
    except (URLError, OSError, ValueError) as exc:
        raise UsageUnavailable(f"Usage API request failed: {exc}") from exc

    try:
        return sum(
            int(result.get("input_tokens", 0)) + int(result.get("output_tokens", 0))
            for bucket in payload.get("data", [])
            for result in bucket.get("results", [])
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise UsageUnavailable("Usage API returned an unexpected response") from exc


def estimate_request_tokens(litellm: Any, model: str, messages: list[dict[str, str]], max_tokens: int) -> int:
    try:
        input_tokens = int(litellm.token_counter(model=model, messages=messages))
    except Exception:
        # UTF-8 bytes are deliberately conservative when tokenizer metadata is unavailable.
        input_tokens = sum(len(message.get("content", "").encode("utf-8")) for message in messages) + 64
    return max(1, input_tokens) + max_tokens


def response_total_tokens(response: Any, reserved_tokens: int) -> int:
    usage = getattr(response, "usage", None)
    if usage is None:
        return reserved_tokens
    total = getattr(usage, "total_tokens", None)
    if total is None and isinstance(usage, dict):
        total = usage.get("total_tokens")
    if total is None:
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        completion = getattr(usage, "completion_tokens", 0) or 0
        if isinstance(usage, dict):
            prompt = usage.get("prompt_tokens", usage.get("input_tokens", prompt)) or 0
            completion = usage.get("completion_tokens", usage.get("output_tokens", completion)) or 0
        total = int(prompt) + int(completion)
    return int(total) if int(total) > 0 else reserved_tokens


class DailyQuotaGuard:
    def __init__(
        self,
        repo_name: str,
        model: str,
        *,
        state_path: Path | None = None,
        usage_reader: Callable[[str], int] = fetch_organization_usage,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repo_name = repo_name
        self.model = model
        self.limit = configured_limit()
        self.state_path = state_path or state_path_for(repo_name)
        self.usage_reader = usage_reader
        self.now = now or (lambda: datetime.now(timezone.utc))

    def _empty_state(self, day: str) -> dict[str, Any]:
        return {"utc_date": day, "used_tokens": 0, "reservations": {}}

    def _load_state(self, day: str) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._empty_state(day)
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise UsageUnavailable(f"quota state is unreadable: {self.state_path}") from exc
        if state.get("utc_date") != day:
            return self._empty_state(day)
        if not isinstance(state.get("reservations"), dict):
            raise UsageUnavailable(f"quota state is invalid: {self.state_path}")
        return state

    def _write_state(self, state: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temp_name = tempfile.mkstemp(prefix=self.state_path.name + ".", dir=self.state_path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.state_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def _locked_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock_path = Path(str(self.state_path) + ".lock")
        lock_handle = lock_path.open("a+", encoding="utf-8")
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        return lock_handle

    def reserve(self, estimated_tokens: int) -> Reservation | None:
        if self.limit == 0 or not is_openai_model(self.model):
            return None
        global_used = self.usage_reader(self.model)
        day, _, _ = utc_day(self.now())
        lock_handle = self._locked_state()
        try:
            state = self._load_state(day)
            local_used = int(state.get("used_tokens", 0))
            active = sum(int(item.get("tokens", 0)) for item in state["reservations"].values())
            projected_global = global_used + estimated_tokens
            projected_local = local_used + active + estimated_tokens
            if projected_global > self.limit or projected_local > self.limit:
                raise DailyQuotaExceeded(
                    f"daily OpenAI limit would be exceeded: limit={self.limit}, "
                    f"global={global_used}, local={local_used}, active={active}, request={estimated_tokens}"
                )
            reservation_id = uuid.uuid4().hex
            state["reservations"][reservation_id] = {
                "tokens": estimated_tokens,
                "created_at": int(time.time()),
            }
            self._write_state(state)
            return Reservation(reservation_id, estimated_tokens, global_used, local_used + active)
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            lock_handle.close()

    def settle(self, reservation: Reservation | None, actual_tokens: int) -> None:
        if reservation is None:
            return
        day, _, _ = utc_day(self.now())
        lock_handle = self._locked_state()
        try:
            state = self._load_state(day)
            if state["reservations"].pop(reservation.reservation_id, None) is not None:
                state["used_tokens"] = int(state.get("used_tokens", 0)) + max(0, actual_tokens)
                self._write_state(state)
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            lock_handle.close()

    def release(self, reservation: Reservation | None) -> None:
        if reservation is None:
            return
        day, _, _ = utc_day(self.now())
        lock_handle = self._locked_state()
        try:
            state = self._load_state(day)
            if state["reservations"].pop(reservation.reservation_id, None) is not None:
                self._write_state(state)
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            lock_handle.close()

    def status(self) -> dict[str, Any]:
        global_used = self.usage_reader(self.model) if self.limit else 0
        day, _, _ = utc_day(self.now())
        lock_handle = self._locked_state()
        try:
            state = self._load_state(day)
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            lock_handle.close()
        active = sum(int(item.get("tokens", 0)) for item in state["reservations"].values())
        local_used = int(state.get("used_tokens", 0))
        return {
            "repo": self.repo_name,
            "utc_date": day,
            "model": bare_model_name(self.model),
            "limit": self.limit,
            "organization_used": global_used,
            "local_used": local_used,
            "local_reserved": active,
            "organization_remaining": max(0, self.limit - global_used),
            "local_remaining": max(0, self.limit - local_used - active),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("status", nargs="?", default="status")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--model", default="openai/gpt-5.6-terra")
    args = parser.parse_args()
    try:
        print(json.dumps(DailyQuotaGuard(args.repo, args.model).status(), ensure_ascii=False, indent=2))
    except QuotaError as exc:
        print(f"openai-quota: {exc}", file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
