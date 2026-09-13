"""Behavior checks for the tool boundary and real multi-step conversation loop."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_provider import MockOfflineProvider
from app import load_test_cases, run_react_agent, evaluate_case
from mcp_server import MCPAcademicServer


class AgentBehaviorTests(unittest.TestCase):
    def test_booking_requires_successful_lookup_in_same_session(self):
        server = MCPAcademicServer()
        args = {"student_id": "SV2026002", "datetime_str": "14:00 15/09/2026",
                "advisor_name": "TS. Lê Thị B"}
        self.assertEqual(server.call_tool("schedule_appointment", args)["result"]["status"],
                         "PRECONDITION_REQUIRED")
        self.assertEqual(server.call_tool("academic_query", {"student_id": "SV2026002"})
                         ["result"]["status"], "SUCCESS")
        booking = server.call_tool("schedule_appointment", args)
        self.assertEqual(booking["jsonrpc"], "2.0")
        self.assertEqual(booking["result"]["status"], "SUCCESS")
        self.assertTrue(booking["result"]["simulated"])

    def test_bad_student_or_advisor_never_creates_booking(self):
        server = MCPAcademicServer()
        self.assertEqual(server.call_tool("academic_query", {"student_id": "SV9999999"})
                         ["result"]["status"], "NOT_FOUND")
        self.assertEqual(server.call_tool("schedule_appointment", {
            "student_id": "SV9999999", "datetime_str": "14:00 15/09/2026",
            "advisor_name": "TS. Lê Thị B"})["result"]["status"], "PRECONDITION_REQUIRED")
        server.call_tool("academic_query", {"student_id": "SV2026001"})
        self.assertEqual(server.call_tool("schedule_appointment", {
            "student_id": "SV2026001", "datetime_str": "14:00 15/09/2026",
            "advisor_name": "Không đúng"})["result"]["status"], "ADVISOR_MISMATCH")

    def test_mock_suite_proves_simple_chain_and_edge_paths(self):
        cases = load_test_cases()
        for case in cases:
            with self.subTest(case=case["id"]):
                result = run_react_agent(case["question"], MockOfflineProvider())
                self.assertTrue(evaluate_case(case, result)["passed"])
        chained = run_react_agent(cases[3]["question"], MockOfflineProvider())
        self.assertEqual([x["tool_name"] for x in chained["trace"]
                          if x["action_type"] == "TOOL_EXECUTION"],
                         ["academic_query", "schedule_appointment"])
        self.assertEqual(chained["trace"][-1]["action_type"], "FINAL_ANSWER")

    def test_repeated_identical_tool_call_is_stopped(self):
        class RepeatProvider:
            model_name = "repeat-test"
            is_live = False
            count = 0

            def next_turn(self, messages, tools, system_prompt):
                self.count += 1
                call_id = f"repeat_{self.count}"
                return {"type": "tool_call", "tool_name": "academic_query",
                        "arguments": {"student_id": "SV2026001"}, "call_id": call_id,
                        "assistant_message": {"role": "assistant", "content": "",
                            "tool_calls": [{"id": call_id, "type": "function",
                                "function": {"name": "academic_query",
                                    "arguments": json.dumps({"student_id": "SV2026001"})}}]}}

        result = run_react_agent("Tra cứu SV2026001", RepeatProvider())
        self.assertFalse(result["success"])
        self.assertEqual(result["trace"][-1]["action_type"], "STOPPED_REPEAT")


if __name__ == "__main__":
    unittest.main()
