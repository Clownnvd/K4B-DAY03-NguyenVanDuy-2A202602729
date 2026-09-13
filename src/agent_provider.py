"""LLM adapter used by the finished lab. No silent fallback from a live API to mock."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class OpenAIProvider:
    is_live = True

    def __init__(self, model: str | None = None) -> None:
        from openai import OpenAI

        key = os.getenv("OPENAI_API_KEY")
        if not key or key == "your_openai_api_key_here":
            raise RuntimeError("OPENAI_API_KEY chưa được cấu hình.")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4.1-mini"
        self.client = OpenAI(api_key=key, timeout=35.0, max_retries=1)

    def generate(self, prompt: str, system_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content or ""

    def next_turn(self, messages: list[dict[str, Any]],
                  tools_schema: list[dict[str, Any]], system_prompt: str) -> dict[str, Any]:
        tools = [{"type": "function", "function": {
            "name": spec["name"], "description": spec["description"],
            "parameters": spec["parameters"]}} for spec in tools_schema]
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": system_prompt}, *messages],
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=False,
            temperature=0,
        )
        message = response.choices[0].message
        usage = response.usage.model_dump() if response.usage else None
        if message.tool_calls:
            call = message.tool_calls[0]
            if call.type != "function":
                raise RuntimeError("Model returned an unsupported tool call type.")
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                raise RuntimeError("Model returned invalid tool JSON.") from exc
            return {
                "type": "tool_call", "tool_name": call.function.name,
                "arguments": arguments, "call_id": call.id,
                "decision_note": (message.content or "").strip(),
                "assistant_message": {
                    "role": "assistant", "content": message.content or "",
                    "tool_calls": [{"id": call.id, "type": "function", "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments or "{}"}}],
                },
                "response_id": response.id, "usage": usage,
            }
        return {"type": "text", "content": message.content or "",
                "response_id": response.id, "usage": usage}


class MockOfflineProvider:
    """Small deterministic adapter for local logic tests; never used as submission evidence."""

    is_live = False
    model_name = "offline-mock"

    def __init__(self) -> None:
        self.counter = 0

    def generate(self, prompt: str, system_prompt: str) -> str:
        if re.search(r"SV\d{7}", prompt, re.I):
            return "Tôi không có công cụ để xác minh dữ liệu sinh viên hoặc tạo lịch."
        return "Đây là bản demo hỗ trợ tra cứu học vụ và tạo bản nháp lịch tư vấn."

    def next_turn(self, messages: list[dict[str, Any]],
                  tools_schema: list[dict[str, Any]], system_prompt: str) -> dict[str, Any]:
        user_query = next(m["content"] for m in messages if m["role"] == "user")
        match = re.search(r"SV\d{7}", user_query, re.I)
        student_id = match.group(0).upper() if match else None
        last_tool = next((m for m in reversed(messages) if m["role"] == "tool"), None)
        if last_tool:
            observation = json.loads(last_tool["content"])
            result = observation["result"]
            if (observation["tool"] == "academic_query" and
                    result["status"] == "SUCCESS" and "lịch" in user_query.lower() and
                    any(verb in user_query.lower() for verb in ("đặt", "tạo"))):
                time_match = re.search(r"\d{2}:\d{2}\s+\d{2}/\d{2}/\d{4}", user_query)
                if time_match:
                    return self._tool("schedule_appointment", {
                        "student_id": student_id, "datetime_str": time_match.group(0),
                        "advisor_name": result["data"]["advisor"]})
            if result["status"] == "NOT_FOUND":
                return {"type": "text", "content": "Không có mã sinh viên DEMO này; không tạo lịch."}
            if observation["tool"] == "schedule_appointment":
                return {"type": "text", "content": result["message"]}
            return {"type": "text", "content": json.dumps(result, ensure_ascii=False)}
        if student_id:
            return self._tool("academic_query", {"student_id": student_id})
        return {"type": "text", "content": self.generate(user_query, system_prompt)}

    def _tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.counter += 1
        call_id = f"mock_{self.counter}"
        return {"type": "tool_call", "tool_name": name, "arguments": arguments,
                "call_id": call_id, "decision_note": "Quyết định mẫu trong mock.",
                "assistant_message": {"role": "assistant", "content": "",
                                      "tool_calls": [{"id": call_id, "type": "function",
                                                      "function": {"name": name,
                                                                   "arguments": json.dumps(arguments)}}]}}


def get_provider(mock: bool = False) -> OpenAIProvider | MockOfflineProvider:
    if mock or os.getenv("LLM_PROVIDER", "openai").lower() == "mock":
        return MockOfflineProvider()
    if os.getenv("LLM_PROVIDER", "openai").lower() != "openai":
        raise RuntimeError("Bản nộp này hỗ trợ LLM_PROVIDER=openai hoặc mock.")
    return OpenAIProvider()
