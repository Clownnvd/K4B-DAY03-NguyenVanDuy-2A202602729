"""Day 03: compare one-shot chatbot with an observable ReAct tool loop."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from agent_provider import get_provider
from mcp_server import MCPAcademicServer
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_AGENT_SYSTEM_PROMPT


ROOT = Path(__file__).resolve().parents[1]


def load_test_cases() -> list[dict[str, Any]]:
    path = ROOT / "config" / "test_cases.json"
    if not path.exists():
        raise FileNotFoundError("Hãy tạo config/test_cases.json từ file mẫu trước khi chạy.")
    cases = json.loads(path.read_text(encoding="utf-8"))
    if len(cases) != 5 or len({case["id"] for case in cases}) != 5:
        raise ValueError("Cần đúng 5 test cases với ID riêng.")
    if any("TODO" in case["question"] for case in cases):
        raise ValueError("Còn câu hỏi TODO trong config/test_cases.json.")
    return cases


def run_baseline_chatbot(query: str, provider: Any) -> dict[str, Any]:
    """One LLM call and no tools: the comparison baseline from the slides."""
    start = time.perf_counter()
    answer = provider.generate(query, CHATBOT_BASELINE_PROMPT)
    return {"answer": answer, "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "tool_calls": 0, "model": provider.model_name, "live_api": provider.is_live}


def run_react_agent(query: str, provider: Any,
                    mcp_server: MCPAcademicServer | None = None) -> dict[str, Any]:
    """Continue the same model conversation after every tool observation."""
    server = mcp_server or MCPAcademicServer()
    messages: list[dict[str, Any]] = [{"role": "user", "content": query}]
    trace: list[dict[str, Any]] = []
    seen_calls: set[str] = set()
    started = time.perf_counter()

    for step in range(1, MAX_ITERATIONS + 1):
        model_start = time.perf_counter()
        try:
            turn = provider.next_turn(messages, server.list_tools(), REACT_AGENT_SYSTEM_PROMPT)
        except Exception as exc:
            error = f"LLM_ERROR: {type(exc).__name__}: {exc}"
            trace.append({"step": step, "action_type": "ERROR", "error": error})
            return _result(error, trace, provider, started, success=False)
        model_latency = round((time.perf_counter() - model_start) * 1000, 2)

        if turn["type"] == "text":
            answer = turn.get("content", "").strip()
            trace.append({
                "step": step, "action_type": "FINAL_ANSWER",
                "thought": "Model dừng gọi tool và đưa ra câu trả lời cuối.",
                "output": answer, "llm_latency_ms": model_latency,
                "latency_ms": model_latency,
                "response_id": turn.get("response_id"), "usage": turn.get("usage"),
            })
            return _result(answer, trace, provider, started, success=bool(answer))

        if turn["type"] != "tool_call":
            trace.append({"step": step, "action_type": "ERROR",
                          "error": f"Unsupported model response: {turn['type']}"})
            return _result("Model trả phản hồi không hợp lệ.", trace, provider, started, False)

        tool_name = turn["tool_name"]
        arguments = turn["arguments"]
        signature = json.dumps([tool_name, arguments], sort_keys=True, ensure_ascii=False)
        if signature in seen_calls:
            trace.append({"step": step, "action_type": "STOPPED_REPEAT",
                          "tool_name": tool_name, "arguments": arguments,
                          "thought": "Dừng vì model lặp lại cùng một tool call."})
            return _result("Đã dừng vì công cụ bị gọi lặp; cần người kiểm tra.",
                           trace, provider, started, False)
        seen_calls.add(signature)

        tool_start = time.perf_counter()
        observation = server.call_tool(tool_name, arguments)
        tool_latency = round((time.perf_counter() - tool_start) * 1000, 2)
        if tool_name == "academic_query":
            decision_summary = "Cần tra cứu hồ sơ DEMO trước khi trả dữ liệu cá nhân hoặc tạo lịch."
        elif tool_name == "schedule_appointment":
            decision_summary = "Đã có observation tra cứu thành công; dùng đúng cố vấn để tạo bản nháp lịch DEMO."
        else:
            decision_summary = "Model chọn công cụ; cần kiểm tra tên và tham số."
        trace.append({
            "step": step, "action_type": "TOOL_EXECUTION",
            "thought": decision_summary,
            "thought_source": "public_summary_of_observed_tool_choice",
            "tool_name": tool_name, "arguments": arguments,
            "observation": observation["result"], "jsonrpc": observation["jsonrpc"],
            "llm_latency_ms": model_latency, "tool_latency_ms": tool_latency,
            "latency_ms": round(model_latency + tool_latency, 2),
            "response_id": turn.get("response_id"), "usage": turn.get("usage"),
        })
        messages.append(turn["assistant_message"])
        messages.append({"role": "tool", "tool_call_id": turn["call_id"],
                         "content": json.dumps(observation, ensure_ascii=False)})

    trace.append({"step": MAX_ITERATIONS + 1, "action_type": "STOPPED_MAX_ITERATIONS",
                  "thought": f"Dừng ở giới hạn {MAX_ITERATIONS} vòng."})
    return _result("Đã dừng ở giới hạn vòng lặp; cần người kiểm tra.",
                   trace, provider, started, False)


def _result(answer: str, trace: list[dict[str, Any]], provider: Any,
            started: float, success: bool) -> dict[str, Any]:
    return {"answer": answer, "trace": trace, "success": success,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "tool_calls": sum(x["action_type"] == "TOOL_EXECUTION" for x in trace),
            "model": provider.model_name, "live_api": provider.is_live}


def evaluate_case(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    tools = [x["tool_name"] for x in result["trace"]
             if x["action_type"] == "TOOL_EXECUTION"]
    statuses = [x["observation"].get("status") for x in result["trace"]
                if x["action_type"] == "TOOL_EXECUTION"]
    expected_tools = case["expected_tools"]
    expected_statuses = case["expected_statuses"]
    passed = (result["success"] and tools == expected_tools and
              statuses == expected_statuses and
              result["trace"][-1]["action_type"] == "FINAL_ANSWER")
    return {"passed": passed, "actual_tools": tools, "actual_statuses": statuses,
            "expected_tools": expected_tools, "expected_statuses": expected_statuses}


def save_json(relative_path: str, data: Any) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_suite(provider: Any) -> int:
    cases = load_test_cases()
    comparisons: list[dict[str, Any]] = []
    all_traces: list[dict[str, Any]] = []
    for case in cases:
        baseline = run_baseline_chatbot(case["question"], provider)
        agent = run_react_agent(case["question"], provider)
        evaluation = evaluate_case(case, agent)
        comparisons.append({
            "id": case["id"], "category": case["category"], "question": case["question"],
            "expected_behavior": case["expected_behavior"],
            "baseline": baseline,
            "agent": {key: value for key, value in agent.items() if key != "trace"},
            "evaluation": evaluation,
        })
        all_traces.extend({"test_id": case["id"], "query": case["question"], **event}
                          for event in agent["trace"])
        label = "PASS" if evaluation["passed"] else "FAIL"
        print(f"{case['id']} {label} | tools={evaluation['actual_tools']} "
              f"statuses={evaluation['actual_statuses']} | "
              f"baseline={baseline['latency_ms']}ms agent={agent['latency_ms']}ms", flush=True)
    prefix = "" if provider.is_live else "mock_"
    save_json(f"docs/{prefix}trace_waterfall.json", all_traces)
    save_json(f"docs/{prefix}test_results.json", {
        "provider": type(provider).__name__, "model": provider.model_name,
        "live_api": provider.is_live, "passed": sum(x["evaluation"]["passed"] for x in comparisons),
        "total": len(comparisons), "cases": comparisons,
    })
    passed = sum(x["evaluation"]["passed"] for x in comparisons)
    print(f"KẾT QUẢ: {passed}/{len(cases)} tests; "
          f"trace={ROOT / 'docs' / (prefix + 'trace_waterfall.json')}")
    return 0 if passed == len(cases) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 03 chatbot vs ReAct MCP-style demo")
    parser.add_argument("--all", action="store_true", help="Run 5 comparison cases")
    parser.add_argument("--interactive", action="store_true", help="Chat with the agent")
    parser.add_argument("--mock", action="store_true", help="Offline logic smoke test")
    args = parser.parse_args()
    provider = get_provider(mock=args.mock)
    print(f"Provider={type(provider).__name__} model={provider.model_name} "
          f"live_api={provider.is_live}")
    if args.all:
        return run_suite(provider)
    if args.interactive:
        while True:
            try:
                query = input("Bạn hỏi (exit để thoát): ").strip()
            except (KeyboardInterrupt, EOFError):
                return 0
            if query.lower() in {"exit", "quit"}:
                return 0
            if not query:
                continue
            result = run_react_agent(query, provider)
            print(result["answer"])
            print(json.dumps(result["trace"], ensure_ascii=False, indent=2))
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
